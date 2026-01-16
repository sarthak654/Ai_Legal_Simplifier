"""
Embeddings and vector store utilities using FAISS and Sentence Transformers
"""
import faiss
import numpy as np
import pickle
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class EmbeddingManager:
    """Manages embeddings and FAISS vector store for RAG"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", vector_store_dir: Path = None):
        self.model_name = model_name
        self.vector_store_dir = vector_store_dir or Path("vector_store")
        self.vector_store_dir.mkdir(exist_ok=True)
        
        # Initialize sentence transformer
        try:
            self.encoder = SentenceTransformer(model_name)
            self.embedding_dim = self.encoder.get_sentence_embedding_dimension()
            logger.info(f"Loaded embedding model: {model_name} (dim: {self.embedding_dim})")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
        
        # FAISS index
        self.index = None
        self.clause_metadata = {}  # Store clause info by index
    
    def create_embeddings(self, clauses: List[Dict]) -> Tuple[bool, Optional[str]]:
        """
        Create embeddings for all clauses and build FAISS index
        
        Args:
            clauses: List of clause dictionaries
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if not clauses:
                return False, "No clauses provided"
            
            # Extract texts for embedding
            texts = []
            metadata = {}
            
            for i, clause in enumerate(clauses):
                # Combine original and simplified text for better retrieval
                text_to_embed = clause.get('original_text', '')
                simplified = clause.get('simplified_text', '')
                if simplified:
                    text_to_embed += f" {simplified}"
                
                texts.append(text_to_embed)
                metadata[i] = {
                    'clause_id': clause.get('id', i),
                    'original_text': clause.get('original_text', ''),
                    'simplified_text': clause.get('simplified_text', ''),
                    'risk_level': clause.get('risk_level', 'LOW'),
                    'section_number': clause.get('section_number')
                }
            
            # Generate embeddings
            logger.info(f"Generating embeddings for {len(texts)} clauses...")
            embeddings = self.encoder.encode(texts, show_progress_bar=True)
            
            # Create FAISS index
            self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for cosine similarity
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Add to index
            self.index.add(embeddings.astype('float32'))
            self.clause_metadata = metadata
            
            logger.info(f"Created FAISS index with {self.index.ntotal} vectors")
            return True, None
            
        except Exception as e:
            error_msg = f"Error creating embeddings: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def search_similar_clauses(self, query: str, top_k: int = 5, min_score: float = 0.3) -> List[Dict]:
        """
        Search for clauses similar to the query
        
        Args:
            query: Search query
            top_k: Number of results to return
            min_score: Minimum similarity score
            
        Returns:
            List of similar clauses with metadata and scores
        """
        try:
            if self.index is None:
                logger.error("FAISS index not initialized")
                return []
            
            # Generate query embedding
            query_embedding = self.encoder.encode([query])
            faiss.normalize_L2(query_embedding)
            
            # Search
            scores, indices = self.index.search(query_embedding.astype('float32'), top_k)
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if score >= min_score and idx in self.clause_metadata:
                    result = self.clause_metadata[idx].copy()
                    result['similarity_score'] = float(score)
                    results.append(result)
            
            logger.info(f"Found {len(results)} similar clauses for query")
            return results
            
        except Exception as e:
            logger.error(f"Error searching clauses: {e}")
            return []
    
    def save_index(self, document_id: str) -> Tuple[bool, Optional[str]]:
        """
        Save FAISS index and metadata to disk
        
        Args:
            document_id: Unique document identifier
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if self.index is None:
                return False, "No index to save"
            
            index_path = self.vector_store_dir / f"{document_id}.index"
            metadata_path = self.vector_store_dir / f"{document_id}.metadata"
            
            # Save FAISS index
            faiss.write_index(self.index, str(index_path))
            
            # Save metadata
            with open(metadata_path, 'wb') as f:
                pickle.dump(self.clause_metadata, f)
            
            logger.info(f"Saved index and metadata for document {document_id}")
            return True, None
            
        except Exception as e:
            error_msg = f"Error saving index: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def load_index(self, document_id: str) -> Tuple[bool, Optional[str]]:
        """
        Load FAISS index and metadata from disk
        
        Args:
            document_id: Unique document identifier
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            index_path = self.vector_store_dir / f"{document_id}.index"
            metadata_path = self.vector_store_dir / f"{document_id}.metadata"
            
            if not index_path.exists() or not metadata_path.exists():
                return False, f"Index files not found for document {document_id}"
            
            # Load FAISS index
            self.index = faiss.read_index(str(index_path))
            
            # Load metadata
            with open(metadata_path, 'rb') as f:
                self.clause_metadata = pickle.load(f)
            
            logger.info(f"Loaded index for document {document_id} ({self.index.ntotal} vectors)")
            return True, None
            
        except Exception as e:
            error_msg = f"Error loading index: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def get_clause_by_id(self, clause_id: int) -> Optional[Dict]:
        """Get clause metadata by clause ID"""
        for metadata in self.clause_metadata.values():
            if metadata.get('clause_id') == clause_id:
                return metadata
        return None
    
    def delete_index(self, document_id: str) -> bool:
        """Delete saved index files"""
        try:
            index_path = self.vector_store_dir / f"{document_id}.index"
            metadata_path = self.vector_store_dir / f"{document_id}.metadata"
            
            if index_path.exists():
                index_path.unlink()
            if metadata_path.exists():
                metadata_path.unlink()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting index: {e}")
            return False