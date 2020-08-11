import random
import csv
import os
import logging

from transformers import (
    InputExample,
    InputFeatures,
    BertForSequenceClassification,
    AlbertForSequenceClassification,
    XLNetForSequenceClassification,
    BertTokenizer,
    XLNetTokenizer
)
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import f1_score


SEQUENCE_CLASSIFICATION_MODELS = {
    "bert": BertForSequenceClassification,
    "albert": AlbertForSequenceClassification,
    "xlnet": XLNetForSequenceClassification
}
TOKENIZERS = {
    "bert": BertTokenizer,
    "xlnet": XLNetTokenizer
}

logger = logging.getLogger(__name__)

class DataProcessor(object):
    """Base class for data converters for sequence classification data sets."""

    def get_train_examples(self):
        """Gets a collection of `InputExample`s for the train set."""
        raise NotImplementedError()

    def get_dev_examples(self):
        """Gets a collection of `InputExample`s for the dev set."""
        raise NotImplementedError()

    def get_test_examples(self):
        """Gets a collection of `InputExample`s for prediction."""
        raise NotImplementedError()

    def get_labels(self):
        """Gets the list of labels for this data set."""
        raise NotImplementedError()

    @classmethod
    def _read_tsv(cls, input_file, quotechar=None):
        """Reads a tab separated value file."""
        with open(input_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t", quotechar=quotechar)
            lines = []
            i = 0
            for line in reader:
                if i:
                    lines.append(line)
                i += 1
            random.shuffle(lines)
            return lines


class IntentProcessor(DataProcessor):
    """Processor for the Intent Recognition data set."""

    def __init__(self, data_dir):
        self.data_dir = data_dir

    def get_train_examples(self):
        """See base class."""
        return self._create_examples(
            self._read_tsv(os.path.join(self.data_dir, "train.tsv")), "train")

    def get_dev_examples(self):
        """See base class."""
        return self._create_examples(
            self._read_tsv(os.path.join(self.data_dir, "dev.tsv")), "dev")

    def get_test_examples(self):
        """See base class."""
        return self._create_examples(
            self._read_tsv(os.path.join(self.data_dir, "test.tsv")), "test")

    def get_labels(self):
        """See base class."""
        with open(os.path.join(self.data_dir, "labels.txt"), 'r', encoding='utf-8') as f:
            labels = f.read().strip().split()
        return labels

    def _create_examples(self, lines, set_type):
        """Creates examples for the training and dev sets."""
        examples = []
        for (i, line) in enumerate(lines):
            # Only the test set has a header
            if i == 0:
                continue
            guid = "%s-%s" % (set_type, i)
            text_a = line[1]
            label = line[0]
            examples.append(
                InputExample(guid=guid, text_a=text_a, text_b=None, label=label))
        return examples


processors = {
    "intent": IntentProcessor
}

def convert_examples_to_features(examples, tokenizer, label_list, max_length=None):
    if max_length is None:
        max_length = tokenizer.max_len

    label_map = {label: i for i, label in enumerate(label_list)}

    def label_from_example(example):
        if example.label is None:
            return None
        return label_map[example.label]

    labels = [label_from_example(example) for example in examples]

    batch_encoding = tokenizer(
        [(example.text_a, example.text_b) for example in examples],
        max_length=max_length,
        padding="max_length",
        truncation=True,
    )

    features = []
    for i in range(len(examples)):
        inputs = {k: batch_encoding[k][i] for k in batch_encoding}

        feature = InputFeatures(**inputs, label=labels[i])
        features.append(feature)

    for i, example in enumerate(examples[:5]):
        logger.info("*** Example ***")
        logger.info("guid: %s" % (example.guid))
        logger.info("features: %s" % features[i])
    return features


def accuracy(preds, labels):
    return (preds == labels).mean()


def f1(preds, labels):
    return f1_score(y_true=labels, y_pred=preds, average='micro')


def pearson(preds, labels):
    return pearsonr(preds, labels)[0]


def spearman(preds, labels):
    return spearmanr(preds, labels)[0]


def compute_metrics(metrics_name, preds, labels):
    assert len(preds) == len(labels)
    metrics = {}
    for metric_name in metrics_name:
        if metric_name == "acc":
            metrics[metric_name] = accuracy(preds, labels)
        elif metric_name == "f1":
            metrics[metric_name] = f1(preds, labels)
        elif metric_name == "pearson":
            metrics[metric_name] = pearson(preds, labels)
        elif metric_name == "spearman":
            metrics[metric_name] = spearman(preds, labels)
    return metrics


