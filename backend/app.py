"""
Flask API Server for AI Knowledge Retrieval Platform
----------------------------------------------------
Provides REST endpoints for:
- Document Ingestion (POST /upload)
- Multi-Agent Query Resolution (POST /query)
- Health and Metrics (GET /health)
- Document Catalog (GET /documents)
- Chat History (GET /history/<session_id>)
- Static Frontend Serving
"""

import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Ensure local backend directories are in python path
import sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.extract_text import extract_text
from utils.chunking import chunk_document
from utils.embeddings import (
    index_chunks,
    get_all_indexed_documents,
    get_or_create_collection,
    reset_collection
)
from utils.db import (
    save_document_record,
    get_all_documents,
    get_recent_history
)
from agents.orchestrator import MultiAgentRAGOrchestrator

load_dotenv()

# Directories
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Initialize Flask app
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)

# Initialize Multi-Agent Orchestrator
orchestrator = MultiAgentRAGOrchestrator()


@app.route("/")
def index():
    """Serves the frontend single-page application."""
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:path>")
def static_files(path):
    """Serves static frontend assets (css, js, assets)."""
    return send_from_directory(FRONTEND_DIR, path)


@app.route("/health", methods=["GET"])
def health():
    """
    Health check and system status endpoint.
    Returns status of ChromaDB, document count, and active configuration.
    """
    try:
        collection = get_or_create_collection()
        total_chunks = collection.count()
        documents = get_all_documents()
        has_gemini = bool(os.getenv("GEMINI_API_KEY", "").strip())

        return jsonify({
            "status": "healthy",
            "service": "AI Knowledge Retrieval Platform (Milestone 1)",
            "vector_store": "ChromaDB (Persistent)",
            "embedding_model": "all-MiniLM-L6-v2",
            "gemini_api_configured": has_gemini,
            "total_chunks_indexed": total_chunks,
            "total_documents": len(documents)
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/upload", methods=["POST"])
def upload_document():
    """
    Knowledge Base Ingestion Endpoint.
    Accepts PDF, DOCX, TXT, CSV files.
    Extracts text, cleans it, splits into chunks with overlap,
    generates embeddings, and stores in ChromaDB & SQLite.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided in request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename provided"}), 400

    allowed_extensions = {".pdf", ".docx", ".doc", ".txt", ".csv"}
    _, ext = os.path.splitext(file.filename)
    if ext.lower() not in allowed_extensions:
        return jsonify({
            "error": f"Unsupported file type '{ext}'. Allowed: .pdf, .docx, .txt, .csv"
        }), 400

    try:
        # Save file to uploads folder
        filename = file.filename
        file_path = os.path.join(UPLOADS_DIR, filename)
        file.save(file_path)
        file_size = os.path.getsize(file_path)

        # 1. Extract and clean text
        extracted_info = extract_text(file_path)
        cleaned_text = extracted_info["text"]

        if not cleaned_text:
            return jsonify({"error": "Could not extract any meaningful text from the file"}), 400

        # 2. Chunk text (chunk_size=500, overlap=50)
        chunks = chunk_document(
            text=cleaned_text,
            filename=filename,
            chunk_size=500,
            chunk_overlap=50,
            additional_metadata={"file_type": ext.lower(), "file_size": file_size}
        )

        # 3. Generate embeddings & index into ChromaDB
        indexed_count = index_chunks(chunks)

        # 4. Save document record in SQLite metadata DB
        save_document_record(
            filename=filename,
            file_path=file_path,
            file_type=ext.lower(),
            file_size=file_size,
            chunks_count=indexed_count
        )

        return jsonify({
            "message": f"Successfully processed and indexed '{filename}'",
            "filename": filename,
            "file_type": ext.lower(),
            "file_size_bytes": file_size,
            "char_count": len(cleaned_text),
            "chunks_indexed": indexed_count
        }), 200

    except Exception as e:
        return jsonify({"error": f"Failed to ingest document: {str(e)}"}), 500


@app.route("/query", methods=["POST"])
def process_query():
    """
    Multi-Agent RAG Query Resolution Endpoint.
    Accepts: { "query": "user question", "session_id": "optional-id" }
    Runs orchestrator sequence:
    Memory -> Query Agent -> Retrieval Agent -> Clarification Agent -> Response Agent -> Memory
    """
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    session_id = data.get("session_id", "").strip() or str(uuid.uuid4())[:8]

    if not query:
        return jsonify({"error": "Query string is required"}), 400

    try:
        result = orchestrator.run(query=query, session_id=session_id)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": f"Query processing failed: {str(e)}"}), 500


@app.route("/documents", methods=["GET"])
def list_documents():
    """Returns list of all indexed documents in the knowledge base."""
    try:
        docs = get_all_documents()
        return jsonify({"documents": docs, "total": len(docs)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/history/<session_id>", methods=["GET"])
def get_session_history(session_id):
    """Returns conversation history for a specific session."""
    try:
        history = get_recent_history(session_id, limit=20)
        return jsonify({"session_id": session_id, "history": history}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/reset", methods=["POST"])
def reset_knowledge_base():
    """Clears all indexed vectors in ChromaDB."""
    try:
        reset_collection()
        return jsonify({"message": "Knowledge base reset successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"Starting Multi-Agent RAG Platform API on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=True)
