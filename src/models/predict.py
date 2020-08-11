import time

import torch
from transformers import (
    AdamW,
    AutoConfig,
    AutoModelForSequenceClassification,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
)
from utils import processors, convert_examples_to_features, compute_metrics, SEQUENCE_CLASSIFICATION_MODELS, TOKENIZERS


class Bert_Classifier(object):
    def __init__(self, model_name_or_path):
        self.config = AutoConfig.from_pretrained(model_name_or_path)

        model_class = SEQUENCE_CLASSIFICATION_MODELS.get(self.config.model_type, AutoModelForSequenceClassification)
        self.model = model_class.from_pretrained(model_name_or_path)
        self.model.eval()

        tokenizer_class = TOKENIZERS.get(self.config.model_type, AutoTokenizer)
        self.tokenizer = tokenizer_class.from_pretrained(model_name_or_path)

    @torch.no_grad()
    def predict(self, text):
        input = self.tokenizer(text, return_tensors="pt")
        logits = self.model(**input)[0]
        prop = torch.softmax(logits, dim=1)
        label_id = torch.argmax(logits, dim=1).item()
        label = self.config.id2label[label_id]
        return label, prop[0][label_id].item()


if __name__ == "__main__":
    model_name_or_path = "intent-pl-bert/best_tfmr"
    model = Bert_Classifier(model_name_or_path)
    print(model.predict('去哪交电费'))