"""
Document processing service for PDF text extraction
"""
import pdfplumber
import logging
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Handles PDF text extraction and basic preprocessing"""
    
    def __init__(self):
        pass
    
    def extract_text_from_pdf(self, pdf_path: Path) -> Tuple[bool, str, Optional[str]]:
        """
        Extract text from PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (success, extracted_text, error_message)
        """
        try:
            extracted_text = ""
            
            with pdfplumber.open(pdf_path) as pdf:
                logger.info(f"Processing PDF with {len(pdf.pages)} pages")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            extracted_text += f"\n--- Page {page_num} ---\n"
                            extracted_text += page_text
                            extracted_text += "\n"
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num}: {e}")
                        continue
            
            if not extracted_text.strip():
                return False, "", "No readable text found in PDF. The document might be image-based or corrupted."
            
            # Basic text cleaning
            cleaned_text = self._clean_text(extracted_text)
            
            logger.info(f"Successfully extracted {len(cleaned_text)} characters from PDF")
            return True, cleaned_text, None
            
        except Exception as e:
            error_msg = f"Error processing PDF: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg
    
    def _clean_text(self, text: str) -> str:
        """
        Basic text cleaning and normalization
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('--- Page'):
                cleaned_lines.append(line)
        
        # Join lines and normalize spacing
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Remove multiple consecutive newlines
        while '\n\n\n' in cleaned_text:
            cleaned_text = cleaned_text.replace('\n\n\n', '\n\n')
        
        return cleaned_text.strip()
    
    def validate_pdf(self, pdf_path: Path, max_size_bytes: int) -> Tuple[bool, Optional[str]]:
        """
        Validate PDF file before processing
        
        Args:
            pdf_path: Path to PDF file
            max_size_bytes: Maximum allowed file size
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if file exists
            if not pdf_path.exists():
                return False, "File does not exist"
            
            # Check file size
            file_size = pdf_path.stat().st_size
            if file_size > max_size_bytes:
                size_mb = file_size / (1024 * 1024)
                max_mb = max_size_bytes / (1024 * 1024)
                return False, f"File too large: {size_mb:.1f}MB (max: {max_mb}MB)"
            
            # Check if it's a valid PDF by trying to open it
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) == 0:
                    return False, "PDF has no pages"
            
            return True, None
            
        except Exception as e:
            return False, f"Invalid PDF file: {str(e)}"