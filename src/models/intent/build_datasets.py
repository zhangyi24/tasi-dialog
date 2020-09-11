# coding=utf-8
# Copyright 2020 Tsinghua University, Author: Yi Zhang
"""Build datasets."""

# coding=utf-8
import argparse
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

    save_dataset(train_set, 'train', datasets_dir)
    save_dataset(dev_set, 'dev', datasets_dir)
    save_dataset(test_set, 'test', datasets_dir)


def save_dataset(dataset, set_type, datasets_dir):
    with open(os.path.join(datasets_dir, '%s.tsv' % set_type), 'w', encoding='utf-8') as f:
        print('\t'.join(['label', 'sample']), file=f)
        for intent, samples in dataset.items():
            for sample in samples:
                sample = sample.replace('\t', ' ').replace('\n', ' ')
                print('\t'.join([intent, sample]), file=f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", default=12345, type=int)
    args = parser.parse_args()

    datasets_dir = 'datasets/intent'
    os.makedirs(datasets_dir, exist_ok=True)
    random.seed(args.seed)
    samples_path = 'dialog_config/corpus/samples.json'
    if os.path.exists(samples_path):
        build_datasets(samples_path, datasets_dir)

