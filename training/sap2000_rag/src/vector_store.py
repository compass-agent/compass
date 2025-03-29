"""
Vector Store Module

Manages the Chroma vector database for storing and querying document embeddings.
"""

import os
import logging
import chromadb

logger = logging.getLogger(__name__)

class VectorStore:
    """Manages the Chroma vector database for document embeddings"""
    
    def __init__(self, db_path):
        """
        Initialize with path to database.
        
        Args:
            db_path (str): Path to Chroma database directory
        """
        self.db_path = db_path
        os.makedirs(db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(path=db_path)
        logger.info(f"Initialized VectorStore at {db_path}")
    
    def create_collection(self, name="sap2000_api", metadata=None):
        """
        Create a new collection or get existing one.
        
        Args:
            name (str): Collection name
            metadata (dict, optional): Collection metadata
            
        Returns:
            Collection: ChromaDB collection object
        """
        try:
            # Try to get existing collection
            collection = self.client.get_collection(name)
            logger.info(f"Retrieved existing collection '{name}'")
        except Exception:  # Handle any ChromaDB-related exceptions
            # Create new collection if it doesn't exist
            metadata = metadata or {"description": "SAP2000 API Documentation"}
            collection = self.client.create_collection(
                name=name,
                metadata=metadata
            )
            logger.info(f"Created new collection '{name}'")
            
        return collection
    
    def collection_exists(self, name):
        """
        Check if a collection exists.
        
        Args:
            name (str): Collection name
            
        Returns:
            bool: True if collection exists, False otherwise
        """
        try:
            self.client.get_collection(name)
            return True
        except Exception:  # Handle any ChromaDB-related exceptions
            return False
    
    def add_documents(self, collection_name, embedded_chunks):
        """
        Add embedded documents to the collection.
        
        Args:
            collection_name (str): Collection name
            embedded_chunks (list): List of chunks with embeddings
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not embedded_chunks:
            logger.warning("No embedded chunks to add")
            return False
            
        try:
            # Get or create collection
            collection = self.create_collection(collection_name)
            
            # Prepare data for ChromaDB
            ids = [f"doc_{i}" for i in range(len(embedded_chunks))]
            documents = [chunk['content'] for chunk in embedded_chunks]
            embeddings = [chunk['embedding'] for chunk in embedded_chunks]
            metadatas = [chunk['metadata'] for chunk in embedded_chunks]
            
            # Add to collection
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(embedded_chunks)} documents to collection '{collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents to collection '{collection_name}': {e}")
            return False
    
    def query(self, collection_name, query_embedding, n_results=5):
        """
        Query the vector database.
        
        Args:
            collection_name (str): Collection name
            query_embedding (list): Query embedding vector
            n_results (int): Number of results to return
            
        Returns:
            dict: Query results with documents, metadatas, and distances
        """
        try:
            # Get collection
            collection = self.client.get_collection(collection_name)
            
            # Query 
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"] # type: ignore
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error querying collection '{collection_name}': {e}")
            return None 