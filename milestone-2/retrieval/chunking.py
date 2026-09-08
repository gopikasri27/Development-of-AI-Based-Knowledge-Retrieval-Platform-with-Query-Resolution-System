"""
Chunking Utility Module for Milestone 2
---------------------------------------
Splits document text into manageable chunks with configured overlap using
LangChain's RecursiveCharacterTextSplitter (with robust fallback), preserving
document sections, page numbers, and full metadata.
"""

import re
import time
from typing import List, Dict, Any, Optional

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        class RecursiveCharacterTextSplitter:  # type: ignore
            def __init__(
                self,
                chunk_size: int = 500,
                chunk_overlap: int = 50,
                separators: Optional[List[str]] = None,
                length_function=len
            ):
                self.chunk_size = chunk_size
                self.chunk_overlap = chunk_overlap
                self.separators = separators or ["\n\n", "\n", ". ", " ", ""]
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


def extract_sections_and_chunk(
    text: str,
    filename: str,
    page: int = 1,
    chunk_size: int = 500,
    chunk_overlap: int = 50
) -> List[Dict[str, Any]]:
    """
    Parses sections from markdown/text and splits into chunk dicts with section metadata.
    """
    if not text or not text.strip():
        return []

    lines = text.splitlines()
    sections: List[Dict[str, Any]] = []
    current_section_title = "General Overview"
    current_section_lines: List[str] = []

    for line in lines:
        match = re.match(r"^(?:#{1,3})\s+(.+)$", line.strip())
        if match:
            if current_section_lines:
                sec_text = "\n".join(current_section_lines).strip()
                if sec_text:
                    sections.append({
                        "section": current_section_title,
                        "text": sec_text
                    })
                current_section_lines = []
            current_section_title = match.group(1).strip()
        else:
            current_section_lines.append(line)

    if current_section_lines:
        sec_text = "\n".join(current_section_lines).strip()
        if sec_text:
            sections.append({
                "section": current_section_title,
                "text": sec_text
            })

    if not sections:
        sections = [{"section": "General Overview", "text": text.strip()}]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
        length_function=len
    )
    chunks: List[Dict[str, Any]] = []
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    global_index = 0

    for sec in sections:
        sec_title = sec["section"]
        sec_text = sec["text"]
        raw_chunks = splitter.split_text(sec_text)

        for chunk_text in raw_chunks:
            if not chunk_text.strip():
                continue

            chunk_id = f"{filename}_chunk_{global_index}"
            meta = {
                "chunk_id": chunk_id,
                "document_name": filename,
                "source": filename,
                "page": page,
                "section": sec_title,
                "chunk_index": global_index,
                "char_count": len(chunk_text),
                "timestamp": timestamp
            }
            # Prefix section heading to chunk text for strong semantic alignment
            enriched_content = f"[{sec_title}]\n{chunk_text}" if not chunk_text.startswith("[") else chunk_text
            chunks.append({
                "id": chunk_id,
                "text": enriched_content,
                "metadata": meta
            })
            global_index += 1

    for c in chunks:
        c["metadata"]["total_chunks"] = len(chunks)

    return chunks


def chunk_document(
    text: str,
    filename: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    page: int = 1,
    additional_metadata: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Standard chunking wrapper for text content.
    """
    chunks = extract_sections_and_chunk(
        text=text,
        filename=filename,
        page=page,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    if additional_metadata:
        for c in chunks:
            c["metadata"].update(additional_metadata)
    return chunks
