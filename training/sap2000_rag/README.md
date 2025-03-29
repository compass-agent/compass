# SAP2000 API Documentation RAG System

A Retrieval-Augmented Generation (RAG) system for SAP2000 API documentation. This system extracts API documentation from PDF files, processes it directly into meaningful chunks, creates vector embeddings, and stores them in a database for quick semantic search and code generation.

## Overview

This system allows you to:
1. Process SAP2000 API documentation from PDF files directly into searchable chunks
2. Generate vector embeddings for semantic search
3. Store the embeddings in a ChromaDB vector database

## Setup

### Prerequisites

- Python 3.8+
- SAP2000 API Documentation PDF files

### Installation

1. Clone the repository or download the source code

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   venv\Scripts\activate  # On Windows
   source venv/bin/activate  # On macOS/Linux
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your OpenAI API key as an environment variable:
   ```
   # On Windows
   set OPENAI_API_KEY=your_api_key_here
   
   # On macOS/Linux
   export OPENAI_API_KEY=your_api_key_here
   ```

## Usage

### Building the RAG System

Place your SAP2000 API Documentation PDF files in the `data/CSI_API_Functions` directory, then run:

```
python main.py
```

This will:
1. Extract and process text from PDF files directly into function-level chunks
2. Generate embeddings for each chunk
3. Store the embeddings in a ChromaDB vector database

The process will create the following directories:
- `output/chunks`: Processed documentation chunks
- `output/embeddings`: Vector embeddings
- `output/vector_db`: ChromaDB vector database

### Processing Pipeline Improvements

The system has been optimized to directly process PDF files into function-level chunks, eliminating the intermediate step of creating markdown files. This improves efficiency and reduces disk usage.

The PDF parser now:
- Extracts content from PDF files
- Identifies individual API function documentation
- Creates structured chunks with metadata
- Saves the chunks directly to JSON format

### Query Functionality (Currently Disabled)

The query functionality is currently commented out in the main script. To enable it, uncomment the query section in the `main()` function of `main.py`. This would allow you to query the system and generate code based on the documentation.

## Customization

You can modify the configuration in the `src/config.py` file to change:
- Input/output directories
- Embedding model
- Collection name

## Troubleshooting

- **Missing PDF files**: Ensure your PDF files are in the correct directory and that the directory exists
- **API Key Issues**: Verify your OpenAI API key is set correctly
- **Memory Errors**: For large documentation sets, consider processing in smaller batches 