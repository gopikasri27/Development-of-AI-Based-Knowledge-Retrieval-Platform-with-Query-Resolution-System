"""
Milestone 2 Flask API Server
----------------------------
Exposes the Multi-Agent Query Resolution & Response Generation pipeline via REST endpoints.
- POST /api/query: Executes the full sequential multi-agent pipeline.
- GET  /api/health: System health and indexed documents metadata.
- POST /api/ingest: Re-indexes or ingests documents into the vector store.
"""

import os
import sys
from flask import Flask, request, jsonify, send_from_directory

# Ensure local imports resolve
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
frontend_dir = os.path.abspath(os.path.join(parent_dir, "..", "milestone-1", "frontend"))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from retrieval.vector_store import VectorStoreManager
from orchestration.agent_orchestrator import MultiAgentOrchestrator

app = Flask(__name__)

# Initialize components
vector_store = VectorStoreManager()
orchestrator = MultiAgentOrchestrator()


def initialize_default_knowledge_base():
    """
    Indexes the two default Milestone 1 domains into the vector store if empty.
    """
    if vector_store.count() == 0:
        kb_dir = os.path.join(parent_dir, "knowledge_base")
        for filename in ["hr_policy.txt", "product_manual.txt"]:
            file_path = os.path.join(kb_dir, filename)
            if os.path.exists(file_path):
                vector_store.index_text_file(file_path, document_name=filename)


# Initial load
initialize_default_knowledge_base()


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


@app.route("/", methods=["GET"])
def serve_index():
    """Serves the Milestone 1 Frontend UI."""
    if os.path.exists(frontend_dir):
        return send_from_directory(frontend_dir, "index.html")
    return jsonify({
        "status": "online",
        "milestone": "Milestone 2",
        "endpoints": ["/api/health", "/api/query", "/api/ingest"]
    }), 200


@app.route("/<path:path>", methods=["GET"])
def serve_static(path):
    """Serves static files (CSS, JS, images) from frontend."""
    if os.path.exists(os.path.join(frontend_dir, path)):
        return send_from_directory(frontend_dir, path)
    return jsonify({"error": "Resource not found"}), 404


@app.route("/api/health", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    """
    Returns API health status and indexed document summary.
    """
    indexed_docs = vector_store.get_indexed_documents()
    total_chunks = vector_store.count()
    return jsonify({
        "status": "healthy",
        "milestone": "Milestone 2",
        "vector_store": "ChromaDB HNSW",
        "total_chunks_indexed": total_chunks,
        "total_chunks": total_chunks,
        "gemini_api_configured": bool(os.environ.get("GEMINI_API_KEY")),
        "indexed_documents": indexed_docs
    }), 200


@app.route("/documents", methods=["GET"])
def get_documents():
    """Returns list of indexed documents."""
    return jsonify({"documents": vector_store.get_indexed_documents()}), 200


@app.route("/api/query", methods=["POST", "OPTIONS"])
@app.route("/query", methods=["POST", "OPTIONS"])
def handle_query():
    """
    Multi-Agent query resolution endpoint.
    
    Request:
        { "query": "user question" }
        
    Response:
        {
            "query": str,
            "query_type": str,
            "classification_confidence": float,
            "answer": str,
            "response": str,
            "sources": [...],
            "citations": [...],
            "confidence": { "score": float, "label": str },
            "is_clarification": bool
        }
    """
    if request.method == "OPTIONS":
        return jsonify({}), 200

    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()

    if not query:
        return jsonify({
            "error": "Query string is required.",
            "query": "",
            "query_type": "ambiguous",
            "classification_confidence": 0.0,
            "answer": "Please provide a valid query.",
            "response": "Please provide a valid query.",
            "sources": [],
            "citations": [],
            "confidence": {
                "score": 0.0,
                "label": "Low"
            },
            "is_clarification": True
        }), 400

    result = orchestrator.process_query(query)
    
    # Enrich for frontend compatibility
    answer_text = result.get("answer", "")
    result["response"] = answer_text
    
    citations = []
    for s in result.get("sources", []):
        citations.append({
            "source_file": s.get("document_name", "unknown"),
            "document_name": s.get("document_name", "unknown"),
            "page": s.get("page", 1),
            "chunk_id": s.get("chunk_id", ""),
            "similarity_score": s.get("relevance_score", 0.0),
            "relevance_score": s.get("relevance_score", 0.0),
            "excerpt": s.get("content", ""),
            "content": s.get("content", "")
        })
    result["citations"] = citations
    
    conf_score = result.get("confidence", {}).get("score", 0.0)
    result["is_clarification"] = (result.get("query_type") == "ambiguous" or conf_score < 0.50)
    
    return jsonify(result), 200


@app.route("/upload", methods=["POST"])
@app.route("/api/upload", methods=["POST"])
def handle_upload():
    """
    Accepts file uploads (PDF, DOCX, TXT, CSV, MD), extracts text, chunks,
    and indexes into the ChromaDB vector store for instant querying.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded in request."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "Empty filename provided."}), 400

    filename = file.filename
    upload_dir = os.path.join(parent_dir, "knowledge_base", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(upload_dir, filename)
    file.save(save_path)

    # Extract text based on file format
    content = ""
    ext = os.path.splitext(filename)[1].lower()

    try:
        if ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(save_path)
                content = "\n\n".join([page.extract_text() or "" for page in reader.pages])
            except Exception:
                with open(save_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
        elif ext == ".docx":
            try:
                import zipfile
                import xml.etree.ElementTree as ET
                with zipfile.ZipFile(save_path) as z:
                    xml_content = z.read("word/document.xml")
                    tree = ET.fromstring(xml_content)
                    paragraphs = []
                    for p in tree.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
                        texts = [node.text for node in p.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t") if node.text]
                        if texts:
                            paragraphs.append("".join(texts))
                    content = "\n\n".join(paragraphs)
            except Exception:
                with open(save_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
        else:
            # Default text extraction for .txt, .md, .csv, .json, .log, etc.
            with open(save_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
    except Exception as e:
        return jsonify({"error": f"Failed to extract text from file: {str(e)}"}), 500

    if not content.strip():
        return jsonify({"error": f"The uploaded file '{filename}' contains no readable text."}), 400

    from retrieval.chunking import chunk_document
    chunks = chunk_document(text=content, filename=filename)
    chunks_count = vector_store.index_chunks(chunks)

    return jsonify({
        "message": f"Successfully indexed '{filename}' into vector store!",
        "filename": filename,
        "chunks_indexed": chunks_count,
        "total_chunks": vector_store.count(),
        "file_size": os.path.getsize(save_path),
        "file_type": ext
    }), 200


@app.route("/api/ingest", methods=["POST"])
def handle_ingest():
    """
    Re-indexes or ingests a file from knowledge_base.
    """
    data = request.get_json(silent=True) or {}
    filename = data.get("filename")
    kb_dir = os.path.join(parent_dir, "knowledge_base")

    if filename:
        file_path = os.path.join(kb_dir, filename)
        if not os.path.exists(file_path):
            return jsonify({"error": f"File {filename} not found in knowledge_base"}), 404
        chunks_added = vector_store.index_text_file(file_path, document_name=filename)
        return jsonify({
            "message": f"Successfully indexed {filename}",
            "chunks_added": chunks_added,
            "total_chunks": vector_store.count()
        }), 200
    else:
        # Re-index all default documents
        vector_store.reset()
        initialize_default_knowledge_base()
        return jsonify({
            "message": "Knowledge base reset and re-indexed successfully",
            "total_chunks": vector_store.count()
        }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
