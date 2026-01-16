"""
Q&A engine using RAG (Retrieval-Augmented Generation) with local LLM
"""
import logging
from typing import List, Tuple, Optional
from ..utils.embeddings import EmbeddingManager
from .simplifier import LegalSimplifier
from ..config import LEGAL_DISCLAIMER

logger = logging.getLogger(__name__)

class QAEngine:
    """Handles question-answering using RAG with document context"""
    
    def __init__(self, embedding_manager: EmbeddingManager, simplifier: LegalSimplifier):
        self.embedding_manager = embedding_manager
        self.simplifier = simplifier
        
        # System prompt for Q&A
        self.qa_system_prompt = """You are a legal document Q&A assistant. Your job is to answer questions based ONLY on the provided legal document context.

STRICT RULES:
1. NEVER provide legal advice
2. ONLY use information from the provided context
3. If the answer is not in the context, say "This information is not mentioned in the document"
4. Be precise and factual
5. Quote relevant parts of the document when possible
6. Use simple language in your explanations
7. NEVER guess or make assumptions
8. Always remind users this is not legal advice

Format: Provide a direct answer based on the document, then quote the relevant section(s)."""
    
    def answer_question(self, document_id: str, question: str) -> Tuple[bool, str, List[int], float]:
        """
        Answer a question about the document using RAG
        
        Args:
            document_id: Document identifier
            question: User's question
            
        Returns:
            Tuple of (success, answer, relevant_clause_ids, confidence_score)
        """
        try:
            # Load the document's vector index
            success, error = self.embedding_manager.load_index(document_id)
            if not success:
                return False, f"Could not load document: {error}", [], 0.0
            
            # Search for relevant clauses
            relevant_clauses = self.embedding_manager.search_similar_clauses(
                query=question,
                top_k=5,
                min_score=0.2
            )
            
            if not relevant_clauses:
                answer = "This information is not mentioned in the document."
                return True, answer, [], 0.0
            
            # Prepare context from relevant clauses
            context = self._prepare_context(relevant_clauses)
            clause_ids = [clause['clause_id'] for clause in relevant_clauses]
            
            # Generate answer using LLM
            success, answer, error = self._generate_answer(question, context)
            
            if not success:
                return False, f"Error generating answer: {error}", clause_ids, 0.0
            
            # Calculate confidence based on similarity scores
            confidence = self._calculate_confidence(relevant_clauses)
            
            # Add disclaimer
            answer_with_disclaimer = f"{answer}\n\n{LEGAL_DISCLAIMER}"
            
            logger.info(f"Answered question with {len(relevant_clauses)} relevant clauses")
            return True, answer_with_disclaimer, clause_ids, confidence
            
        except Exception as e:
            error_msg = f"Error in Q&A: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, [], 0.0
    
    def _prepare_context(self, relevant_clauses: List[dict]) -> str:
        """Prepare context string from relevant clauses"""
        context_parts = []
        
        for i, clause in enumerate(relevant_clauses, 1):
            original_text = clause.get('original_text', '')
            simplified_text = clause.get('simplified_text', '')
            section_num = clause.get('section_number', '')
            
            context_part = f"--- Relevant Section {i}"
            if section_num:
                context_part += f" ({section_num})"
            context_part += " ---\n"
            
            context_part += f"Original text: {original_text}\n"
            if simplified_text:
                context_part += f"Simplified: {simplified_text}\n"
            
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _generate_answer(self, question: str, context: str) -> Tuple[bool, str, Optional[str]]:
        """Generate answer using LLM with context"""
        try:
            user_prompt = f"""Based on the following legal document sections, please answer this question:

Question: {question}

Document Context:
{context}

Remember: Only use information from the provided context. If the answer is not in the context, say "This information is not mentioned in the document." Do not provide legal advice."""
            
            # Use the simplifier's LLM client
            response = self.simplifier.client.chat(
                model=self.simplifier.model_name,
                messages=[
                    {"role": "system", "content": self.qa_system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": 400,
                }
            )
            
            answer = response['message']['content'].strip()
            
            if not answer or len(answer) < 10:
                return False, "", "LLM returned empty response"
            
            return True, answer, None
            
        except Exception as e:
            return False, "", str(e)
    
    def _calculate_confidence(self, relevant_clauses: List[dict]) -> float:
        """Calculate confidence score based on similarity scores"""
        if not relevant_clauses:
            return 0.0
        
        # Use the highest similarity score as base confidence
        max_score = max(clause.get('similarity_score', 0.0) for clause in relevant_clauses)
        
        # Adjust based on number of relevant clauses
        num_clauses = len(relevant_clauses)
        if num_clauses >= 3:
            confidence_boost = 0.1
        elif num_clauses >= 2:
            confidence_boost = 0.05
        else:
            confidence_boost = 0.0
        
        confidence = min(max_score + confidence_boost, 1.0)
        return round(confidence, 2)
    
    def get_document_summary(self, document_id: str) -> Tuple[bool, str]:
        """Get a summary of the document's key points"""
        try:
            success, error = self.embedding_manager.load_index(document_id)
            if not success:
                return False, f"Could not load document: {error}"
            
            # Get a sample of clauses for summary
            sample_clauses = []
            for i, (idx, metadata) in enumerate(self.embedding_manager.clause_metadata.items()):
                if i < 5:  # First 5 clauses
                    sample_clauses.append(metadata)
            
            if not sample_clauses:
                return False, "No clauses found in document"
            
            # Create summary context
            context = self._prepare_context(sample_clauses)
            
            summary_prompt = f"""Based on these legal document sections, provide a brief summary of the key points and main topics covered:

{context}

Provide a concise summary in bullet points."""
            
            success, summary, error = self._generate_answer("What are the main points of this document?", context)
            
            if success:
                return True, f"{summary}\n\n{LEGAL_DISCLAIMER}"
            else:
                return False, error
                
        except Exception as e:
            return False, str(e)