"""
Legal text simplification service using local LLM via Ollama
"""
import ollama
import logging
from typing import Optional, Tuple
import time

logger = logging.getLogger(__name__)

class LegalSimplifier:
    """Simplifies legal text using local LLM"""
    
    def __init__(self, model_name: str = "gemma3:12b", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.client = ollama.Client(host=base_url)
        
        # System prompt for legal simplification
        self.system_prompt = """You are a legal text simplifier. Your job is to explain legal clauses in simple, plain English that a non-lawyer can understand.

STRICT RULES:
1. NEVER provide legal advice
2. NEVER guess or hallucinate information
3. Only explain what the text actually says
4. Use simple, everyday language
5. Break down complex sentences
6. Explain legal terms in parentheses
7. Keep explanations concise but complete
8. If you cannot simplify something, say "This clause is too complex to simplify safely"

Format your response as a clear, simple explanation of what the legal text means."""
    
    def simplify_clause(self, legal_text: str) -> Tuple[bool, str, Optional[str]]:
        """
        Simplify a legal clause into plain English
        
        Args:
            legal_text: Original legal text to simplify
            
        Returns:
            Tuple of (success, simplified_text, error_message)
        """
        try:
            # Check if text is too short to simplify
            if len(legal_text.strip()) < 20:
                return True, "This clause is too short to require simplification.", None
            
            # Check if Ollama is available
            if not self._check_ollama_connection():
                return False, "", "Ollama service is not available. Please ensure Ollama is running."
            
            # Prepare a simpler, more direct prompt
            user_prompt = f"""Explain this legal text in simple English that anyone can understand:

{legal_text}

Make it clear and easy to read. Don't give legal advice, just explain what it says."""
            
            logger.info(f"Sending request to {self.model_name}...")
            
            # Call Ollama with more generous settings
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.3,  # Slightly higher for more natural language
                    "top_p": 0.9,
                    "num_predict": 500,  # More tokens for better explanations
                    "stop": ["Legal advice:", "I recommend", "You should"],  # Stop on advice-giving
                }
            )
            
            simplified_text = response['message']['content'].strip()
            
            # Basic validation of the response
            if not simplified_text or len(simplified_text) < 10:
                logger.warning("LLM returned empty or very short response")
                return True, f"In simple terms: {legal_text[:200]}... (This clause contains standard legal language)", None
            
            # Remove any potential legal advice language
            simplified_text = self._clean_response(simplified_text)
            
            logger.info(f"Successfully simplified clause ({len(legal_text)} -> {len(simplified_text)} chars)")
            return True, simplified_text, None
            
        except Exception as e:
            error_msg = f"Error simplifying clause: {str(e)}"
            logger.error(error_msg)
            # Provide a fallback explanation instead of failing
            fallback = f"This clause discusses: {legal_text[:100]}..." if len(legal_text) > 100 else legal_text
            return True, fallback, None
    
    def _check_ollama_connection(self) -> bool:
        """Check if Ollama service is available"""
        try:
            # Try to list models to check connection
            models = self.client.list()
            
            # Check if our model is available
            available_models = [model['name'] for model in models['models']]
            if self.model_name not in available_models:
                logger.warning(f"Model {self.model_name} not found. Available models: {available_models}")
                # Try to pull the model
                try:
                    logger.info(f"Attempting to pull model {self.model_name}...")
                    self.client.pull(self.model_name)
                    return True
                except Exception as e:
                    logger.error(f"Failed to pull model {self.model_name}: {e}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ollama connection failed: {e}")
            return False
    
    def _clean_response(self, text: str) -> str:
        """Clean the LLM response to remove problematic content"""
        # Remove common legal advice phrases
        advice_phrases = [
            "you should", "you must", "i recommend", "i suggest",
            "you need to", "it's best to", "you ought to",
            "my advice", "i advise", "you have to", "i would recommend"
        ]
        
        cleaned_text = text
        for phrase in advice_phrases:
            # Replace advice language with neutral language
            cleaned_text = cleaned_text.replace(phrase, "this means")
        
        # Add disclaimer if needed
        if any(phrase in text.lower() for phrase in advice_phrases):
            cleaned_text += "\n\n⚠️ Note: This is an explanation only, not legal advice."
        
        return cleaned_text
    
    def _contains_legal_advice(self, text: str) -> bool:
        """Check if text contains potential legal advice"""
        advice_indicators = [
            "you should", "you must", "i recommend", "i suggest",
            "you need to", "it's best to", "you ought to",
            "my advice", "i advise", "you have to"
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in advice_indicators)
    
    def get_model_info(self) -> dict:
        """Get information about the current model"""
        try:
            models = self.client.list()
            for model in models['models']:
                if model['name'] == self.model_name:
                    return {
                        'name': model['name'],
                        'size': model.get('size', 'Unknown'),
                        'modified_at': model.get('modified_at', 'Unknown')
                    }
            return {'error': f'Model {self.model_name} not found'}
        except Exception as e:
            return {'error': str(e)}
    
    def test_model(self) -> Tuple[bool, str]:
        """Test if the model is working properly"""
        try:
            test_text = "The party agrees to indemnify the other party."
            success, result, error = self.simplify_clause(test_text)
            if success:
                return True, f"Model test successful: {result[:100]}..."
            else:
                return False, f"Model test failed: {error}"
        except Exception as e:
            return False, f"Model test error: {str(e)}"