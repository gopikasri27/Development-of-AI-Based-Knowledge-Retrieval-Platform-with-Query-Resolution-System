"""
Milestone 3 Extended Agent Orchestrator
----------------------------------------
Orchestrates the full multi-agent query resolution pipeline:
1. Conversation Memory Agent (M3.2) - Session history check & pronoun resolution
2. Query Understanding Agent (M2.1) - Intent classification
3. Clarification Agent (M3.1) - Ambiguity detection & follow-up question generation
4. Retrieval Agent (M2.2) - Vector search over ChromaDB
5. Response Generation Agent (M2.3) - Grounded answer synthesis & confidence calculation
6. Response Transparency Panel Formatting (M3.4) - Metadata & citation structure
"""

import time
import os
import sys
from typing import Dict, Any, Optional

# Ensure both milestone-2 and milestone-3 roots are in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
m3_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(m3_dir)
m2_dir = os.path.join(root_dir, "milestone-2")

for p in [m2_dir, m3_dir, root_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

import agents
m2_agents_dir = os.path.join(m2_dir, "agents")
m3_agents_dir = os.path.join(m3_dir, "agents")
if hasattr(agents, "__path__"):
    if m2_agents_dir not in agents.__path__:
        agents.__path__.append(m2_agents_dir)
    if m3_agents_dir not in agents.__path__:
        agents.__path__.append(m3_agents_dir)

# M2 Agents
from agents.query_understanding_agent import QueryUnderstandingAgent
from agents.retrieval_agent import RetrievalAgent
from agents.response_generation_agent import ResponseGenerationAgent, INSUFFICIENT_INFO_MESSAGE

# M3 Agents & Memory
from agents.clarification_agent import ClarificationAgent
from agents.conversation_memory_agent import ConversationMemoryAgent
from memory.conversation_memory import ConversationMemory


class Milestone3Orchestrator:
    """
    Coordinates multi-agent query resolution with Memory, Clarification, Retrieval,
    Generation, and Transparency support.
    """

    def __init__(
        self,
        memory_store: Optional[ConversationMemory] = None,
        memory_agent: Optional[ConversationMemoryAgent] = None,
        query_agent: Optional[QueryUnderstandingAgent] = None,
        clarification_agent: Optional[ClarificationAgent] = None,
        retrieval_agent: Optional[RetrievalAgent] = None,
        response_agent: Optional[ResponseGenerationAgent] = None
    ):
        self.memory_store = memory_store or ConversationMemory()
        self.memory_agent = memory_agent or ConversationMemoryAgent(memory_store=self.memory_store)
        self.query_agent = query_agent or QueryUnderstandingAgent()
        self.clarification_agent = clarification_agent or ClarificationAgent()
        self.retrieval_agent = retrieval_agent or RetrievalAgent()
        self.response_agent = response_agent or ResponseGenerationAgent()

    def process_query(
        self,
        query: str,
        session_id: str = "default_session",
        clarification_response: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end Milestone 3 resolution pipeline.
        
        Args:
            query (str): User text or voice transcription.
            session_id (str): Multi-turn session identifier.
            clarification_response (Optional[str]): User's answer to a previous clarification question.
            
        Returns:
            Dict containing answer, clarification state, citations, confidence, telemetry, and memory state.
        """
        start_time = time.time()
        telemetry_steps = []

        is_refinement = False
        original_query = query
        effective_query = query.strip()

        # -------------------------------------------------------------
        # STEP 1: Handle pending clarification or refinement
        # -------------------------------------------------------------
        t0 = time.time()
        pending = self.memory_store.get_pending_clarification(session_id)

        if pending and (clarification_response or effective_query):
            user_response = clarification_response or effective_query
            effective_query = self.clarification_agent.refine_query(
                original_query=pending["original_query"],
                clarification_response=user_response,
                clarification_question=pending["clarification_question"]
            )
            original_query = pending["original_query"]
            self.memory_store.clear_pending_clarification(session_id)
            is_refinement = True

        # Conversation Memory Agent context processing
        memory_context = self.memory_agent.process_query_context(session_id, effective_query)
        resolved_query = memory_context.get("resolved_query", effective_query)

        telemetry_steps.append({
            "step": 1,
            "agent": "Conversation Memory Agent",
            "status": "success",
            "duration_ms": round((time.time() - t0) * 1000, 2),
            "details": {
                "session_id": session_id,
                "is_context_dependent": memory_context.get("is_context_dependent", False),
                "pronoun_resolved": memory_context.get("pronoun_resolved"),
                "resolved_query": resolved_query,
                "is_refinement": is_refinement
            }
        })

        # -------------------------------------------------------------
        # STEP 2: Query Understanding Agent (M2.1)
        # -------------------------------------------------------------
        t1 = time.time()
        try:
            query_classification = self.query_agent.analyze_query(resolved_query)
            classified_type = query_classification.get("query_type", "factual")
            classification_confidence = float(query_classification.get("classification_confidence", 0.0))

            telemetry_steps.append({
                "step": 2,
                "agent": "Query Understanding Agent",
                "status": "success",
                "duration_ms": round((time.time() - t1) * 1000, 2),
                "details": {
                    "query_type": classified_type,
                    "confidence": classification_confidence
                }
            })
        except Exception as e:
            query_classification = {
                "query": resolved_query,
                "query_type": "factual",
                "classification_confidence": 0.50,
                "routing": "retrieval"
            }
            classified_type = "factual"
            classification_confidence = 0.50
            telemetry_steps.append({
                "step": 2,
                "agent": "Query Understanding Agent",
                "status": "error_fallback",
                "duration_ms": round((time.time() - t1) * 1000, 2),
                "error": str(e)
            })

        # -------------------------------------------------------------
        # STEP 3: Clarification Agent (M3.1)
        # -------------------------------------------------------------
        t2 = time.time()
        # If this is ALREADY a refined query after user clarified, bypass secondary clarification
        if is_refinement:
            clarification_eval = {
                "clarification_required": False,
                "ambiguity_type": "none",
                "clarification_question": None,
                "reasoning": "Query was refined using user clarification response."
            }
        else:
            clarification_eval = self.clarification_agent.evaluate_query(
                query=resolved_query,
                memory_context=memory_context,
                query_classification=query_classification
            )

        telemetry_steps.append({
            "step": 3,
            "agent": "Clarification Agent",
            "status": "success",
            "duration_ms": round((time.time() - t2) * 1000, 2),
            "details": {
                "clarification_required": clarification_eval["clarification_required"],
                "ambiguity_type": clarification_eval["ambiguity_type"]
            }
        })

        if clarification_eval["clarification_required"]:
            cq = clarification_eval["clarification_question"]
            self.memory_store.set_pending_clarification(
                session_id=session_id,
                original_query=original_query,
                clarification_question=cq,
                ambiguity_type=clarification_eval["ambiguity_type"]
            )

            total_duration = round((time.time() - start_time) * 1000, 2)
            return {
                "query": original_query,
                "refined_query": resolved_query,
                "session_id": session_id,
                "is_clarification": True,
                "clarification_question": cq,
                "answer": f"**Clarification Required:** {cq}",
                "query_type": "ambiguous",
                "classification_confidence": round(classification_confidence, 2),
                "sources": [],
                "citations": [],
                "confidence": {"score": 0.0, "label": "Low"},
                "transparency": {
                    "confidence_score": 0.0,
                    "confidence_label": "Low",
                    "sources": [],
                    "insufficient_evidence": True,
                    "message": "Query is ambiguous or context is missing; clarification required before retrieval."
                },
                "telemetry": {
                    "pipeline_steps": telemetry_steps,
                    "total_duration_ms": total_duration
                },
                "memory_summary": self.memory_store.get_recent_entities_and_topics(session_id)
            }

        # -------------------------------------------------------------
        # STEP 4: Retrieval Agent (M2.2)
        # -------------------------------------------------------------
        t3 = time.time()
        try:
            retrieved_data = self.retrieval_agent.retrieve(
                query=resolved_query,
                query_classification=query_classification
            )
            chunks_found = retrieved_data.get("result_count", 0)
            top_relevance = retrieved_data["results"][0]["relevance_score"] if retrieved_data.get("results") else 0.0

            telemetry_steps.append({
                "step": 4,
                "agent": "Retrieval Agent",
                "status": "success",
                "duration_ms": round((time.time() - t3) * 1000, 2),
                "details": {
                    "chunks_retrieved": chunks_found,
                    "top_relevance": top_relevance
                }
            })
        except Exception as e:
            retrieved_data = {"query": resolved_query, "results": [], "result_count": 0}
            telemetry_steps.append({
                "step": 4,
                "agent": "Retrieval Agent",
                "status": "error_fallback",
                "duration_ms": round((time.time() - t3) * 1000, 2),
                "error": str(e)
            })

        # -------------------------------------------------------------
        # STEP 5: Response Generation Agent (M2.3)
        # -------------------------------------------------------------
        t4 = time.time()
        try:
            generation_output = self.response_agent.generate_response(
                query=resolved_query,
                query_classification=query_classification,
                retrieved_data=retrieved_data
            )

            telemetry_steps.append({
                "step": 5,
                "agent": "Response Generation Agent",
                "status": "success",
                "duration_ms": round((time.time() - t4) * 1000, 2),
                "details": {
                    "confidence_score": generation_output["confidence"]["score"],
                    "confidence_label": generation_output["confidence"]["label"]
                }
            })
        except Exception as e:
            generation_output = {
                "answer": INSUFFICIENT_INFO_MESSAGE,
                "sources": [],
                "confidence": {"score": 0.0, "label": "Low"}
            }
            telemetry_steps.append({
                "step": 5,
                "agent": "Response Generation Agent",
                "status": "error_fallback",
                "duration_ms": round((time.time() - t4) * 1000, 2),
                "error": str(e)
            })

        # -------------------------------------------------------------
        # STEP 6: Response Transparency Panel Metadata Preparation (M3.4)
        # -------------------------------------------------------------
        answer_text = generation_output.get("answer", INSUFFICIENT_INFO_MESSAGE)
        confidence = generation_output.get("confidence", {"score": 0.0, "label": "Low"})
        retrieved_results = retrieved_data.get("results", [])

        citations = []
        for r in retrieved_results:
            citations.append({
                "document_name": r.get("document_name", "unknown"),
                "source_file": r.get("document_name", "unknown"),
                "page": r.get("page", 1),
                "section": r.get("section", "General"),
                "chunk_id": r.get("chunk_id", "chunk_0"),
                "relevance_score": round(float(r.get("relevance_score", 0.0)), 4),
                "similarity_score": round(float(r.get("relevance_score", 0.0)), 4),
                "content": r.get("content", ""),
                "excerpt": r.get("content", "")
            })

        insufficient_evidence = len(citations) == 0 or confidence["score"] < 0.30

        transparency_panel_data = {
            "confidence_score": confidence.get("score", 0.0),
            "confidence_label": confidence.get("label", "Low"),
            "sources": citations,
            "total_retrieved_chunks": len(citations),
            "insufficient_evidence": insufficient_evidence,
            "message": "Insufficient supporting evidence was found in the knowledge base." if insufficient_evidence else None
        }

        # Update Conversation Memory
        self.memory_store.add_turn(
            session_id=session_id,
            query=original_query,
            answer=answer_text,
            refined_query=resolved_query,
            query_type=classified_type,
            sources=citations,
            topic=memory_context.get("topic")
        )

        total_duration = round((time.time() - start_time) * 1000, 2)

        return {
            "query": original_query,
            "refined_query": resolved_query if is_refinement or resolved_query != original_query else None,
            "session_id": session_id,
            "is_clarification": False,
            "clarification_question": None,
            "answer": answer_text,
            "response": answer_text,
            "query_type": classified_type,
            "classification_confidence": round(classification_confidence, 2),
            "sources": generation_output.get("sources", []),
            "citations": citations,
            "confidence": confidence,
            "transparency": transparency_panel_data,
            "telemetry": {
                "pipeline_steps": telemetry_steps,
                "total_duration_ms": total_duration
            },
            "memory_summary": self.memory_store.get_recent_entities_and_topics(session_id)
        }
