"""
Risk detection service using rule-based keyword analysis
"""
import re
import logging
from typing import List, Tuple, Dict
from ..models import RiskLevel
from ..config import RISK_KEYWORDS

logger = logging.getLogger(__name__)

class RiskDetector:
    """Detects risk levels in legal clauses using keyword-based rules"""
    
    def __init__(self):
        self.risk_keywords = RISK_KEYWORDS
        
        # Additional context patterns that increase risk
        self.high_risk_patterns = [
            r'shall be liable for.*damages',
            r'liquidated damages.*\$[\d,]+',
            r'immediate termination',
            r'without.*notice',
            r'indemnify.*against.*claims',
            r'non-compete.*period.*\d+.*years?',
            r'confidential.*perpetuity',
            r'injunctive relief'
        ]
        
        self.medium_risk_patterns = [
            r'material breach',
            r'cure.*within.*\d+.*days',
            r'written notice.*required',
            r'intellectual property.*ownership',
            r'assignment.*rights'
        ]
    
    def analyze_risk(self, clause_text: str) -> Tuple[RiskLevel, List[str]]:
        """
        Analyze risk level of a legal clause
        
        Args:
            clause_text: Text of the legal clause
            
        Returns:
            Tuple of (risk_level, list_of_reasons)
        """
        try:
            text_lower = clause_text.lower()
            reasons = []
            
            # Check for high-risk patterns first
            high_risk_score = 0
            medium_risk_score = 0
            low_risk_score = 0
            
            # Pattern-based detection (highest priority)
            for pattern in self.high_risk_patterns:
                if re.search(pattern, text_lower):
                    high_risk_score += 3
                    reasons.append(f"Contains high-risk pattern: {pattern}")
            
            for pattern in self.medium_risk_patterns:
                if re.search(pattern, text_lower):
                    medium_risk_score += 2
                    reasons.append(f"Contains medium-risk pattern")
            
            # Keyword-based detection
            high_keywords_found = []
            medium_keywords_found = []
            low_keywords_found = []
            
            for keyword in self.risk_keywords["HIGH"]:
                if keyword in text_lower:
                    high_keywords_found.append(keyword)
                    high_risk_score += 2
            
            for keyword in self.risk_keywords["MEDIUM"]:
                if keyword in text_lower:
                    medium_keywords_found.append(keyword)
                    medium_risk_score += 1
            
            for keyword in self.risk_keywords["LOW"]:
                if keyword in text_lower:
                    low_keywords_found.append(keyword)
                    low_risk_score += 0.5
            
            # Add keyword-based reasons
            if high_keywords_found:
                reasons.append(f"High-risk keywords: {', '.join(high_keywords_found[:3])}")
            if medium_keywords_found:
                reasons.append(f"Medium-risk keywords: {', '.join(medium_keywords_found[:3])}")
            
            # Determine final risk level
            if high_risk_score >= 2:
                risk_level = RiskLevel.HIGH
            elif medium_risk_score >= 2 or high_risk_score >= 1:
                risk_level = RiskLevel.MEDIUM
            else:
                risk_level = RiskLevel.LOW
                if not reasons:
                    reasons.append("Standard legal language with minimal risk indicators")
            
            # Additional context-based risk assessment
            additional_reasons = self._assess_contextual_risk(clause_text, risk_level)
            reasons.extend(additional_reasons)
            
            logger.debug(f"Risk analysis: {risk_level.value} - {len(reasons)} reasons")
            return risk_level, reasons[:5]  # Limit to top 5 reasons
            
        except Exception as e:
            logger.error(f"Error in risk analysis: {e}")
            return RiskLevel.LOW, ["Error in risk analysis"]
    
    def _assess_contextual_risk(self, text: str, current_risk: RiskLevel) -> List[str]:
        """Assess additional contextual risk factors"""
        additional_reasons = []
        text_lower = text.lower()
        
        # Financial implications
        if re.search(r'\$[\d,]+', text) or 'monetary' in text_lower or 'financial' in text_lower:
            additional_reasons.append("Contains financial implications")
        
        # Time-sensitive obligations
        if re.search(r'\d+.*days?|immediately|forthwith|without delay', text_lower):
            additional_reasons.append("Contains time-sensitive obligations")
        
        # Broad scope language
        broad_terms = ['all', 'any', 'every', 'entire', 'complete', 'unlimited', 'perpetual']
        if any(term in text_lower for term in broad_terms):
            additional_reasons.append("Contains broad scope language")
        
        # Exclusive or restrictive language
        restrictive_terms = ['exclusively', 'solely', 'only', 'prohibited', 'forbidden', 'restricted']
        if any(term in text_lower for term in restrictive_terms):
            additional_reasons.append("Contains restrictive language")
        
        # Waiver of rights
        if 'waive' in text_lower or 'waiver' in text_lower:
            additional_reasons.append("May involve waiver of rights")
        
        return additional_reasons
    
    def get_risk_summary(self, clauses: List[Dict]) -> Dict[str, int]:
        """
        Get summary of risk levels across all clauses
        
        Args:
            clauses: List of clause dictionaries with risk_level
            
        Returns:
            Dictionary with risk level counts
        """
        summary = {
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0,
            "total": len(clauses)
        }
        
        for clause in clauses:
            risk_level = clause.get('risk_level', RiskLevel.LOW)
            if isinstance(risk_level, RiskLevel):
                summary[risk_level.value] += 1
            else:
                summary[str(risk_level)] += 1
        
        return summary
    
    def get_high_risk_clauses(self, clauses: List[Dict]) -> List[Dict]:
        """Get only the high-risk clauses"""
        return [
            clause for clause in clauses 
            if clause.get('risk_level') == RiskLevel.HIGH
        ]