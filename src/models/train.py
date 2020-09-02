# coding=utf-8
import argparse
import glob
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict

import numpy as np
import torch
import torch.distributed
from torch.utils.data import DataLoader, TensorDataset
import pytorch_lightning as pl
from pytorch_lightning.callbacks.lr_logger import LearningRateLogger
from pytorch_lightning.utilities import rank_zero_info, rank_zero_only
from transformers import (
    AutoConfig,
    AutoModelForSequenceClassification,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
)

from utils import processors, convert_examples_to_features, accuracy, SEQUENCE_CLASSIFICATION_MODELS, TOKENIZERS

logger = logging.getLogger(__name__)


class BERTTransformer(pl.LightningModule):
    def __init__(self, hparams):
        """Initialize a model, tokenizer and config."""
        super().__init__()

        if type(hparams) is dict:
            hparams = argparse.Namespace(**hparams)
        self.hparams = hparams
        self.processor = processors[hparams.task](hparams.data_dir)
        self.output_dir = Path(self.hparams.output_dir)

        self.labels = self.processor.get_labels()
        id2label = {idx: label for idx, label in enumerate(self.labels)}
        label2id = {label: idx for idx, label in enumerate(self.labels)}
        config_kwargs = {"id2label": id2label, "label2id": label2id}
        cache_dir = self.hparams.cache_dir if self.hparams.cache_dir else None
        self.config = AutoConfig.from_pretrained(self.hparams.pretrained_model_name_or_path, cache_dir=cache_dir,
                                                 **config_kwargs)

        extra_model_params = ("encoder_layerdrop", "decoder_layerdrop", "dropout", "attention_dropout")
        for p in extra_model_params:
            if getattr(self.hparams, p, None):
                assert hasattr(self.config, p), f"model config doesn't have a `{p}` attribute"
                setattr(self.config, p, getattr(self.hparams, p))

        model_class = self.hparams.model_class.lower() if self.hparams.model_class is not None else None
        self.config.update({"model_class": model_class})
        model_class = SEQUENCE_CLASSIFICATION_MODELS.get(model_class, AutoModelForSequenceClassification)
        self.model = model_class.from_pretrained(
            self.hparams.pretrained_model_name_or_path,
            from_tf=bool(".ckpt" in self.hparams.pretrained_model_name_or_path),
            config=self.config,
            cache_dir=cache_dir,
        )

        tokenizer_class = self.hparams.tokenizer_class.lower() if self.hparams.tokenizer_class is not None else None
        self.config.update({"tokenizer_class": tokenizer_class})
        tokenizer_class = TOKENIZERS.get(tokenizer_class, AutoTokenizer)
        self.tokenizer = tokenizer_class.from_pretrained(self.hparams.pretrained_model_name_or_path,
                                                         cache_dir=cache_dir)

        self.n_gpu_used = torch.cuda.device_count()
        self.batch_size_per_gpu = int(np.ceil(
            np.ceil(self.hparams.batch_size / self.hparams.accumulate_grad_batches) / self.n_gpu_used))
        self.effective_batch_size = self.batch_size_per_gpu * self.n_gpu_used * self.hparams.accumulate_grad_batches

    def forward(self, **inputs):
        return self.model(**inputs)

    def prepare_data(self):
        """Called to initialize data. Use the call to construct features"""
        for set_type in ["train", "dev", "test"]:
            logger.info("Creating features from dataset file at %s", args.data_dir)

            if set_type == "train":
                examples = self.processor.get_train_examples()
            elif set_type == "dev":
                examples = self.processor.get_dev_examples()
            else:
                examples = self.processor.get_test_examples()
            features = convert_examples_to_features(
                examples,
                self.tokenizer,
                max_length=args.max_seq_length,
                label_list=self.labels
            )
            cached_features_file = self.get_feature_file_name(set_type)
            logger.info("Saving features into cached file %s", cached_features_file)
            torch.save(features, cached_features_file)

    def setup(self, stage):
        self.trainset = self.get_dataset("train")
        self.devset = self.get_dataset("dev")
        self.testset = self.get_dataset("test")
        steps_per_epoch = (len(self.trainset) - 1) // self.effective_batch_size + 1
        self.total_steps = steps_per_epoch * self.hparams.max_epochs

    def get_dataset(self, set_type):
        """Load datasets. Called after prepare data."""
        cached_features_file = self.get_feature_file_name(set_type)
        logger.info("Loading features from cached file %s", cached_features_file)
        features = torch.load(cached_features_file)
        all_input_ids = torch.tensor([f.input_ids for f in features], dtype=torch.long)
        all_attention_mask = torch.tensor([f.attention_mask for f in features], dtype=torch.long)
        all_token_type_ids = torch.tensor([f.token_type_ids for f in features], dtype=torch.long)
        all_labels = torch.tensor([f.label for f in features], dtype=torch.long)
        return TensorDataset(all_input_ids, all_attention_mask, all_token_type_ids, all_labels)

    def train_dataloader(self):
        return DataLoader(self.trainset, batch_size=self.batch_size_per_gpu, shuffle=True, pin_memory=True)

    def val_dataloader(self):
        return DataLoader(self.devset, batch_size=self.batch_size_per_gpu, shuffle=False, pin_memory=True)

    def test_dataloader(self):
        return DataLoader(self.testset, batch_size=self.batch_size_per_gpu, shuffle=False, pin_memory=True)

    def training_step(self, batch, batch_idx):
        inputs = {"input_ids": batch[0], "attention_mask": batch[1], "labels": batch[3]}
        if self.config.model_type != "distilbert":
            inputs["token_type_ids"] = batch[2] if self.config.model_type in ["bert", "xlnet", "albert"] else None
        outputs = self(**inputs)
        loss = outputs[0]
        result = {"loss": loss}
        log = {"loss": loss}
        result.update({"log": log})
        return result

    def validation_step(self, batch, batch_idx):
        inputs = {"input_ids": batch[0], "attention_mask": batch[1], "labels": batch[3]}
        batches_size = torch.tensor(batch[0].size()[0], dtype=torch.float, device=self.device)
        if self.config.model_type != "distilbert":
            inputs["token_type_ids"] = batch[2] if self.config.model_type in ["bert", "xlnet", "albert"] else None
        outputs = self(**inputs)
        eval_loss_batch, logits = outputs[:2]

        result = {"eval_loss": eval_loss_batch.unsqueeze(0), "logits": logits, "target": inputs["labels"], "batches_size": batches_size.unsqueeze(0)}
        return result

    def test_step(self, batch, batch_nb):
        return self.validation_step(batch, batch_nb)

    def eval_epoch_end(self, outputs):
        batches_size = torch.cat([x["batches_size"] for x in outputs])
        eval_loss = torch.cat([x["eval_loss"] for x in outputs])
        logits = torch.cat([x["logits"] for x in outputs])
        out_label_ids = torch.cat([x["target"] for x in outputs])
        eval_loss = eval_loss.matmul(batches_size).div(batches_size.sum())
        preds = torch.argmax(logits, dim=1)
        acc = accuracy(preds, out_label_ids)
        if self.n_gpu_used > 1 and torch.distributed.is_available():
            eval_loss = self.gather_tensor_across_gpus(eval_loss).mean()
            acc = self.gather_tensor_across_gpus(acc).mean()
        return eval_loss, acc

    def validation_epoch_end(self, outputs) -> dict:
        val_loss, acc = self.eval_epoch_end(outputs)
        result = {"val_loss": val_loss, "acc": acc}
        log = {"val_loss": val_loss, "acc": acc}
        progress_bar = {"val_loss": val_loss, "acc": acc}
        result.update({"log": log, "progress_bar": progress_bar})
        return result

    def test_epoch_end(self, outputs) -> dict:
        test_loss, acc = self.eval_epoch_end(outputs)
        result = {"test_loss": test_loss, "acc": acc}
        log = {"test_loss": test_loss, "acc": acc}
        progress_bar = {"test_loss": test_loss, "acc": acc}
        result.update({"log": log, "progress_bar": progress_bar})
        return result

    def gather_tensor_across_gpus(self, tensor):
        if not tensor.size():
            tensor.unsqueeze_(0)
        tensor_list = [torch.empty_like(tensor) for _ in range(self.trainer.world_size)]
        torch.distributed.all_gather(tensor_list, tensor)
        return torch.cat(tensor_list)

    def get_feature_file_name(self, set_type):
        return os.path.join(
            self.hparams.data_dir,
            "cached_{}_{}_{}".format(
                set_type,
                os.path.split(os.path.realpath(self.hparams.pretrained_model_name_or_path))[-1],
                str(self.hparams.max_seq_length),
            ),
        )

    @rank_zero_only
    def on_save_checkpoint(self, checkpoint: Dict[str, Any]) -> None:
        save_path = self.output_dir.joinpath("best_model")
        save_path.mkdir(exist_ok=True)
        self.model.save_pretrained(save_path)
        self.tokenizer.save_pretrained(save_path)

    def configure_optimizers(self):
        """Prepare optimizer and schedule (linear warmup and decay)"""
        model = self.model
        no_decay = ["bias", "LayerNorm.weight"]
        optimizer_grouped_parameters = [
            {
                "params": [p for n, p in model.named_parameters() if not any(nd in n for nd in no_decay)]
            },
            {
                "params": [p for n, p in model.named_parameters() if any(nd in n for nd in no_decay)],
                "weight_decay": 0.0
            },
        ]
        optimizer = torch.optim.AdamW(optimizer_grouped_parameters, lr=self.hparams.learning_rate)
        self.opt = optimizer
        scheduler = get_linear_schedule_with_warmup(
            self.opt, num_warmup_steps=int(self.hparams.warmup_prop * self.total_steps),
            num_training_steps=self.total_steps
        )
        scheduler = {"scheduler": scheduler, "interval": "step", "frequency": 1}
        return [optimizer], [scheduler]

    @staticmethod
    def add_model_specific_args(parser):
        # generic
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Whether to switch to debug mode",
        )
        parser.add_argument(
            "--output_dir",
            default="output_dir",
            type=str,
            help="The output directory where the model predictions and checkpoints will be written.",
        )
        parser.add_argument(
            "--fp16",
            action="store_true",
            help="Whether to use 16-bit (mixed) precision (through NVIDIA apex) instead of 32-bit",
        )

        parser.add_argument(
            "--fp16_opt_level",
            type=str,
            default="O2",
            help="For fp16: Apex AMP optimization level selected in ['O0', 'O1', 'O2', and 'O3']."
                 "See details at https://nvidia.github.io/apex/amp.html",
        )
        parser.add_argument("--gpus", type=int, default=-1)
        parser.add_argument("--distributed_backend", type=str, default="ddp_spawn")
        parser.add_argument("--do_train", action="store_true", help="Whether to run training.")
        parser.add_argument("--do_predict", action="store_true", help="Whether to run predictions on the test set.")
        parser.add_argument("--accumulate_grad_batches", type=int, default=1,
                            help="Number of updates steps to accumulate before performing a backward/update pass.")
        parser.add_argument("--seed", type=int, default=42, help="random seed for initialization")

        # model
        parser.add_argument(
            "--pretrained_model_name_or_path",
            default=None,
            type=str,
            required=True,
            help="Path to pretrained model or model identifier from huggingface.co/models",
        )
        parser.add_argument(
            "--model_class", default=None, type=str, help="Pretrained model class"
        )
        parser.add_argument(
            "--tokenizer_class",
            default=None,
            type=str,
            help="Pretrained tokenizer class",
        )
        parser.add_argument(
            "--cache_dir",
            default=os.path.join(os.path.dirname(__file__), "tfs_cache"),
            type=str,
            help="Where do you want to store the pre-trained models downloaded from s3",
        )

        # train
        parser.add_argument("--num_workers", default=0, type=int, help="kwarg passed to DataLoader")
        parser.add_argument("--max_epochs", default=3, type=int)
        parser.add_argument("--batch_size", default=32, type=int)
        parser.add_argument("--learning_rate", default=5e-5, type=float, help="The initial learning rate for Adam.")
        parser.add_argument("--warmup_prop", default=0, type=float,
                            help="The proportion of warmup steps to the total steps.")
        parser.add_argument("--max_grad_norm", dest="gradient_clip_val", default=1.0, type=float,
                            help="Max gradient norm")

        # task
        parser.add_argument(
            "--max_seq_length",
            default=128,
            type=int,
            help="The maximum total input sequence length after tokenization. Sequences longer "
                 "than this will be truncated, sequences shorter will be padded.",
        )
        parser.add_argument("--task", default="", type=str, required=True, help="The task to run")
        parser.add_argument(
            "--data_dir",
            default=None,
            type=str,
            required=True,
            help="The input data dir. Should contain the training files for the CoNLL-2003 NER task.",
        )

        return parser


class LoggingCallback(pl.Callback):
    def on_validation_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule):
        rank_zero_info("\n***** Validation results *****")
        metrics = trainer.callback_metrics
        # Log results
        for key in sorted(metrics):
            if key not in ["log", "progress_bar"]:
                rank_zero_info(f"{key} = {metrics[key]}")

    def on_test_end(self, trainer: pl.Trainer, pl_module: pl.LightningModule):
        metrics = trainer.callback_metrics
        # Log and save results to file
        output_test_results_file = os.path.join(pl_module.hparams.output_dir, "test_results.txt")
        with open(output_test_results_file, "w", encoding="utf-8") as f:
            rank_zero_info("\n***** Test results *****")
            print("***** Test results *****", file=f)
            for key in sorted(metrics):
                if key not in ["log", "progress_bar"]:
                    rank_zero_info(f"{key} = {metrics[key]}")
                    print(f"{key} = {metrics[key]}", file=f)


def get_trainer(model: pl.LightningModule, args: argparse.Namespace):
    if rank_zero_only.rank == 0:
        # empty output_dir
        if os.path.exists(model.hparams.output_dir):
            shutil.rmtree(model.hparams.output_dir)
        os.makedirs(model.hparams.output_dir, exist_ok=True)

    # checkpoint_callback
    checkpoint_callback = pl.callbacks.ModelCheckpoint(filepath=args.output_dir, monitor="val_loss", mode="min",
                                                       save_top_k=1)
    # early_stop_callback
    early_stop_callback = pl.callbacks.EarlyStopping(monitor='val_loss', min_delta=0.00, patience=10, verbose=False,
                                                     mode='min')
    # logging_callback
    logging_callback = LoggingCallback()

    # train_params
    train_params = {}
    if args.fp16:
        train_params["precision"] = 16
        train_params["amp_level"] = args.fp16_opt_level
    if model.n_gpu_used <= 1 or not torch.distributed.is_available():
        train_params["distributed_backend"] = None
    if args.debug:
        train_params["weights_summary"] = "full"

    trainer = pl.Trainer.from_argparse_args(
        args,
        default_root_dir=args.output_dir,
        callbacks=[logging_callback, LearningRateLogger()],
        checkpoint_callback=checkpoint_callback,
        early_stop_callback=early_stop_callback,
        deterministic=True,
        sync_batchnorm=True,
        **train_params,
    )

    return trainer


if __name__ == "__main__":
    assert torch.cuda.device_count() > 0, "No CUDA devices found"
    # argparse
    parser = argparse.ArgumentParser()
    parser = BERTTransformer.add_model_specific_args(parser)
    args = parser.parse_args()

    # seed_everything
    pl.seed_everything(args.seed)

    # init model and trainer
    model = BERTTransformer(args)
    trainer = get_trainer(model, args)

    # fit
    trainer.fit(model)

    # test
    trainer.test()

    # delete checkpoints to save disk space
    checkpoints = glob.glob(os.path.join(args.output_dir, "epoch=*.ckpt"))
    if rank_zero_only.rank == 0:
        for ckpt in checkpoints:
            os.remove(ckpt)
