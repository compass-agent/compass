"""
SAP2000 API Documentation RAG System

This script processes SAP2000 API documentation from PDF files,
creates embeddings, and stores them in a vector database for
retrieval-augmented generation of SAP2000 code.

Usage:
    python main.py    # Build the RAG system
"""

import os
import logging
import sys
from src.pdf_parser import PDFParser
from src.embedding_manager import EmbeddingManager
from src.vector_store import VectorStore
from src.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('sap2000_rag.log')
    ]
)
logger = logging.getLogger(__name__)

def build_rag_system(config):
    """Build the complete RAG system from PDF files"""
    logger.info("Building SAP2000 API Documentation RAG system...")
    
    # Create necessary directories
    os.makedirs(config['chunks_dir'], exist_ok=True)
    os.makedirs(config['embeddings_dir'], exist_ok=True)
    
    # Verify PDF directory exists
    if not os.path.exists(config['pdf_dir']):
        logger.error(f"PDF directory does not exist: {config['pdf_dir']}")
        logger.error("Please ensure the PDF directory exists and contains SAP2000 API documentation PDFs.")
        return
    
    # Define output files
    chunks_file = os.path.join(config['chunks_dir'], 'api_chunks.json')
    embeddings_file = os.path.join(config['embeddings_dir'], 'api_embeddings.json')
    
    # Step 1+2: Extract content from PDF files and process into chunks
    chunks = []
    if not os.path.exists(chunks_file) or not os.path.getsize(chunks_file) > 0:
        logger.info("Step 1: Extracting and processing PDF files directly into chunks")
        parser = PDFParser(config['pdf_dir'])
        chunks = parser.extract_and_process(chunks_file)
        logger.info(f"Extraction and processing complete. {len(chunks)} chunks created and saved to {chunks_file}")
    else:
        logger.info(f"Step 1: Skipping extraction and processing - chunks already exist at {chunks_file}")
        parser = PDFParser(config['pdf_dir'])
        chunks = parser.load_chunks(chunks_file)
    
    # Step 2: Generate embeddings
    embedded_chunks = []
    if not os.path.exists(embeddings_file) or not os.path.getsize(embeddings_file) > 0:
        logger.info("Step 2: Generating embeddings")
        embedding_manager = EmbeddingManager()
        embedded_chunks = embedding_manager.generate_embeddings(chunks, output_file=embeddings_file)
        logger.info(f"Embeddings created and saved to {embeddings_file}")
    else:
        logger.info(f"Step 2: Skipping embedding generation - embeddings already exist at {embeddings_file}")
        embedding_manager = EmbeddingManager()
        embedded_chunks = embedding_manager.load_embeddings(embeddings_file)
    
    # Step 3: Store in vector database
    vector_store = VectorStore(config['db_dir'])
    if not vector_store.collection_exists(config['collection_name']):
        logger.info("Step 3: Storing in vector database")
        vector_store.add_documents(config['collection_name'], embedded_chunks)
        logger.info(f"Documents stored in vector database at {config['db_dir']}")
    else:
        logger.info(f"Step 3: Skipping vector storage - collection '{config['collection_name']}' already exists in {config['db_dir']}")
    
    logger.info("RAG system build complete!")
    logger.info(f"- PDF directory: {config['pdf_dir']}")
    logger.info(f"- Processed chunks: {chunks_file}")
    logger.info(f"- Generated embeddings: {embeddings_file}")
    logger.info(f"- Vector database: {config['db_dir']}")

def query_rag_system(config, query):
    """Query the RAG system and generate code"""
    logger.info(f"Querying SAP2000 RAG system: '{query}'")
    
    # Initialize components
    embedding_manager = EmbeddingManager()
    vector_store = VectorStore(config['db_dir'])
    
    # Generate embedding for query
    query_embedding = embedding_manager.get_embedding_for_query(query)
    if not query_embedding:
        logger.error("Failed to generate embedding for query")
        return "Error: Could not generate embedding for query."
    
    # Query vector store
    results = vector_store.query(config['collection_name'], query_embedding, n_results=5)
    if not results or 'documents' not in results or not results['documents']:
        logger.warning("No relevant API documentation found for query")
        return "Error: No relevant API documentation found for this query."
    
    # Extract documents and metadata safely
    documents = results['documents'][0] if 'documents' in results else []
    metadatas = results.get('metadatas', [])
    metadata_list = metadatas[0] if metadatas and len(metadatas) > 0 else []
    
    # print the documents and metadata
    for doc, metadata in zip(documents, metadata_list):
        #print(f"Document: {doc}")
        print(f"Metadata: {metadata}")
        print("-" * 50)

def main():
    """Main entry point"""
    # Get configuration
    config = get_config()
    if False:
        # Build the RAG system
        build_rag_system(config)
    else:
        sample_query = "How I set a dead load on a SAP2000 model?"
        print(f"\nRunning sample query: '{sample_query}'")
        query_rag_system(config, sample_query)
        

if __name__ == "__main__":
    main() 