"""
Text Extraction and Normalization Utility Module
------------------------------------------------
Extracts and normalizes text from PDF, DOCX, TXT, and CSV files.
Applies Unicode normalization (NFKC), collapses whitespace, and strips control characters.
"""

import os
import re
import unicodedata
from typing import Dict, Any, Optional
import pandas as pd

# Optional / safe imports for document parsing
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    import docx
except ImportError:
    docx = None


def clean_text(text: Optional[str]) -> str:
    """
    Cleans and normalizes raw text.
    - Normalizes unicode characters (NFKC)
    - Strips non-printable characters while preserving standard whitespace
    - Normalizes line breaks and collapses multiple spaces/tabs
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Unicode normalization
    text = unicodedata.normalize("NFKC", text)
    
    # Replace carriage returns and vertical tabs
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # Remove control characters except tab and newline
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or unicodedata.category(ch)[0] != "C")
    
    # Replace multiple spaces with a single space
    text = re.sub(r"[ \t]+", " ", text)
    
    # Replace 3 or more newlines with double newline
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    return text.strip()


def extract_from_txt(file_path: str) -> str:
    """Extracts and normalizes text from a plain text file."""
    encodings = ["utf-8", "latin-1", "utf-16", "cp1252"]
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                content = f.read()
                return clean_text(content)
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    
    # Fallback to binary read with ignore
    with open(file_path, "rb") as f:
        return clean_text(f.read().decode("utf-8", errors="ignore"))


def extract_from_pdf(file_path: str) -> str:
    """Extracts text from PDF file using pypdf."""
    if PdfReader is None:
        raise ImportError("pypdf is not installed. Please install pypdf to process PDF files.")
    
    reader = PdfReader(file_path)
    extracted_pages = []
    
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        if page_text.strip():
            extracted_pages.append(f"--- [Page {i + 1}] ---\n" + page_text.strip())
            
    full_text = "\n\n".join(extracted_pages)
    return clean_text(full_text)


def extract_from_docx(file_path: str) -> str:
    """Extracts text from DOCX file using python-docx."""
    if docx is None:
        raise ImportError("python-docx is not installed. Please install python-docx to process DOCX files.")
    
    doc = docx.Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    
    # Also extract text from tables
    for table in doc.tables:
        for row in table.rows:
            row_text = " | ".join([cell.text.strip() for cell in row.cells if cell.text.strip()])
            if row_text:
                paragraphs.append(row_text)
                
    full_text = "\n\n".join(paragraphs)
    return clean_text(full_text)


def extract_from_csv(file_path: str) -> str:
    """Extracts text from CSV file using pandas."""
    try:
        df = pd.read_csv(file_path)
    except Exception:
        df = pd.read_csv(file_path, encoding="latin-1")
        
    lines = []
    # Include headers summary
    columns = [str(c) for c in df.columns]
    lines.append("CSV Columns: " + ", ".join(columns))
    
    # Convert rows to descriptive textual statements
    for idx, row in df.iterrows():
        row_items = [f"{col}: {row[col]}" for col in df.columns if pd.notna(row[col])]
        if row_items:
            lines.append(f"Row {idx + 1}: " + " | ".join(row_items))
            
    full_text = "\n".join(lines)
    return clean_text(full_text)


def extract_text(file_path: str) -> Dict[str, Any]:
    """
    Dispatcher function to extract text based on file extension.
    Supports .pdf, .docx, .txt, .csv.
    Returns dictionary with extracted text, file metadata, and status.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    filename = os.path.basename(file_path)
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    
    if ext == ".txt":
        raw_text = extract_from_txt(file_path)
    elif ext == ".pdf":
        raw_text = extract_from_pdf(file_path)
    elif ext in [".docx", ".doc"]:
        raw_text = extract_from_docx(file_path)
    elif ext == ".csv":
        raw_text = extract_from_csv(file_path)
    else:
        # Fallback to text reader for other plain files like .md, .json, .log
        raw_text = extract_from_txt(file_path)
        
    cleaned = clean_text(raw_text)
    
    return {
        "filename": filename,
        "extension": ext,
        "size_bytes": os.path.getsize(file_path),
        "char_count": len(cleaned),
        "text": cleaned
    }
