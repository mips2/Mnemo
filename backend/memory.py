# memory.py
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import torch

class MemoryStore:
    def __init__(self, embedding_model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.dimension = self.embedding_model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(self.dimension)
        self.memory_store = []

    def encode(self, text):
        return self.embedding_model.encode([text])[0]

    def add_to_memory(self, text):
        embedding = self.encode(text)
        self.index.add(np.array([embedding]))
        self.memory_store.append(text)

    def retrieve_memory(self, query, top_k=5):
        if self.index.ntotal == 0:
            return []
        query_embedding = self.encode(query)
        D, I = self.index.search(np.array([query_embedding]), top_k)
        retrieved = [self.memory_store[i] for i in I[0] if i < len(self.memory_store)]
        return retrieved
