# active_learning.py
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForCausalLM, AdamW

class ActiveLearner:
    def __init__(self, model_name, tokenizer, model):
        self.tokenizer = tokenizer
        self.model = model
        self.optimizer = AdamW(self.model.parameters(), lr=5e-5)

    def measure_uncertainty(self, inputs):
        with torch.no_grad():
            outputs = self.model(inputs, labels=inputs)
            loss = outputs.loss
        return loss.item()

    def fine_tune(self, input_ids, labels):
        self.model.train()
        outputs = self.model(input_ids=input_ids, labels=labels)
        loss = outputs.loss
        loss.backward()
        self.optimizer.step()
        self.optimizer.zero_grad()
        self.model.eval()
        return loss.item()
