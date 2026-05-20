import pandas as pd
import numpy as np
import requests
import json
import streamlit as st
from typing import List, Dict, Any
from BackEnd.core.logging_config import get_logger

logger = get_logger("rag_engine")

class SimpleVectorStore:
    """In-memory numpy-based vector store for lightweight RAG."""
    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self.vectors: np.ndarray = np.array([])

    def add_documents(self, documents: List[Dict[str, Any]], embeddings: np.ndarray):
        self.documents.extend(documents)
        if self.vectors.size == 0:
            self.vectors = embeddings
        else:
            self.vectors = np.vstack([self.vectors, embeddings])

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.vectors.size == 0:
            return []
        
        # Cosine similarity: dot product of normalized vectors
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        vectors_norm = self.vectors / np.linalg.norm(self.vectors, axis=1)[:, np.newaxis]
        similarities = np.dot(vectors_norm, query_norm)
        
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            doc = self.documents[idx].copy()
            doc["score"] = similarities[idx]
            results.append(doc)
            
        return results

class RAGAgent:
    """Retrieval-Augmented Generation Agent for Data Pilot."""
    
    def __init__(self, model_name: str = "gemma", base_url: str = "http://localhost:11434", agent_type: str = "Local AI Agent"):
        self.model_name = model_name
        self.base_url = base_url.rstrip('/')
        self.agent_type = agent_type
        self.vector_store = SimpleVectorStore()
        self._api_key = st.secrets.get("GEMINI_API_KEY") if agent_type == "Google Gemini" else None

    def _get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using the configured provider."""
        if not texts:
            return np.array([])
            
        if self.agent_type == "Google Gemini":
            try:
                import google.generativeai as genai
                genai.configure(api_key=self._api_key)
                # Using standard Gemini embedding model
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=texts,
                    task_type="retrieval_document"
                )
                return np.array(result['embedding'])
            except Exception as e:
                logger.error(f"Gemini Embedding Error: {e}")
                return np.zeros((len(texts), 768)) # Fallback zero vector
        else:
            # Local Ollama Embeddings (e.g., nomic-embed-text)
            embeddings = []
            url = f"{self.base_url}/api/embeddings"
            for text in texts:
                try:
                    payload = {"model": "nomic-embed-text", "prompt": text}
                    res = requests.post(url, json=payload, timeout=10)
                    if res.status_code == 200:
                        embeddings.append(res.json().get("embedding", []))
                    else:
                        embeddings.append(np.zeros(768).tolist())
                except Exception as e:
                    logger.error(f"Ollama Embedding Error: {e}")
                    embeddings.append(np.zeros(768).tolist())
            return np.array(embeddings)

    def _ingest_dataframe(self, df: pd.DataFrame, max_rows: int = 500):
        """Convert DataFrame rows into searchable text documents."""
        if df.empty:
            return
            
        # Take recent rows to avoid massive API overhead for a quick response
        sample_df = df.tail(max_rows).copy()
        
        docs = []
        texts = []
        
        for _, row in sample_df.iterrows():
            # Format the row into a readable chunk
            row_dict = row.dropna().to_dict()
            text_chunk = ", ".join([f"{k}: {v}" for k, v in row_dict.items()])
            texts.append(text_chunk)
            docs.append({"content": text_chunk, "metadata": {"index": _}})
            
        embeddings = self._get_embeddings(texts)
        if embeddings.size > 0:
            self.vector_store.add_documents(docs, embeddings)

    def query(self, prompt: str, context_df: pd.DataFrame) -> str:
        """Full RAG Pipeline: Ingest -> Embed Query -> Retrieve -> Generate."""
        # 1. Ingest Data (Ideally cached, but done here dynamically for the query context)
        self._ingest_dataframe(context_df)
        
        # 2. Embed the User Query
        query_emb = self._get_embeddings([prompt])
        if query_emb.size == 0 or not query_emb.any():
            return "⚠️ Vector Search Unavailable: Could not generate embeddings. Ensure your embedding model is active."
            
        # 3. Retrieve Top K relevant records
        retrieved_docs = self.vector_store.search(query_emb[0], top_k=7)
        
        context_block = "\n\n".join([f"Record: {doc['content']}" for doc in retrieved_docs])
        
        # 4. Augmented Generation
        system_prompt = f"""
        You are DEEN-BI Data Pilot, an expert e-commerce analyst.
        You have performed a semantic search on the database. Here are the most relevant row records for the user's query:
        
        {context_block}
        
        Answer the user's question accurately based ONLY on these specific records. Be concise, professional, and use markdown.
        """
        
        if self.agent_type == "Google Gemini":
            import google.generativeai as genai
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(f"{system_prompt}\n\nUser Question: {prompt}")
            return response.text
        else:
            is_ollama = "11434" in self.base_url
            url = f"{self.base_url}/api/generate" if is_ollama else f"{self.base_url}/v1/chat/completions"
            
            payload = {
                "model": self.model_name,
                "prompt": f"{system_prompt}\n\nUser Question: {prompt}",
                "stream": False
            }
            
            response = requests.post(url, json=payload, timeout=30)
            res_json = response.json()
            return res_json.get("response", "No response.") if is_ollama else res_json.get("choices", [{}])[0].get("message", {}).get("content", "No response.")