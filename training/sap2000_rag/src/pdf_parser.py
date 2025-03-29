"""
Simplified PDF Parser

Extracts SAP2000 API documentation from PDFs and segments into individual API chunks.
"""

import os
import logging
import re
import json
import glob
import PyPDF2
from pathlib import Path

logger = logging.getLogger(__name__)

class PDFParser:
    """Simple parser to extract and segment SAP2000 API documentation"""
    
    def __init__(self, pdf_dir):
        """Initialize with directory containing PDF files"""
        self.pdf_dir = os.path.abspath(pdf_dir)
    
    def extract_and_process(self, chunks_file=None):
        """
        Extract all API docs from PDFs and save as chunks
        
        Args:
            chunks_file: Optional path to save JSON chunks
            
        Returns:
            List of chunks, each representing one API documentation
        """
        # Create output directory if needed
        if chunks_file:
            os.makedirs(os.path.dirname(chunks_file), exist_ok=True)
        
        # Find PDF files
        pdf_files = glob.glob(os.path.join(self.pdf_dir, "*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {self.pdf_dir}")
            return []
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        all_chunks = []
        
        # Process each PDF
        for pdf_file in pdf_files:
            try:
                module_name = Path(os.path.basename(pdf_file)).stem
                logger.info(f"Processing {module_name}.pdf")
                
                # Extract raw content
                raw_content = self._extract_raw_text(pdf_file)
                
                # Segment into API docs
                api_docs = self._segment_into_api_docs(raw_content, module_name)
                logger.info(f"Found {len(api_docs)} API docs in {module_name}.pdf")
                
                # Create chunks
                for api_id, content in api_docs.items():
                    # Extract the full syntax to use as API name
                    syntax = self._extract_syntax(content)
                    
                    # Use syntax as the function name if available, otherwise use the API ID
                    function_name = syntax if syntax else api_id
                    
                    chunk = {
                        'content': content,
                        'metadata': {
                            'function_name': function_name,
                            'syntax': syntax,
                            'module': module_name,
                            'source': f"{module_name}.pdf"
                        }
                    }
                    all_chunks.append(chunk)
            
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {e}")
                logger.exception(e)
        
        # Save to file if specified
        if chunks_file and all_chunks:
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump(all_chunks, f, indent=2)
            logger.info(f"Saved {len(all_chunks)} chunks to {chunks_file}")
        
        return all_chunks
    
    def _extract_raw_text(self, pdf_file):
        """Extract raw text from PDF file with minimal processing"""
        try:
            clean_pages = []
            with open(pdf_file, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    # Extract text from this page
                    page_text = page.extract_text()
                    if not page_text:
                        continue
                    
                    # Remove page number and file metadata that appears at the end of pages
                    page_text = re.sub(r'Page \d+ of \d+.*?$', '', page_text, flags=re.MULTILINE)
                    page_text = re.sub(r'\d{1,2}/\d{1,2}/\d{4}.*?file:///.*?\.htm$', '', page_text, flags=re.MULTILINE)
                    
                    # Add the cleaned page text if not empty
                    clean_page = page_text.strip()
                    if clean_page:
                        clean_pages.append(clean_page)
            
            # Join all cleaned pages with newlines
            content = '\n '.join(clean_pages)
            
            return content
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_file}: {e}")
            raise
    
    def _segment_into_api_docs(self, content, module_name):
        """
        Segment content into separate API documentations.
        
        Uses keyword markers to identify the start of new API sections.
        """
        api_docs = {}
        
        try:
            # Updated pattern to match any content on the line above "Syntax"
            # Much more relaxed to capture API names with special characters
            api_pattern = r'(?:\n|\A)\s*([^\n]+?)\s*\n+\s*Syntax\s*\n'
            
            # Find all API starts
            matches = list(re.finditer(api_pattern, content, re.DOTALL))
            
            # Extract the start positions and API names, with no duplicates
            api_starts = []
            seen_positions = set()
            
            for match in matches:
                # Get the position of the API name (not the Syntax line)
                # We need to calculate this since it may have leading spaces now
                full_start = match.start(1)
                line_start = content.rfind('\n', 0, full_start)
                if line_start == -1:  # if it's at the beginning of the content
                    line_start = 0 
                else:
                    line_start += 1  # move past the newline character
                
                # Only add if we haven't seen this position
                if line_start not in seen_positions:
                    # We'll extract the proper syntax later, but need API name for validation
                    api_name = match.group(1).strip()
                    
                    # Skip if empty or too short
                    if len(api_name) < 2:
                        continue
                        
                    api_starts.append((line_start, api_name))
                    seen_positions.add(line_start)
            
            # Sort by position in document
            api_starts.sort(key=lambda x: x[0])
            
            if not api_starts:
                logger.warning(f"No API docs found in {module_name}")
                api_docs[f"{module_name}_full"] = content
                return api_docs
            
            logger.info(f"Found {len(api_starts)} API docs in {module_name}")
            
            # Process each API section
            for i, (start_pos, api_name) in enumerate(api_starts):
                # Define end position (start of next API or end of document)
                end_pos = api_starts[i+1][0] if i < len(api_starts) - 1 else len(content)
                
                # Extract the complete API content
                api_content = content[start_pos:end_pos].strip()
                
                # Make sure content is substantial and contains expected sections
                if len(api_content) > 100 and "VB6 Procedure" in api_content:
                    # Extract the full syntax to use as the unique key
                    syntax = self._extract_syntax(api_content)
                    
                    # Use the full syntax as the key if available, otherwise use API name with module
                    key = syntax if syntax else f"{module_name}_{api_name}"
                    
                    api_docs[key] = api_content
                    # Debug for first few APIs
                    if i < 3:
                        logger.debug(f"API: {key}, Content length: {len(api_content)}, First 50 chars: {api_content[:50]}")
            
            if not api_docs:
                logger.warning(f"No valid API docs found in {module_name}")
                api_docs[f"{module_name}_full"] = content
            
            return api_docs
            
        except Exception as e:
            logger.error(f"Error segmenting content for {module_name}: {e}")
            logger.exception(e)
            return {f"{module_name}_error": content}
    
    def _extract_syntax(self, content):
        """
        Extract the full syntax line from API content.
        
        Looks for text between "Syntax" and the next section.
        """
        try:
            # Look for content that appears after "Syntax" and before "VB6 Procedure"
            syntax_pattern = r'Syntax\s*\n+\s*([^\n]+)'
            syntax_match = re.search(syntax_pattern, content)
            
            if syntax_match:
                return syntax_match.group(1).strip()
            
            # If not found with the above pattern, try alternative patterns
            alt_patterns = [
                r'(Helper\.[A-Za-z0-9_]+)',
                r'(SapObject\.(?:SapModel\.)?[A-Za-z0-9_.]+)'
            ]
            
            for pattern in alt_patterns:
                match = re.search(pattern, content)
                if match:
                    return match.group(1).strip()
            
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting syntax: {e}")
            return ""
    
    def load_chunks(self, chunks_file):
        """Load previously processed chunks from file"""
        if not os.path.exists(chunks_file):
            logger.warning(f"Chunks file not found: {chunks_file}")
            return []
        
        try:
            with open(chunks_file, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            logger.info(f"Loaded {len(chunks)} chunks from {chunks_file}")
            return chunks
        except Exception as e:
            logger.error(f"Error loading chunks: {e}")
            return [] 