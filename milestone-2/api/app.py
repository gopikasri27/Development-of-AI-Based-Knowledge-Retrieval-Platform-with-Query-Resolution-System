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
from flask import Flask, request, jsonify

# Ensure local imports resolve
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
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


@app.route("/api/health", methods=["GET"])
def health_check():
    """
    Returns API health status and indexed document summary.
    """
    indexed_docs = vector_store.get_indexed_documents()
    total_chunks = vector_store.count()
    return jsonify({
        "status": "healthy",
        "milestone": "Milestone 2",
        "total_chunks": total_chunks,
        "indexed_documents": indexed_docs
    }), 200


@app.route("/api/query", methods=["POST", "OPTIONS"])
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
            "sources": [...],
            "confidence": { "score": float, "label": str }
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
            "sources": [],
            "confidence": {
                "score": 0.0,
                "label": "Low"
            }
        }), 400

    result = orchestrator.process_query(query)
    return jsonify(result), 200


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
