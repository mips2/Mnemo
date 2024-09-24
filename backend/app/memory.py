# backend/app/memory.py
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from sqlmodel import Session, select
from .models import Memory, User

class MemoryStore:
    def __init__(self, session: Session, user: User, embedding_model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.session = session
        self.user = user
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.dimension = self.embedding_model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(self.dimension)
        self.memory_store = []
        self.load_memories()

    def load_memories(self):
        memories = self.session.exec(select(Memory).where(Memory.user_id == self.user.id)).all()
        for memory in memories:
            embedding = self.encode(memory.content)
            self.index.add(np.array([embedding]))
            self.memory_store.append(memory.content)

    def encode(self, text):
        return self.embedding_model.encode([text])[0]

    def add_to_memory(self, text):
        embedding = self.encode(text)
        self.index.add(np.array([embedding]))
        self.memory_store.append(text)
        memory = Memory(user_id=self.user.id, content=text)
        self.session.add(memory)
        self.session.commit()

    def retrieve_memory(self, query, top_k=5):
        if self.index.ntotal == 0:
            return []
        query_embedding = self.encode(query)
        D, I = self.index.search(np.array([query_embedding]), top_k)
        retrieved = [self.memory_store[i] for i in I[0] if i < len(self.memory_store)]
        return retrieved
