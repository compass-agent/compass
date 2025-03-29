"""
Embedding Manager Module

Handles the creation and management of embeddings for document chunks.
"""

import os
import json
import logging
from openai import OpenAI
import time
from compass.key import OPENAI_API_KEY
MODEL = "text-embedding-3-small"
logger = logging.getLogger(__name__)

class EmbeddingManager:
    """Manages the creation and storage of embeddings"""
    
    def __init__(self):
        """
        Initialize with OpenAI API key and model.
        
        Args:
            api_key (str, optional): OpenAI API key. If None, uses environment variable.
            model (str): OpenAI embedding model name
        """
        self.model = MODEL
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info(f"Initialized EmbeddingManager with model {MODEL}")
    
    def generate_embeddings(self, chunks, batch_size=100, output_file=None):
        """
        Generate embeddings for document chunks.
        
        Args:
            chunks (list): List of document chunks
            batch_size (int): Number of chunks to process in one batch
            output_file (str, optional): Path to save embedded chunks
            
        Returns:
            list: List of chunks with embeddings added
        """
        if not chunks:
            logger.warning("No chunks provided for embedding generation")
            return []
            
        logger.info(f"Generating embeddings for {len(chunks)} chunks using {self.model}")
        
        # Process in batches to avoid rate limits
        embedded_chunks = []
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            batch_texts = [chunk['content'] for chunk in batch]
            
            try:
                # Call OpenAI embedding API
                response = self.client.embeddings.create(
                    input=batch_texts,
                    model=self.model
                )
                
                # Extract embeddings from response
                batch_embeddings = [data.embedding for data in response.data]
                
                # Add embeddings to chunks
                for j, embedding in enumerate(batch_embeddings):
                    chunk_with_embedding = batch[j].copy()
                    chunk_with_embedding['embedding'] = embedding
                    embedded_chunks.append(chunk_with_embedding)
                
                logger.info(f"Generated embeddings for batch {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}")
                
                # Respect rate limits - sleep between batches
                if i + batch_size < len(chunks):
                    time.sleep(1)  # Add a small delay between batches
                    
            except Exception as e:
                logger.error(f"Error generating embeddings for batch starting at index {i}: {e}")
                # Continue with next batch instead of failing completely
                continue
        
        # Save to file if specified
        if output_file and embedded_chunks:
            try:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(embedded_chunks, f, indent=2)
                logger.info(f"Saved {len(embedded_chunks)} embedded chunks to {output_file}")
            except Exception as e:
                logger.error(f"Error saving embeddings to {output_file}: {e}")
        
        return embedded_chunks
    
    def get_embedding_for_query(self, query_text):
        """
        Generate embedding for a query string.
        
        Args:
            query_text (str): Query text to embed
            
        Returns:
            list: Embedding vector
        """
        if not query_text:
            logger.warning("Empty query text provided")
            return None
            
        try:
            response = self.client.embeddings.create(
                input=[query_text],
                model=self.model
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding for query: {e}")
            return None
    
    def load_embeddings(self, embeddings_file):
        """
        Load previously generated embeddings from file.
        
        Args:
            embeddings_file (str): Path to embeddings file
            
        Returns:
            list: List of chunks with embeddings
        """
        if not os.path.exists(embeddings_file):
            logger.warning(f"Embeddings file not found: {embeddings_file}")
            return []
        
        try:
            with open(embeddings_file, 'r', encoding='utf-8') as f:
                embedded_chunks = json.load(f)
            logger.info(f"Loaded {len(embedded_chunks)} embedded chunks from {embeddings_file}")
            return embedded_chunks
        except Exception as e:
            logger.error(f"Error loading embeddings from {embeddings_file}: {e}")
            return [] 