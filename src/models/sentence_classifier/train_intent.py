import os
import shutil
import random

import torch

from train import train, get_argparser
from build_datasets import build_datasets

PRETRAINED_MODEL_NAME_DICT = {
    "bert": "bert-base-chinese",
    "roberta": "hfl/chinese-roberta-wwm-ext",
    "xlnet": "hfl/chinese-xlnet-base",
    "albert": "voidful/albert_chinese_base"
}

MODEL_CLASS_DICT = {
    "bert": "bert",
    "roberta": "bert",
    "xlnet": "xlnet",
    "albert": "albert"

}

TOKENIZER_CLASS_DICT = {
    "bert": "bert",
    "roberta": "bert",
    "xlnet": "xlnet",
    "albert": "bert"

}

if __name__ == '__main__':
    assert torch.cuda.device_count() > 0, "No CUDA devices found"

    parser = get_argparser()
    parser.add_argument("--model_type", default="bert", type=str)
    args = parser.parse_args()
    args.task = "intent"
    if not args.pretrained_model_name_or_path:
        args.pretrained_model_name_or_path = PRETRAINED_MODEL_NAME_DICT[args.model_type]
    if not args.model_class:
        args.model_class = MODEL_CLASS_DICT[args.model_type]
    if not args.tokenizer_class:
        args.tokenizer_class = TOKENIZER_CLASS_DICT[args.model_type]

    ckpt_dir = os.path.join("checkpoints", args.task, args.model_type)
    data_dir = os.path.join("datasets", args.task)
    shutil.rmtree(ckpt_dir, ignore_errors=True)
    shutil.rmtree(data_dir, ignore_errors=True)

    os.makedirs(data_dir, exist_ok=True)
    random.seed(args.seed)
    samples_path = 'dialog_config/corpus/samples.json'
    if os.path.exists(samples_path):
        build_datasets(samples_path, data_dir)

    if args.data_dir is None:
        args.data_dir = data_dir
    if args.output_dir is None:
        args.output_dir = ckpt_dir
    if args.max_seq_length is None:
        args.max_seq_length = 64
    if args.batch_size is None:
        args.batch_size = 64
    if args.max_epochs is None:
        args.max_epochs = 100
    if args.learning_rate is None:
        args.learning_rate = 3e-5
    if args.warmup_prop is None:
        args.warmup_prop = 0.1

    train(args)
