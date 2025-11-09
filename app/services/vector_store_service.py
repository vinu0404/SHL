from typing import List, Dict, Any, Optional
from datetime import datetime
from app.database.chroma_db import get_chroma_client
from app.services.embedding_service import get_embedding_service
from app.models.assessment import Assessment
from app.utils.logger import get_logger
from app.utils.helpers import chunk_list

logger = get_logger("vector_store_service")


class VectorStoreService:
    """Service for managing assessment vectors in ChromaDB"""
    
    def __init__(self):
        self.chroma_manager = get_chroma_client()
        self.embedding_service = get_embedding_service()
    
    async def index_assessments(
        self,
        assessments: Dict[str, Dict[str, Any]],
        batch_size: int = 10
    ) -> int:
        """
        Index assessments into vector store
        
        Args:
            assessments: Dictionary of assessments (url -> data)
            batch_size: Batch size for embedding generation
            
        Returns:
            Number of assessments indexed
        """
        try:
            logger.info(f"Starting to index {len(assessments)} assessments")
            
            # Convert to Assessment objects
            assessment_objects = []
            for url, data in assessments.items():
                try:
                    assessment = Assessment(**data)
                    assessment_objects.append(assessment)
                except Exception as e:
                    logger.warning(f"Failed to parse assessment {url}: {e}")
                    continue
            
            if not assessment_objects:
                logger.warning("No valid assessments to index")
                return 0
            
            # Prepare data for indexing
            documents = []
            metadatas = []
            ids = []
            
            for assessment in assessment_objects:
                # Create document text for embedding
                doc_text = assessment.to_embedding_text()
                documents.append(doc_text)
                
                # Create metadata
                metadata = {
                    "name": assessment.name,
                    "url": assessment.url,
                    "test_type": ",".join(assessment.test_type),
                    "remote_support": assessment.remote_support,
                    "adaptive_support": assessment.adaptive_support,
                    "duration": assessment.duration or -1,
                    "job_levels": assessment.job_levels,
                    "languages": assessment.languages,
                    "description": assessment.description[:500]  # Limit length
                }
                metadatas.append(metadata)
                
                # Use URL as unique ID (normalized)
                doc_id = assessment.url.replace("https://", "").replace("/", "_")
                ids.append(doc_id)
            
            # Generate embeddings in batches
            logger.info(f"Generating embeddings for {len(documents)} documents")
            embeddings = await self.embedding_service.generate_embeddings(
                documents,
                batch_size=batch_size
            )
            
            # Add to ChromaDB in batches
            batch_size = 100  # ChromaDB batch size
            doc_batches = chunk_list(documents, batch_size)
            emb_batches = chunk_list(embeddings, batch_size)
            meta_batches = chunk_list(metadatas, batch_size)
            id_batches = chunk_list(ids, batch_size)
            
            for i, (docs, embs, metas, batch_ids) in enumerate(
                zip(doc_batches, emb_batches, meta_batches, id_batches)
            ):
                logger.info(f"Indexing batch {i + 1}/{len(doc_batches)}")
                self.chroma_manager.add_documents(
                    documents=docs,
                    embeddings=embs,
                    metadatas=metas,
                    ids=batch_ids
                )
            
            # Data is auto-persisted with PersistentClient
            
            logger.info(f"Successfully indexed {len(assessment_objects)} assessments")
            return len(assessment_objects)
            
        except Exception as e:
            logger.error(f"Failed to index assessments: {e}")
            raise
    
    async def search_assessments(
        self,
        query: str,
        top_k: int = 15,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant assessments
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of matching assessments with scores
        """
        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.generate_query_embedding(query)
            
            # Search in ChromaDB
            results = self.chroma_manager.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters
            )
            
            # Parse results
            assessments = []
            
            if results and results['ids'] and len(results['ids']) > 0:
                for i in range(len(results['ids'][0])):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i]
                    
                    # Convert distance to similarity score (cosine distance to similarity)
                    similarity_score = 1 - distance
                    
                    # Parse test types back to list
                    test_types = metadata.get('test_type', '').split(',')
                    test_types = [t.strip() for t in test_types if t.strip()]
                    
                    assessment_data = {
                        "name": metadata.get('name', ''),
                        "url": metadata.get('url', ''),
                        "test_type": test_types,
                        "remote_support": metadata.get('remote_support', 'No'),
                        "adaptive_support": metadata.get('adaptive_support', 'No'),
                        "duration": metadata.get('duration', -1),
                        "job_levels": metadata.get('job_levels', ''),
                        "languages": metadata.get('languages', ''),
                        "description": metadata.get('description', ''),
                        "similarity_score": similarity_score
                    }
                    
                    # Handle duration of -1 (unknown)
                    if assessment_data['duration'] == -1:
                        assessment_data['duration'] = None
                    
                    assessments.append(assessment_data)
            
            logger.info(f"Found {len(assessments)} assessments for query")
            return assessments
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    async def get_assessment_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get specific assessment by URL
        
        Args:
            url: Assessment URL
            
        Returns:
            Assessment data or None
        """
        try:
            doc_id = url.replace("https://", "").replace("/", "_")
            results = self.chroma_manager.get_by_ids([doc_id])
            
            if results and results['ids']:
                metadata = results['metadatas'][0]
                test_types = metadata.get('test_type', '').split(',')
                test_types = [t.strip() for t in test_types if t.strip()]
                
                return {
                    "name": metadata.get('name', ''),
                    "url": metadata.get('url', ''),
                    "test_type": test_types,
                    "remote_support": metadata.get('remote_support', 'No'),
                    "adaptive_support": metadata.get('adaptive_support', 'No'),
                    "duration": metadata.get('duration') if metadata.get('duration') != -1 else None,
                    "job_levels": metadata.get('job_levels', ''),
                    "languages": metadata.get('languages', ''),
                    "description": metadata.get('description', ''),
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get assessment by URL: {e}")
            return None
    
    async def filter_by_test_type(
        self,
        test_types: List[str],
        top_k: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get assessments filtered by test type
        
        Args:
            test_types: List of test types to filter by
            top_k: Maximum number of results
            
        Returns:
            List of matching assessments
        """
        try:
            # Create a generic query for filtering
            query = f"Assessments for {', '.join(test_types)}"
            
            # Search with broader results
            assessments = await self.search_assessments(
                query=query,
                top_k=top_k
            )
            
            # Further filter by test type
            filtered = []
            for assessment in assessments:
                assessment_types = [t.lower() for t in assessment.get('test_type', [])]
                if any(req_type.lower() in ' '.join(assessment_types) for req_type in test_types):
                    filtered.append(assessment)
            
            return filtered
            
        except Exception as e:
            logger.error(f"Failed to filter by test type: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store
        
        Returns:
            Statistics dictionary
        """
        try:
            count = self.chroma_manager.count_documents()
            
            return {
                "total_assessments": count,
                "collection_name": self.chroma_manager.collection_name,
                "last_updated": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}
    
    async def clear_collection(self):
        """Clear all documents from the collection"""
        try:
            self.chroma_manager.recreate_collection()
            logger.info("Collection cleared")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            raise


# Global vector store service instance
vector_store_service = VectorStoreService()


def get_vector_store_service() -> VectorStoreService:
    """Get vector store service instance"""
    return vector_store_service