"""
SAP2000 API Query Module

This module provides functionality to query the SAP2000 API documentation
using a vector database with embeddings of API documentation chunks.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
import chromadb
from openai import OpenAI
from compass.key import OPENAI_API_KEY

logger = logging.getLogger(__name__)

# Configuration
DEFAULT_DB_PATH = os.path.abspath(os.path.join("src", "compass", "database", "sap2000_api"))
DEFAULT_COLLECTION_NAME = "sap2000_api"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"

class SAPAPIQuery:
    """
    Query the SAP2000 API documentation using a RAG (Retrieval-Augmented Generation) approach
    with vector embeddings for semantic search.
    """
    
    def __init__(
        self, 
        db_path: str = DEFAULT_DB_PATH,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL
    ):
        """
        Initialize the SAP API query system.
        
        Args:
            db_path: Path to the Chroma vector database
            collection_name: Name of the collection in the database
            embedding_model: Name of the OpenAI embedding model to use
        """
        self.db_path = db_path
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        
        # Initialize OpenAI client with API key from compass/key.py
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Initialize vector database client
        self._init_vector_db()
        
        logger.info(f"Initialized SAP API Query system with DB at {db_path}")
    
    def _init_vector_db(self) -> None:
        """Initialize connection to the vector database"""
        try:
            self.db_client = chromadb.PersistentClient(path=self.db_path)
            
            # Check if collection exists
            try:
                self.collection = self.db_client.get_collection(self.collection_name)
                logger.info(f"Connected to existing collection '{self.collection_name}'")
            except chromadb.errors.InvalidCollectionException: # type: ignore
                logger.warning(f"Collection '{self.collection_name}' does not exist in the database")
                raise ValueError(f"Collection '{self.collection_name}' not found. Please ensure the database is properly initialized.")
                
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {e}")
            raise
    
    def get_embedding_for_query(self, query_text: str) -> Optional[List[float]]:
        """
        Generate an embedding vector for the given query text.
        
        Args:
            query_text: The text to generate an embedding for
            
        Returns:
            List of floating point values representing the embedding, or None if generation failed
        """
        if not query_text:
            logger.warning("Empty query text provided")
            return None
            
        try:
            response = self.client.embeddings.create(
                input=[query_text],
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding for query: {e}")
            return None
    
    def query_api_docs(
        self, 
        queries: List[str], 
        n_results: int = 5
    ) -> Dict[str, Any]:
        """
        Query the API documentation for the given list of queries.
        Return a maximum of n_results total across all queries, selecting the ones with highest similarity.
        
        Args:
            queries: List of query strings to search for
            n_results: Maximum number of total results to return across all queries
            
        Returns:
            Dictionary containing the results organized by query
        """
        # Get results for each query
        all_results = []
        query_results = {}
        
        for query in queries:
            query_result = self._execute_single_query(query, n_results)
            query_results[query] = query_result
            
            # Add results to the combined list
            if "results" in query_result and query_result["results"]:
                for result in query_result["results"]:
                    # Add the original query to each result
                    result["original_query"] = query
                    all_results.append(result)
        
        # Sort all results by similarity score (highest first)
        sorted_results = sorted(
            all_results, 
            key=lambda x: x.get("similarity", 0) if x.get("similarity") is not None else 0,
            reverse=True
        )
        
        # Take only the top n_results
        top_results = sorted_results[:n_results]
        
        # Organize results back by query
        final_results = {}
        for query in queries:
            final_results[query] = {
                "query": query,
                "results": []
            }
        
        # Add top results back to their respective queries
        for result in top_results:
            original_query = result.pop("original_query")
            final_results[original_query]["results"].append(result)
        
        return final_results
    
    def _execute_single_query(
        self, 
        query: str, 
        n_results: int = 5
    ) -> Dict[str, Any]:
        """
        Execute a single query against the vector database.
        
        Args:
            query: Query string to search for
            n_results: Number of results to return
            
        Returns:
            Dictionary containing the query results
        """
        # Get embedding for query
        query_embedding = self.get_embedding_for_query(query)
        if not query_embedding:
            return {
                "error": "Failed to generate embedding for query",
                "results": []
            }
        
        try:
            # Execute query against vector database
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"] # type: ignore
            )
            
            # Format results
            formatted_results = []
            if results and len(results["ids"]) > 0:
                for i in range(len(results["ids"][0])):
                    doc = results["documents"][0][i] if "documents" in results and i < len(results["documents"][0]) else None # type: ignore
                    metadata = results["metadatas"][0][i] if "metadatas" in results and i < len(results["metadatas"][0]) else None # type: ignore
                    distance = results["distances"][0][i] if "distances" in results and i < len(results["distances"][0]) else None # type: ignore
                    
                    formatted_results.append({
                        "content": doc,
                        "metadata": metadata,
                        "similarity": 1.0 - (distance / 2) if distance is not None else None  # Convert distance to similarity score
                    })
            
            return {
                "query": query,
                "results": formatted_results
            }
            
        except Exception as e:
            logger.error(f"Error querying vector database: {e}")
            return {
                "query": query,
                "error": str(e),
                "results": []
            }
    
    def format_api_query_results(self, query_results: Dict[str, Any]) -> str:
        """
        Format the query results into a human-readable string.
        
        Args:
            query_results: Dictionary of query results from query_api_docs
            
        Returns:
            Formatted string representation of results
        """
        output_lines = []
        output_lines.append("=" * 80)
        output_lines.append("SAP2000 API DOCUMENTATION SEARCH RESULTS")
        output_lines.append("=" * 80)
        
        for query, result in query_results.items():
            output_lines.append(f"\nQUERY: {query}")
            output_lines.append("-" * 50)
            
            if "error" in result and result["error"]:
                output_lines.append(f"Error: {result['error']}")
                continue
                
            if not result["results"]:
                output_lines.append("No relevant API documentation found for this query.")
                continue
            
            # Add results
            for i, doc in enumerate(result["results"]):
                output_lines.append(f"\nResult {i+1}:")
                
                # Add metadata if available
                if doc["metadata"]:
                    if "source" in doc["metadata"]:
                        output_lines.append(f"Source: {doc['metadata']['source']}")
                    if "category" in doc["metadata"]:
                        output_lines.append(f"Category: {doc['metadata']['category']}")
                    if "function" in doc["metadata"]:
                        output_lines.append(f"Function: {doc['metadata']['function']}")
                
                # Add similarity score
                if doc["similarity"] is not None:
                    output_lines.append(f"Relevance: {doc['similarity']:.2f}")
                    
                # Add content
                if doc["content"]:
                    output_lines.append("\nContent:")
                    output_lines.append("-" * 40)
                    # Format the content with indentation for better readability
                    content_lines = doc["content"].split("\n")
                    for line in content_lines:
                        output_lines.append(f"  {line}")
                
                output_lines.append("-" * 50)
        
        return "\n".join(output_lines) 