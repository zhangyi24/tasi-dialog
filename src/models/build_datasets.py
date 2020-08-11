# coding=utf-8
# Copyright 2020 Tsinghua University, Author: Yi Zhang
"""Build datasets."""

# coding=utf-8
import json
import random
import os


def build_datasets(samples_path, datasets_dir):
    with open(samples_path, 'r', encoding='utf-8') as f:
        samples = json.load(f)

    with open(os.path.join(datasets_dir, 'labels.txt'), 'w', encoding='utf-8') as f:
        intents = samples.keys()
        print('\n'.join(intents), file=f)

    train_set = {}
    dev_set = {}
    test_set = {}
    for intent in samples:
        samples_per_intent = samples[intent]['samples']
        samples_per_intent = list(set(samples_per_intent))
        samples_per_intent.sort()
        random.shuffle(samples_per_intent)
        train_set[intent] = samples_per_intent[: int(len(samples_per_intent) * 0.8)]
        dev_set[intent] = samples_per_intent[int(len(samples_per_intent) * 0.8): int(len(samples_per_intent) * 0.9)]
        test_set[intent] = samples_per_intent[int(len(samples_per_intent) * 0.9):]

    save_dataset(train_set, 'train')
    save_dataset(dev_set, 'dev')
    save_dataset(test_set, 'test')


def save_dataset(dataset, set_type):
    with open(os.path.join(datasets_dir, '%s.tsv' % set_type), 'w', encoding='utf-8') as f:
        print('\t'.join(['label', 'sample']), file=f)
        for intent, samples in dataset.items():
            for sample in samples:
                sample = sample.replace('\t', ' ').replace('\n', ' ')
                print('\t'.join([intent, sample]), file=f)


if __name__ == '__main__':
    datasets_dir = 'datasets/intent'
    os.makedirs(datasets_dir, exist_ok=True)
    random.seed(12345)
    samples_path = 'dialog_config/corpus/samples.json'
    if os.path.exists(samples_path):
        build_datasets(samples_path, datasets_dir)

