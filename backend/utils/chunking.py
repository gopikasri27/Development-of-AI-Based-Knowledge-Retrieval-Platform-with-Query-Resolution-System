"""
Chunking Utility Module
----------------------
Splits document text into manageable chunks with configured overlap using
LangChain's RecursiveCharacterTextSplitter, attaching full metadata.
"""

import time
from typing import List, Dict, Any, Optional

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        # Graceful fallback custom implementation if langchain is not present
        class RecursiveCharacterTextSplitter:  # type: ignore
            def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50, separators: Optional[List[str]] = None, length_function=len):
                self.chunk_size = chunk_size
                self.chunk_overlap = chunk_overlap
                self.separators = separators or ["\n\n", "\n", " ", ""]
                self.length_function = length_function

            def split_text(self, text: str) -> List[str]:
                if not text:
                    return []
                chunks = []
                start = 0
                while start < len(text):
                    end = min(start + self.chunk_size, len(text))
                    if end < len(text):
                        last_break = text.rfind(" ", start, end)
                        if last_break != -1 and last_break > start + (self.chunk_size // 2):
                            end = last_break
                    chunks.append(text[start:end].strip())
                    start = end - self.chunk_overlap if end < len(text) else len(text)
                return [c for c in chunks if c]


def chunk_document(
    text: str,
    filename: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    additional_metadata: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Chunks extracted document text using RecursiveCharacterTextSplitter with overlap.
    
    Args:
        text (str): Cleaned document text.
        filename (str): Source document filename.
        chunk_size (int): Size of each chunk (characters/tokens). Default 500.
        chunk_overlap (int): Overlap between consecutive chunks. Default 50.
        additional_metadata (Optional[dict]): Extra metadata to attach to every chunk.
        
    Returns:
        List[Dict[str, Any]]: List of chunk dicts with 'id', 'text', and 'metadata'.
    """
    if not text or not text.strip():
        return []
        
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
        length_function=len
    )
    
    raw_chunks = splitter.split_text(text)
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    chunks = []
    for idx, chunk_content in enumerate(raw_chunks):
        if not chunk_content.strip():
            continue
            
        chunk_id = f"{filename}_chunk_{idx}"
        meta = {
            "chunk_id": chunk_id,
            "source": filename,
            "chunk_index": idx,
            "total_chunks": len(raw_chunks),
            "char_count": len(chunk_content),
            "timestamp": timestamp,
        }
        if additional_metadata:
            meta.update(additional_metadata)
            
        chunks.append({
            "id": chunk_id,
            "text": chunk_content,
            "metadata": meta
        })
        
    return chunks
