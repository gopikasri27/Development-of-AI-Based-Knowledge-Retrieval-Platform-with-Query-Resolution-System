"""
AI-Based Knowledge Retrieval Platform with Query Resolution System
-------------------------------------------------------------------
Main Unified Flask Application Entry Point.
Exposes RESTful endpoints and serves the Web Interface and Analytics Dashboard.
"""

import os
import sys
from flask import Flask, request, jsonify, send_from_directory, render_template

# Path configuration
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
static_dir = os.path.join(current_dir, "static")
template_dir = os.path.join(current_dir, "templates")
kb_dir = os.path.join(root_dir, "knowledge_base")
data_dir = os.path.join(root_dir, "data")

for p in [current_dir, root_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from retrieval.vector_store import VectorStoreManager
from orchestration.orchestrator import MultiAgentOrchestrator

try:
    from analytics.query_analytics import QueryAnalyticsEngine
    analytics_engine = QueryAnalyticsEngine(db_path=os.path.join(data_dir, "analytics.db"))
except Exception as e:
    print(f"[Warning] Could not initialize AnalyticsEngine: {e}")
    analytics_engine = None

app = Flask(
    __name__,
    static_folder=static_dir,
    template_folder=template_dir
)

# Initialize core services
vector_store = VectorStoreManager(
    collection_name="milestone2_knowledge_base",
    persist_directory=os.path.join(data_dir, "vectorstore")
)
orchestrator = MultiAgentOrchestrator()


def initialize_default_knowledge_base():
    """Indexes initial knowledge documents if vector store is empty."""
    if vector_store.count() == 0:
        if os.path.exists(kb_dir):
            for filename in [
                "hr_policy.txt",
                "product_manual.txt",
                "ai_ml_knowledge.txt",
                "cloud_computing_knowledge.txt",
                "cybersecurity_knowledge.txt"
            ]:
                file_path = os.path.join(kb_dir, filename)
                if os.path.exists(file_path):
                    vector_store.index_text_file(file_path, document_name=filename)


# Initial check and index if empty
initialize_default_knowledge_base()


@app.after_request
def add_security_and_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,DELETE,OPTIONS"
    response.headers["Permissions-Policy"] = "microphone=*"
    response.headers["Feature-Policy"] = "microphone *"
    return response


# ----------------------------------------------------
# Frontend View Routes
# ----------------------------------------------------

@app.route("/", methods=["GET"])
def serve_index():
    """Serves the primary Assistant Web UI."""
    index_file = os.path.join(template_dir, "index.html")
    if os.path.exists(index_file):
        return send_from_directory(template_dir, "index.html")
    return jsonify({
        "status": "online",
        "service": "AI-Based Knowledge Retrieval Platform",
        "endpoints": ["/api/health", "/api/query", "/api/clarify", "/analytics"]
    }), 200


@app.route("/analytics", methods=["GET"])
def serve_analytics():
    """Serves the Query Analytics & Knowledge Gap Dashboard."""
    analytics_file = os.path.join(template_dir, "analytics.html")
    if os.path.exists(analytics_file):
        return send_from_directory(template_dir, "analytics.html")
    return jsonify({"error": "Analytics dashboard template not found"}), 404


# Static asset fallbacks for direct relative references
@app.route("/style.css", methods=["GET"])
def serve_css():
    return send_from_directory(os.path.join(static_dir, "css"), "style.css")


@app.route("/script.js", methods=["GET"])
def serve_main_js():
    return send_from_directory(os.path.join(static_dir, "js"), "main.js")


@app.route("/voice/<path:filename>", methods=["GET"])
def serve_voice_static(filename):
    return send_from_directory(os.path.join(static_dir, "js"), filename)


@app.route("/transparency/<path:filename>", methods=["GET"])
def serve_transparency_static(filename):
    return send_from_directory(os.path.join(static_dir, "js"), filename)


@app.route("/static/<path:path>", methods=["GET"])
def serve_static_resource(path):
    return send_from_directory(static_dir, path)


# ----------------------------------------------------
# Core Multi-Agent Query Resolution Endpoints
# ----------------------------------------------------

@app.route("/api/query", methods=["POST", "OPTIONS"])
@app.route("/query", methods=["POST", "OPTIONS"])
def handle_query():
    """Main Multi-Agent Query Resolution Endpoint."""
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

    if analytics_engine:
        try:
            analytics_engine.record_query(result, session_id=session_id)
        except Exception as e:
            print(f"[Analytics Error] Failed to record query: {e}")

    return jsonify(result), 200


@app.route("/api/clarify", methods=["POST", "OPTIONS"])
def handle_clarify():
    """Submits user clarification response to resolve active ambiguous query."""
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
    """Retrieves or clears multi-turn conversation memory for a session."""
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
    """Accepts document upload, extracts text, chunks, and indexes into NumPy vector store."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded in request."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"error": "Empty filename provided."}), 400

    filename = file.filename
    upload_dir = os.path.join(kb_dir, "uploads")
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
                import docx
                doc = docx.Document(save_path)
                content = "\n\n".join([p.text for p in doc.paragraphs if p.text])
            except Exception:
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
        "file_type": ext,
        "storage_notice": "In-memory vector store: uploaded documents are available for the active session and will reset if the cloud service restarts."
    }), 200


@app.route("/api/ingest", methods=["POST"])
def handle_ingest():
    """Re-indexes or ingests files into vector store."""
    data = request.get_json(silent=True) or {}
    filename = data.get("filename")

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


@app.route("/api/health", methods=["GET"])
@app.route("/health", methods=["GET"])
def health_check():
    """Returns API health status and indexed vector store metadata."""
    indexed_docs = vector_store.get_indexed_documents()
    total_chunks = vector_store.count()
    embedding_provider = "gemini-embedding-001" if os.environ.get("GEMINI_API_KEY") else "local-hash-fallback"
    return jsonify({
        "status": "healthy",
        "service": "AI-Based Knowledge Retrieval Platform",
        "vector_store": "NumPy Cosine Vector Store",
        "embedding_provider": embedding_provider,
        "total_chunks_indexed": total_chunks,
        "total_chunks": total_chunks,
        "gemini_api_configured": bool(os.environ.get("GEMINI_API_KEY")),
        "indexed_documents": indexed_docs
    }), 200


@app.route("/documents", methods=["GET"])
def get_documents():
    """Returns list of indexed documents."""
    return jsonify({"documents": vector_store.get_indexed_documents()}), 200


# ----------------------------------------------------
# Query Analytics & Knowledge Gap API Endpoints
# ----------------------------------------------------

@app.route("/api/analytics/stats", methods=["GET"])
def get_analytics_stats():
    """Returns aggregated query analytics statistics."""
    if not analytics_engine:
        return jsonify({"error": "Analytics engine not available"}), 503
    filters = {
        "knowledge_domain": request.args.get("domain"),
        "query_type": request.args.get("query_type"),
        "resolution_status": request.args.get("status"),
        "confidence_level": request.args.get("confidence_level")
    }
    filters = {k: v for k, v in filters.items() if v is not None}
    stats = analytics_engine.get_summary_stats(filters=filters)
    return jsonify(stats), 200


@app.route("/api/analytics/gaps", methods=["GET"])
def get_analytics_gaps():
    """Returns detected knowledge gaps from low-confidence / unanswered queries."""
    if not analytics_engine:
        return jsonify({"error": "Analytics engine not available"}), 503
    min_freq = request.args.get("min_frequency", default=1, type=int)
    gaps = analytics_engine.get_knowledge_gaps(min_frequency=min_freq)
    return jsonify({"knowledge_gaps": gaps, "total_gaps": len(gaps)}), 200


@app.route("/api/analytics/queries", methods=["GET"])
def get_analytics_queries():
    """Returns recent query execution logs with filtering."""
    if not analytics_engine:
        return jsonify({"error": "Analytics engine not available"}), 503
    filters = {
        "knowledge_domain": request.args.get("domain"),
        "query_type": request.args.get("query_type"),
        "resolution_status": request.args.get("status"),
        "confidence_level": request.args.get("confidence_level")
    }
    filters = {k: v for k, v in filters.items() if v is not None}
    limit = request.args.get("limit", default=50, type=int)
    queries = analytics_engine.get_recent_queries(limit=limit, filters=filters)
    return jsonify({"queries": queries, "count": len(queries)}), 200


@app.route("/api/analytics/topics", methods=["GET"])
def get_analytics_topics():
    """Returns frequently asked topics."""
    if not analytics_engine:
        return jsonify({"error": "Analytics engine not available"}), 503
    limit = request.args.get("limit", default=10, type=int)
    topics = analytics_engine.get_frequently_asked_topics(limit=limit)
    return jsonify({"frequent_topics": topics}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
