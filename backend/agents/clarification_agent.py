"""
Clarification Agent
------------------
Role: Determines if the user's query is ambiguous or if retrieved evidence
confidence is too low. Generates structured clarifying questions instead of
hallucinating an unsupported answer.
"""

from typing import Dict, Any, List


class ClarificationAgent:
    def __init__(self, confidence_threshold: float = 0.50):
        self.confidence_threshold = confidence_threshold

    def needs_clarification(
        self,
        query_data: Dict[str, Any],
        retrieval_data: Dict[str, Any]
    ) -> bool:
        """
        Determines whether clarification is required.
        Triggers if:
        1. Query agent flagged the query as ambiguous / too sparse.
        2. Zero chunks retrieved from the knowledge base.
        3. Top retrieval similarity is below the confidence threshold.
        """
        if query_data.get("is_ambiguous", False):
            return True
            
        chunks = retrieval_data.get("retrieved_chunks", [])
        if not chunks:
            return True
            
        top_similarity = retrieval_data.get("top_similarity", 0.0)
        if top_similarity < self.confidence_threshold:
            return True
            
        return False

    def generate_clarification(
        self,
        query_data: Dict[str, Any],
        retrieval_data: Dict[str, Any],
        available_documents: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generates a targeted, helpful clarification message and options for the user.
        """
        original_query = query_data.get("original_query", "")
        keywords = query_data.get("keywords", [])
        top_sim = retrieval_data.get("top_similarity", 0.0)
        available_docs = available_documents or []
        
        # Build tailored explanation
        if not retrieval_data.get("retrieved_chunks"):
            reason = "No relevant information was found in the indexed knowledge base for your inquiry."
            suggestion = "Could you please specify which document or topic you are asking about?"
        elif top_sim < self.confidence_threshold:
            reason = f"The knowledge base has low relevance confidence ({int(top_sim * 100)}%) for '{original_query}'."
            suggestion = "To avoid providing an incorrect answer, could you please clarify or rephrase your question with more specific details?"
        else:
            reason = "Your query appears broad or ambiguous."
            suggestion = "Please provide additional context or specify which policy/product feature you mean."
            
        doc_list_text = ""
        if available_docs:
            doc_list_text = f"\n\nCurrently indexed knowledge sources: {', '.join(available_docs)}"
            
        clarification_response = f"I want to make sure I give you accurate information.\n\n{reason}\n{suggestion}{doc_list_text}"
        
        return {
            "agent": "Clarification Agent",
            "needs_clarification": True,
            "clarification_message": clarification_response,
            "reason": reason,
            "top_similarity": top_sim,
            "suggested_actions": [
                "Rephrase your question with more specific keywords",
                "Mention the document name (e.g., HR Policy, User Manual)",
                "Upload the relevant document if it hasn't been added yet"
            ]
        }
