from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from .memory import MemoryStore
from .active_learning import ActiveLearner

MODEL_NAME = "distilgpt2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
model.eval()

active_learner = ActiveLearner(model, tokenizer)

def generate_response(user_input, memory_store, current_user, session):
    memory = memory_store.retrieve_memory(user_input)
    memory_context = " ".join(memory)
    augmented_input = f"Context: {memory_context}\nUser: {user_input}\nAssistant:"

    inputs = tokenizer.encode(augmented_input, return_tensors='pt')
    
    with torch.no_grad():
        outputs = model.generate(
            inputs,
            max_length=150,
            pad_token_id=tokenizer.eos_token_id,
            no_repeat_ngram_size=2,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
        )
    
    response = tokenizer.decode(outputs[0], skip_special_tokens=True, clean_up_tokenization_spaces=False)
    ai_response = response.split("Assistant:")[-1].strip()

    # Update memory
    memory_store.add_to_memory(user_input)
    memory_store.add_to_memory(ai_response)

    return ai_response

def fine_tune_model(user_input, corrected_response):
    input_ids = tokenizer.encode(user_input, return_tensors='pt')
    label_ids = tokenizer.encode(corrected_response, return_tensors='pt')
    loss = active_learner.fine_tune(input_ids, label_ids)
    return loss