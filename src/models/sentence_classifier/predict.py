import time

import torch
from transformers import (
    AutoConfig,
    AutoModelForSequenceClassification,
    AutoTokenizer
)

from .utils import SEQUENCE_CLASSIFICATION_MODELS, TOKENIZERS


class Bert_Classifier(object):
    def __init__(self, model_path):
        self.config = AutoConfig.from_pretrained(model_path)

        model_class = SEQUENCE_CLASSIFICATION_MODELS.get(self.config.model_class, AutoModelForSequenceClassification)
        self.model = model_class.from_pretrained(model_path)
        self.model.eval()

        tokenizer_class = TOKENIZERS.get(self.config.tokenizer_class, AutoTokenizer)
        self.tokenizer = tokenizer_class.from_pretrained(model_path)

    @torch.no_grad()
    def predict(self, text):
        input = self.tokenizer(text, return_tensors="pt")
        logits = self.model(**input)[0]
        prop = torch.softmax(logits, dim=1)
        label_id = torch.argmax(logits, dim=1).item()
        label = self.config.id2label[label_id]
        return label, prop[0][label_id].item()
