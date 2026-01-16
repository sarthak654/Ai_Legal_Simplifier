"""
Legal clause splitting service using rule-based approach
"""
import re
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class ClauseSplitter:
    """Splits legal documents into individual clauses using rule-based logic"""
    
    def __init__(self):
        # Patterns for identifying clause boundaries
        self.section_patterns = [
            r'^\d+\.\s+',  # 1. Section
            r'^\d+\.\d+\s+',  # 1.1 Subsection
            r'^\([a-z]\)\s+',  # (a) Paragraph
            r'^\([0-9]+\)\s+',  # (1) Numbered paragraph
            r'^[A-Z][A-Z\s]+:',  # SECTION HEADER:
            r'^Article\s+\d+',  # Article 1
            r'^Section\s+\d+',  # Section 1
        ]
        
        # Minimum clause length (characters)
        self.min_clause_length = 50
        
        # Maximum clause length (characters) - split if longer
        self.max_clause_length = 2000
    
    def split_document(self, text: str) -> List[Dict[str, any]]:
        """
        Split document text into legal clauses
        
        Args:
            text: Full document text
            
        Returns:
            List of clause dictionaries with metadata
        """
        try:
            # First, split by major section boundaries
            sections = self._split_by_sections(text)
            
            clauses = []
            clause_id = 1
            
            for section in sections:
                section_clauses = self._split_section_into_clauses(section)
                
                for clause_text in section_clauses:
                    if len(clause_text.strip()) >= self.min_clause_length:
                        clause = {
                            'id': clause_id,
                            'text': clause_text.strip(),
                            'section_number': self._extract_section_number(clause_text),
                            'word_count': len(clause_text.split()),
                            'char_count': len(clause_text)
                        }
                        clauses.append(clause)
                        clause_id += 1
            
            logger.info(f"Split document into {len(clauses)} clauses")
            return clauses
            
        except Exception as e:
            logger.error(f"Error splitting document: {e}")
            return []
    
    def _split_by_sections(self, text: str) -> List[str]:
        """Split text by major section boundaries"""
        lines = text.split('\n')
        sections = []
        current_section = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line starts a new section
            is_section_start = any(re.match(pattern, line) for pattern in self.section_patterns)
            
            if is_section_start and current_section:
                # Save previous section
                section_text = '\n'.join(current_section)
                if section_text.strip():
                    sections.append(section_text)
                current_section = [line]
            else:
                current_section.append(line)
        
        # Add the last section
        if current_section:
            section_text = '\n'.join(current_section)
            if section_text.strip():
                sections.append(section_text)
        
        return sections if sections else [text]  # Return original if no sections found
    
    def _split_section_into_clauses(self, section_text: str) -> List[str]:
        """Split a section into individual clauses"""
        # If section is short enough, return as single clause
        if len(section_text) <= self.max_clause_length:
            return [section_text]
        
        # Split by sentences and group into clauses
        sentences = self._split_into_sentences(section_text)
        clauses = []
        current_clause = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence would exceed max length, save current clause
            if current_length + sentence_length > self.max_clause_length and current_clause:
                clause_text = ' '.join(current_clause)
                if len(clause_text.strip()) >= self.min_clause_length:
                    clauses.append(clause_text)
                current_clause = [sentence]
                current_length = sentence_length
            else:
                current_clause.append(sentence)
                current_length += sentence_length
        
        # Add the last clause
        if current_clause:
            clause_text = ' '.join(current_clause)
            if len(clause_text.strip()) >= self.min_clause_length:
                clauses.append(clause_text)
        
        return clauses if clauses else [section_text]
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using simple rules"""
        # Simple sentence splitting - can be improved
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _extract_section_number(self, text: str) -> Optional[str]:
        """Extract section number from clause text"""
        for pattern in self.section_patterns:
            match = re.match(pattern, text.strip())
            if match:
                return match.group().strip()
        return None