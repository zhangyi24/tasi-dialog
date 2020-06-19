# coding=utf-8
import json


with open('../../dialog_config/corpus/samples.json', 'r', encoding='utf-8') as f:
	samples = json.load(f)

with open('labels.txt', 'w', encoding='utf-8') as f:
	intents = samples.keys()
	print('\n'.join(intents), file=f)

train_set = {}
dev_set = {}
test_set = {}
for intent in samples:
	samples_per_intent = samples[intent]['samples']
	train_set[intent] = samples_per_intent[: int(len(samples_per_intent) * 0.8)]
	dev_set[intent] = samples_per_intent[int(len(samples_per_intent) * 0.8): int(len(samples_per_intent) * 0.9)]
	test_set[intent] = samples_per_intent[int(len(samples_per_intent) * 0.9):]

def save_dataset(dataset, set_type):
	with open('%s.tsv' % set_type, 'w', encoding='utf-8') as f:
		print('\t'.join(['label', 'sample']), file=f)
		for intent, samples in dataset.items():
			for sample in samples:
				print('\t'.join([intent, sample]), file=f)

save_dataset(train_set, 'train')
save_dataset(dev_set, 'dev')
save_dataset(test_set, 'test')

