"""
Milestone 3 Flask API Server
----------------------------
Exposes the complete Milestone 3 Multi-Agent Query Resolution System via REST endpoints:
- POST /api/query: Sequential multi-agent pipeline with Memory, Query Understanding, Clarification, Retrieval, Generation, and Transparency.
- POST /api/clarify: Resolves active clarification prompts with user input and returns refined response.
- GET/DELETE /api/memory/<session_id>: Session interaction context management.
- GET /api/health: System health and indexed documents metadata.
- POST /api/upload & /api/ingest: Document vector ingestion.
"""

import os
import sys
from flask import Flask, request, jsonify, send_from_directory

# Ensure path resolution for milestone-3 and milestone-2
current_dir = os.path.dirname(os.path.abspath(__file__))
m3_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(m3_dir)
m2_dir = os.path.join(root_dir, "milestone-2")
frontend_dir = os.path.join(m3_dir, "frontend")

for p in [m2_dir, m3_dir, root_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

import agents
if hasattr(agents, "__path__"):
    for dir_path in [os.path.join(m2_dir, "agents"), os.path.join(m3_dir, "agents")]:
        if dir_path not in agents.__path__:
            agents.__path__.append(dir_path)

from retrieval.vector_store import VectorStoreManager

import importlib.util
orch_path = os.path.join(m3_dir, "orchestration", "milestone3_orchestrator.py")
spec = importlib.util.spec_from_file_location("milestone3_orchestrator", orch_path)
orch_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orch_mod)
Milestone3Orchestrator = orch_mod.Milestone3Orchestrator

app = Flask(__name__)

# Initialize components
vector_store = VectorStoreManager()
orchestrator = Milestone3Orchestrator()


def initialize_default_knowledge_base():
    """Indexes default Milestone 1 & 2 knowledge documents if vector store is empty."""
    if vector_store.count() == 0:
        kb_dir = os.path.join(m2_dir, "knowledge_base")
        if os.path.exists(kb_dir):
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
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,DELETE,OPTIONS"
    return response


@app.route("/", methods=["GET"])
def serve_index():
    """Serves the Milestone 3 Frontend UI."""
    if os.path.exists(os.path.join(frontend_dir, "index.html")):
        return send_from_directory(frontend_dir, "index.html")
    return jsonify({
        "status": "online",
        "milestone": "Milestone 3",
        "endpoints": ["/api/health", "/api/query", "/api/clarify", "/api/memory/<session_id>"]
    }), 200


@app.route("/<path:path>", methods=["GET"])
def serve_static(path):
    """Serves static files (CSS, JS, assets) from frontend."""
    if os.path.exists(os.path.join(frontend_dir, path)):
        return send_from_directory(frontend_dir, path)
    return jsonify({"error": "Resource not found"}), 404


@app.route("/api/health", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    """Returns API health status and vector store information."""
    indexed_docs = vector_store.get_indexed_documents()
    total_chunks = vector_store.count()
    return jsonify({
        "status": "healthy",
        "milestone": "Milestone 3",
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
    Main Multi-Agent Query Resolution Endpoint.
    
    Request payload:
        {
            "query": str,
            "session_id": str (optional),
            "clarification_response": str (optional)
        }
    """
    if request.method == "OPTIONS":
        return jsonify({}), 200

    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    session_id = data.get("session_id", "default_session").strip()
    clarification_response = data.get("clarification_response")

    if not query and not clarification_response:
        return jsonify({
            "error": "Query string or clarification response is required.",
            "is_clarification": True,
            "answer": "Please provide a valid text or voice query.",
            "confidence": {"score": 0.0, "label": "Low"},
            "sources": [],
            "citations": []
        }), 400

    result = orchestrator.process_query(
        query=query,
        session_id=session_id,
        clarification_response=clarification_response
    )

    return jsonify(result), 200


@app.route("/api/clarify", methods=["POST", "OPTIONS"])
def handle_clarify():
    """
    Submits user clarification response to refine pending ambiguous query.
    
    Request payload:
        {
            "session_id": str,
            "clarification_response": str
        }
    """
    if request.method == "OPTIONS":
        return jsonify({}), 200

    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id", "default_session").strip()
    user_response = data.get("clarification_response", "").strip()

    if not user_response:
        return jsonify({"error": "Clarification response text is required."}), 400

    result = orchestrator.process_query(
        query="",
        session_id=session_id,
        clarification_response=user_response
    )

    return jsonify(result), 200


@app.route("/api/memory/<session_id>", methods=["GET", "DELETE"])
def handle_memory(session_id):
    """Retrieves or clears conversation memory for a given session."""
    if request.method == "DELETE":
        orchestrator.memory_store.clear_session(session_id)
        return jsonify({"message": f"Memory cleared for session '{session_id}'"}), 200

    history = orchestrator.memory_store.get_session_history(session_id)
    summary = orchestrator.memory_store.get_recent_entities_and_topics(session_id)
    return jsonify({
        "session_id": session_id,
        "turns_count": len(history),
        "history": history,
        "summary": summary
    }), 200


@app.route("/upload", methods=["POST"])
@app.route("/api/upload", methods=["POST"])
def handle_upload():
    """Accepts document upload, extracts text, chunks, and indexes into ChromaDB."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded in request."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "Empty filename provided."}), 400

    filename = file.filename
    upload_dir = os.path.join(m2_dir, "knowledge_base", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    save_path = os.path.join(upload_dir, filename)
    file.save(save_path)

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
    """Re-indexes or ingests files into vector store."""
    data = request.get_json(silent=True) or {}
    filename = data.get("filename")
    kb_dir = os.path.join(m2_dir, "knowledge_base")

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
        vector_store.reset()
        initialize_default_knowledge_base()
        return jsonify({
            "message": "Knowledge base reset and re-indexed successfully",
            "total_chunks": vector_store.count()
        }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
