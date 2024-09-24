# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

from memory import MemoryStore
from active_learning.py import ActiveLearner

app = FastAPI(title="Dynamic Memory Transformer with Active Learning")

# Initialize components
MODEL_NAME = "distilgpt2"  # Use a small transformer model
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
model.eval()

memory_store = MemoryStore()
active_learner = ActiveLearner(MODEL_NAME, tokenizer, model)

class Query(BaseModel):
    text: str

class FeedbackData(BaseModel):
    user_input: str
    model_response: str
    feedback: str  # Corrected response from the user

@app.post("/generate")
def generate(query: Query):
    try:
        # Retrieve relevant memory
        memory = memory_store.retrieve_memory(query.text)
        memory_context = " ".join(memory)
        
        # Combine user input with memory context
        augmented_input = f"Context: {memory_context}\nUser: {query.text}\nAssistant:"
        
        # Tokenize and generate response
        inputs = tokenizer.encode(augmented_input, return_tensors='pt')
        outputs = model.generate(inputs, max_length=150, pad_token_id=tokenizer.eos_token_id)
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract the assistant's reply
        assistant_reply = response.split("Assistant:")[-1].strip()
        
        # Update memory with the latest interaction
        memory_store.add_to_memory(query.text)
        memory_store.add_to_memory(assistant_reply)
        
        return {"response": assistant_reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
def feedback(feedback_data: FeedbackData):
    try:
        # Measure uncertainty
        combined_input = f"Context: {' '.join(memory_store.retrieve_memory(feedback_data.user_input))}\nUser: {feedback_data.user_input}\nAssistant:"
        inputs = tokenizer.encode(combined_input, return_tensors='pt')
        uncertainty = active_learner.measure_uncertainty(inputs)
        
        threshold = 1.0  # Define your own threshold based on experimentation
        if uncertainty > threshold:
            # Fine-tune the model with user feedback
            corrected_response = feedback_data.feedback
            input_ids = tokenizer.encode(combined_input, return_tensors='pt')
            labels = tokenizer.encode(f"Assistant: {corrected_response}", return_tensors='pt')
            loss = active_learner.fine_tune(input_ids, labels)
            return {"status": "Model fine-tuned", "loss": loss}
        else:
            return {"status": "No fine-tuning needed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)}
