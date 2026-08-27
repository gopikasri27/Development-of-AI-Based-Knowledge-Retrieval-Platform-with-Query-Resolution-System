"""
Multi-Agent RAG Orchestrator
----------------------------
Role: Coordinates the full agent pipeline sequentially:
1. Memory Agent retrieves session history.
2. Query Agent parses intent, extracts entities, and classifies query type.
3. Retrieval Agent executes semantic vector search over ChromaDB.
4. Clarification Agent checks confidence threshold / ambiguity.
   - If confidence is low or ambiguous: returns clarifying response.
5. Response Agent synthesizes grounded answer with Google Gemini API and citations.
6. Memory Agent records the conversational turn.
"""

from typing import Dict, Any
from agents.query_agent import QueryAgent
from agents.retrieval_agent import RetrievalAgent
from agents.clarification_agent import ClarificationAgent
from agents.response_agent import ResponseAgent
from agents.memory_agent import MemoryAgent
from utils.embeddings import get_all_indexed_documents


class MultiAgentRAGOrchestrator:
    def __init__(self):
        self.query_agent = QueryAgent()
        self.retrieval_agent = RetrievalAgent(default_top_k=5, min_confidence_threshold=0.50)
        self.clarification_agent = ClarificationAgent(confidence_threshold=0.50)
        self.response_agent = ResponseAgent(model_name="gemini-1.5-flash")
        self.memory_agent = MemoryAgent(max_history_turns=5)

    def run(self, query: str, session_id: str = "default_session") -> Dict[str, Any]:
        """
        Executes the end-to-end multi-agent resolution pipeline.
        """
        steps = []
        
        # Step 1: Memory Agent - Fetch recent history
        history = self.memory_agent.get_history(session_id)
        steps.append({
            "step": 1,
            "agent": "Memory Agent",
            "action": "Retrieved session context",
            "details": f"Loaded {len(history)} prior conversational turns."
        })

        # Step 2: Query Understanding Agent
        query_data = self.query_agent.process(query, history=history)
        steps.append({
            "step": 2,
            "agent": "Query Understanding Agent",
            "action": "Parsed intent and classified query",
            "details": {
                "query_type": query_data["query_type"],
                "keywords": query_data["keywords"],
                "reformulated_query": query_data["reformulated_query"]
            }
        })

        # Step 3: Retrieval Agent - Vector Search in ChromaDB
        retrieval_data = self.retrieval_agent.process(query_data, top_k=5)
        steps.append({
            "step": 3,
            "agent": "Retrieval Agent",
            "action": "Retrieved semantic chunks from ChromaDB",
            "details": {
                "chunks_found": retrieval_data["chunks_count"],
                "top_similarity": retrieval_data["top_similarity"],
                "avg_similarity": retrieval_data["avg_similarity"],
                "confidence_status": retrieval_data["status"]
            }
        })

        # Step 4: Clarification Agent - Evaluate confidence & ambiguity
        indexed_docs = [d["source"] for d in get_all_indexed_documents()]
        needs_clarification = self.clarification_agent.needs_clarification(query_data, retrieval_data)
        
        if needs_clarification:
            clarification_data = self.clarification_agent.generate_clarification(
                query_data, retrieval_data, available_documents=indexed_docs
            )
            final_answer = clarification_data["clarification_message"]
            citations = []
            engine = "Clarification Agent"
            is_clarification = True
            
            steps.append({
                "step": 4,
                "agent": "Clarification Agent",
                "action": "Triggered clarification due to low confidence or ambiguity",
                "details": {
                    "reason": clarification_data["reason"],
                    "top_similarity": clarification_data["top_similarity"]
                }
            })
        else:
            is_clarification = False
            # Step 5: Response Generation Agent (Gemini API + citations)
            response_data = self.response_agent.process(query_data, retrieval_data, history=history)
            final_answer = response_data["answer"]
            citations = response_data["citations"]
            engine = response_data["engine"]
            
            steps.append({
                "step": 4,
                "agent": "Clarification Agent",
                "action": "Validated confidence threshold (Passed)",
                "details": f"Confidence score {int(retrieval_data['top_similarity'] * 100)}% >= threshold 50%."
            })
            
            steps.append({
                "step": 5,
                "agent": "Response Generation Agent",
                "action": "Synthesized grounded response with citations",
                "details": {
                    "engine": engine,
                    "citations_count": len(citations)
                }
            })

        # Step 6: Memory Agent - Update conversation memory
        self.memory_agent.process(
            session_id=session_id,
            user_query=query,
            agent_response=final_answer,
            sources=citations,
            query_type=query_data["query_type"]
        )
        steps.append({
            "step": 6 if not is_clarification else 5,
            "agent": "Memory Agent",
            "action": "Saved conversation turn to metadata database",
            "details": f"Session '{session_id}' updated."
        })

        return {
            "query": query,
            "query_type": query_data["query_type"],
            "response": final_answer,
            "citations": citations,
            "is_clarification": is_clarification,
            "confidence_score": retrieval_data["top_similarity"],
            "agent_pipeline_steps": steps,
            "engine": engine,
            "session_id": session_id
        }
