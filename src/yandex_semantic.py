import re
import pickle
import os
import numpy as np
import faiss
from langchain_community.embeddings.yandex import YandexGPTEmbeddings

def preprocess_text(text: str) -> str:
    if not text:
        return ""
    
    text = text.lower()
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'@\w+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


class YandexSemanticSearch:
    def __init__(self, folder_id: str, api_key: str):
        self.folder_id = folder_id
        self.api_key = api_key
        
        self.doc_embeddings = YandexGPTEmbeddings(
            api_key=api_key,
            folder_id=folder_id,
            model_uri=f"emb://{folder_id}/text-search-doc/latest"
        )
        
        self.query_embeddings = YandexGPTEmbeddings(
            api_key=api_key,
            folder_id=folder_id,
            model_uri=f"emb://{folder_id}/text-search-query/latest"
        )
        
        test_vector = self.query_embeddings.embed_query("test")
        self.dimension = len(test_vector)
        print(f"Размерность вектора: {self.dimension}")
        
        self.index = faiss.IndexFlatIP(self.dimension)
        self.prompts_metadata = []
        self._last_index_mtime = None
        
        self._load_index()
    
    def get_all_prompts(self):
        return self.prompts_metadata.copy()
    
    def get_user_prompts(self, user_id):
        user_prompts = []
        for uid, text, pid in self.prompts_metadata:
            if uid == user_id:
                user_prompts.append({"id": pid, "text": text})
        return user_prompts
    
    def get_next_available_id(self):
        if not self.prompts_metadata:
            return 1
        
        existing_ids = sorted([pid for _, _, pid in self.prompts_metadata])
        
        expected_id = 1
        for pid in existing_ids:
            if pid > expected_id:
                return expected_id
            expected_id = pid + 1
        
        return existing_ids[-1] + 1
    
    def remove_prompt_by_id(self, prompt_id):
        index_to_remove = None
        for i, (uid, text, pid) in enumerate(self.prompts_metadata):
            if pid == prompt_id:
                index_to_remove = i
                break
        
        if index_to_remove is not None:
            removed = self.prompts_metadata.pop(index_to_remove)
            
            if self.prompts_metadata:
                new_index = faiss.IndexFlatIP(self.dimension)
                for uid, text, pid in self.prompts_metadata:
                    vector = self.vectorize_prompt(text)
                    vector = vector.reshape(1, -1).astype(np.float32)
                    new_index.add(vector)
                self.index = new_index
            else:
                self.index = faiss.IndexFlatIP(self.dimension)
            
            self._save_index()
            return removed
        return None
    
    def _reload_index_if_needed(self):
        index_path = "./data/faiss.index"
        prompts_path = "./data/prompts.pkl"
        
        if os.path.exists(index_path) and os.path.exists(prompts_path):
            index_mtime = os.path.getmtime(index_path)
            
            if self._last_index_mtime is None or index_mtime > self._last_index_mtime:
                print(f"Индекс изменился, перезагружаем...")
                self._load_index()
                self._last_index_mtime = index_mtime
                return True
        return False
    
    def vectorize_prompt(self, prompt_text: str) -> np.ndarray:
        clean_text = preprocess_text(prompt_text)
        vector = self.query_embeddings.embed_query(clean_text)
        return np.array(vector, dtype=np.float32)
    
    def vectorize_message(self, message_text: str) -> np.ndarray:
        clean_text = preprocess_text(message_text)
        vector = self.doc_embeddings.embed_query(clean_text)
        return np.array(vector, dtype=np.float32)
    
    def add_prompt(self, user_id: int, prompt_text: str):
        prompt_id = self.get_next_available_id()
        vector = self.vectorize_prompt(prompt_text)
        
        if len(vector) != self.dimension:
            print(f"Ошибка размерности: ожидалось {self.dimension}, получено {len(vector)}")
            self.dimension = len(vector)
            self.index = faiss.IndexFlatIP(self.dimension)
        
        vector = vector.reshape(1, -1).astype(np.float32)
        self.index.add(vector)
        self.prompts_metadata.append((user_id, prompt_text, prompt_id))
        self._save_index()
        print(f"Промпт добавлен: {prompt_text[:50]}... (ID: {prompt_id})")
        return prompt_id
    
    def search(self, message_text: str, threshold: float = 0.65, top_k: int = 10):
        self._reload_index_if_needed()
        
        if self.index.ntotal == 0:
            return []
        
        query_vector = self.vectorize_message(message_text)
        query_vector = query_vector.reshape(1, -1).astype(np.float32)
        
        distances, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and distances[0][i] >= threshold:
                user_id, prompt_text, prompt_id = self.prompts_metadata[idx]
                results.append({
                    'user_id': user_id,
                    'prompt': prompt_text,
                    'prompt_id': prompt_id,
                    'similarity': float(distances[0][i])
                })
        
        return results
    
    def _save_index(self):
        os.makedirs("./data", exist_ok=True)
        faiss.write_index(self.index, "./data/faiss.index")
        with open("./data/prompts.pkl", "wb") as f:
            pickle.dump(self.prompts_metadata, f)
        
        if os.path.exists("./data/faiss.index"):
            self._last_index_mtime = os.path.getmtime("./data/faiss.index")
    
    def _load_index(self):
        if os.path.exists("./data/faiss.index"):
            self.index = faiss.read_index("./data/faiss.index")
            with open("./data/prompts.pkl", "rb") as f:
                self.prompts_metadata = pickle.load(f)
            self.dimension = self.index.d
            print(f"Индекс загружен. Промптов: {len(self.prompts_metadata)}")
            
            if os.path.exists("./data/faiss.index"):
                self._last_index_mtime = os.path.getmtime("./data/faiss.index")