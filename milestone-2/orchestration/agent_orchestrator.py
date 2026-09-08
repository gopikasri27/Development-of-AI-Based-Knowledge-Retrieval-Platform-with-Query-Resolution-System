"""
Multi-Agent Orchestrator (M2.4)
-------------------------------
Coordinates the 3 specialized agents in strict sequence:
1. Query Understanding Agent (M2.1)
2. Retrieval Agent (M2.2)
3. Response Generation Agent (M2.3)

Provides robust exception handling at every boundary, collects step telemetry,
and produces standardized JSON response payloads.
"""

import time
import traceback
from typing import Dict, Any, Optional
import os
import sys

# Ensure local imports resolve
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from agents.query_understanding_agent import QueryUnderstandingAgent
from agents.retrieval_agent import RetrievalAgent
from agents.response_generation_agent import ResponseGenerationAgent, INSUFFICIENT_INFO_MESSAGE


class MultiAgentOrchestrator:
    """
    Coordinates multi-agent query understanding, retrieval, and grounded response synthesis.
    """
    def __init__(
        self,
        query_agent: Optional[QueryUnderstandingAgent] = None,
        retrieval_agent: Optional[RetrievalAgent] = None,
        response_agent: Optional[ResponseGenerationAgent] = None
    ):
        self.query_agent = query_agent or QueryUnderstandingAgent()
        self.retrieval_agent = retrieval_agent or RetrievalAgent()
        self.response_agent = response_agent or ResponseGenerationAgent()

    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Executes the end-to-end sequential multi-agent pipeline.
        
        Sequence:
            User Query
                ↓
            Query Understanding Agent (M2.1)
                ↓
            Retrieval Agent (M2.2)
                ↓
            Response Generation Agent (M2.3)
                ↓
            Final Response
            
        Returns standard API / system response dictionary.
        """
        start_time = time.time()
        telemetry_steps = []

        # Default fallback state
        classified_type = "ambiguous"
        classification_confidence = 0.0
        retrieved_data = {"query": query, "results": [], "result_count": 0}

        # -------------------------------------------------------------
        # STEP 1: Query Understanding Agent
        # -------------------------------------------------------------
        t0 = time.time()
        try:
            query_classification = self.query_agent.analyze_query(query)
            classified_type = query_classification.get("query_type", "factual")
            classification_confidence = float(query_classification.get("classification_confidence", 0.0))
            routing = query_classification.get("routing", "retrieval")

            telemetry_steps.append({
                "step": 1,
                "agent": "Query Understanding Agent",
                "status": "success",
                "duration_ms": round((time.time() - t0) * 1000, 2),
                "details": {
                    "query_type": classified_type,
                    "classification_confidence": classification_confidence,
                    "routing": routing
                }
            })
        except Exception as e:
            # Classification failure fallback
            query_classification = {
                "query": query,
                "query_type": "factual",
                "classification_confidence": 0.50,
                "routing": "retrieval",
                "error": str(e)
            }
            classified_type = "factual"
            classification_confidence = 0.50
            telemetry_steps.append({
                "step": 1,
                "agent": "Query Understanding Agent",
                "status": "error_fallback",
                "duration_ms": round((time.time() - t0) * 1000, 2),
                "error": str(e)
            })

        # -------------------------------------------------------------
        # STEP 2: Retrieval Agent
        # -------------------------------------------------------------
        t1 = time.time()
        try:
            if query_classification.get("routing") == "clarification":
                # Ambiguous queries: skip heavy retrieval or return empty results
                retrieved_data = {
                    "query": query,
                    "results": [],
                    "result_count": 0
                }
                telemetry_steps.append({
                    "step": 2,
                    "agent": "Retrieval Agent",
                    "status": "skipped_ambiguous",
                    "duration_ms": round((time.time() - t1) * 1000, 2),
                    "details": {"reason": "Query marked for clarification; retrieval bypassed."}
                })
            else:
                retrieved_data = self.retrieval_agent.retrieve(
                    query=query,
                    query_classification=query_classification
                )
                telemetry_steps.append({
                    "step": 2,
                    "agent": "Retrieval Agent",
                    "status": "success",
                    "duration_ms": round((time.time() - t1) * 1000, 2),
                    "details": {
                        "chunks_retrieved": retrieved_data.get("result_count", 0),
                        "top_score": retrieved_data["results"][0]["relevance_score"] if retrieved_data.get("results") else 0.0
                    }
                })
        except Exception as e:
            # Retrieval failure fallback
            retrieved_data = {
                "query": query,
                "results": [],
                "result_count": 0,
                "error": str(e)
            }
            telemetry_steps.append({
                "step": 2,
                "agent": "Retrieval Agent",
                "status": "error_fallback",
                "duration_ms": round((time.time() - t1) * 1000, 2),
                "error": str(e)
            })

        # -------------------------------------------------------------
        # STEP 3: Response Generation Agent
        # -------------------------------------------------------------
        t2 = time.time()
        try:
            generation_output = self.response_agent.generate_response(
                query=query,
                query_classification=query_classification,
                retrieved_data=retrieved_data
            )
            telemetry_steps.append({
                "step": 3,
                "agent": "Response Generation Agent",
                "status": "success",
                "duration_ms": round((time.time() - t2) * 1000, 2),
                "details": {
                    "confidence_score": generation_output["confidence"]["score"],
                    "confidence_label": generation_output["confidence"]["label"],
                    "sources_count": len(generation_output.get("sources", []))
                }
            })
        except Exception as e:
            # Generation failure fallback
            generation_output = {
                "answer": INSUFFICIENT_INFO_MESSAGE,
                "sources": [],
                "confidence": {
                    "score": 0.0,
                    "label": "Low"
                }
            }
            telemetry_steps.append({
                "step": 3,
                "agent": "Response Generation Agent",
                "status": "error_fallback",
                "duration_ms": round((time.time() - t2) * 1000, 2),
                "error": str(e)
            })

        total_duration_ms = round((time.time() - start_time) * 1000, 2)

        # Standard unified response payload
        return {
            "query": query,
            "query_type": classified_type,
            "classification_confidence": round(classification_confidence, 2),
            "answer": generation_output.get("answer", INSUFFICIENT_INFO_MESSAGE),
            "sources": generation_output.get("sources", []),
            "confidence": generation_output.get("confidence", {"score": 0.0, "label": "Low"}),
            "telemetry": {
                "pipeline_steps": telemetry_steps,
                "total_duration_ms": total_duration_ms
            }
        }
