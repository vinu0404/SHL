from typing import List, Union
import google.generativeai as genai
from app.config import settings
from app.utils.logger import get_logger
from app.utils.helpers import chunk_list

logger = get_logger("embedding_service")


class EmbeddingService:
    """Service for generating embeddings using Gemini"""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_EMBEDDING_MODEL
        self.batch_size = settings.EMBEDDING_BATCH_SIZE
        self._initialized = False
    
    def initialize(self):
        """Initialize Gemini API for embeddings"""
        if self._initialized:
            return
        
        try:
            genai.configure(api_key=self.api_key)
            self._initialized = True
            logger.info(f"Embedding service initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        if not self._initialized:
            self.initialize()
        
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )
            
            embedding = result['embedding']
            logger.debug(f"Generated embedding of dimension {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def generate_embeddings(
        self,
        texts: List[str],
        batch_size: int = None
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        if not self._initialized:
            self.initialize()
        
        if not texts:
            return []
        
        batch_size = batch_size or self.batch_size
        embeddings = []
        
        # Process in batches
        text_batches = chunk_list(texts, batch_size)
        
        for batch_idx, batch in enumerate(text_batches):
            try:
                logger.debug(f"Processing batch {batch_idx + 1}/{len(text_batches)}")
                
                # Generate embeddings for batch
                for text in batch:
                    result = genai.embed_content(
                        model=self.model_name,
                        content=text,
                        task_type="retrieval_document"
                    )
                    embeddings.append(result['embedding'])
                
            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch {batch_idx}: {e}")
                # Add zero vectors as fallback
                for _ in batch:
                    embeddings.append([0.0] * 768)  # Default dimension
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings
    
    async def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a query (uses retrieval_query task type)
        
        Args:
            query: Query text
            
        Returns:
            Query embedding vector
        """
        if not self._initialized:
            self.initialize()
        
        try:
            result = genai.embed_content(
                model=self.model_name,
                content=query,
                task_type="retrieval_query"
            )
            
            embedding = result['embedding']
            logger.debug(f"Generated query embedding of dimension {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise
    
    async def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score
        """
        import numpy as np
        
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Compute cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to compute similarity: {e}")
            return 0.0
    
    async def find_most_similar(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[List[float]],
        top_k: int = 10
    ) -> List[tuple]:
        """
        Find most similar embeddings to query
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embeddings
            top_k: Number of top results to return
            
        Returns:
            List of (index, similarity_score) tuples
        """
        import numpy as np
        
        try:
            query_vec = np.array(query_embedding)
            candidate_matrix = np.array(candidate_embeddings)
            
            # Compute similarities
            similarities = np.dot(candidate_matrix, query_vec) / (
                np.linalg.norm(candidate_matrix, axis=1) * np.linalg.norm(query_vec)
            )
            
            # Get top k indices
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            results = [(int(idx), float(similarities[idx])) for idx in top_indices]
            
            logger.debug(f"Found {len(results)} most similar embeddings")
            return results
            
        except Exception as e:
            logger.error(f"Failed to find similar embeddings: {e}")
            return []
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model"""
        # Gemini embedding-001 produces 768-dimensional embeddings
        return 768


# Global embedding service instance
embedding_service = EmbeddingService()


def get_embedding_service() -> EmbeddingService:
    """Get embedding service instance"""
    if not embedding_service._initialized:
        embedding_service.initialize()
    return embedding_service