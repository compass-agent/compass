"""
Configuration Module

Manages configuration values and API keys for the SAP2000 RAG system.
"""

import os

# Get the absolute path to the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# OpenAI API Configuration
# Default to environment variable, can be overridden
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Default paths using absolute paths
DEFAULT_PDF_DIR = os.path.join(PROJECT_ROOT, 'data', 'CSI_API_Functions')
DEFAULT_OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
DEFAULT_CHUNKS_DIR = os.path.join(DEFAULT_OUTPUT_DIR, 'chunks')
DEFAULT_EMBEDDINGS_DIR = os.path.join(DEFAULT_OUTPUT_DIR, 'embeddings')
DEFAULT_DB_DIR = os.path.join(PROJECT_ROOT, '..', '..', 'backend', 'src', 'compass', 'database', 'sap2000_api')

# Collection name for vector database
DEFAULT_COLLECTION_NAME = 'sap2000_api'

# Model names
DEFAULT_EMBEDDING_MODEL = 'text-embedding-3-small'
DEFAULT_LLM_MODEL = 'gpt-4'

def get_config():
    """Return default configuration values with absolute paths"""
    return {
        'pdf_dir': DEFAULT_PDF_DIR,
        'output_dir': DEFAULT_OUTPUT_DIR,
        'chunks_dir': DEFAULT_CHUNKS_DIR,
        'embeddings_dir': DEFAULT_EMBEDDINGS_DIR,
        'db_dir': DEFAULT_DB_DIR,
        'collection_name': DEFAULT_COLLECTION_NAME,
        'embedding_model': DEFAULT_EMBEDDING_MODEL,
        'llm_model': DEFAULT_LLM_MODEL,
        'api_key': OPENAI_API_KEY
    } 