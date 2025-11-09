from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("chroma_db")


class ChromaDBManager:
    """ChromaDB vector store manager"""
    
    def __init__(self, persist_directory: str = None, collection_name: str = None):
        self.persist_directory = persist_directory or settings.CHROMA_DB_PATH
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        self.client = None
        self.collection = None
        self._initialized = False
    
    def initialize(self):
        """Initialize ChromaDB client and collection"""
        if self._initialized:
            logger.info("ChromaDB already initialized")
            return
        
        try:
            # Ensure directory exists
            persist_path = Path(self.persist_directory)
            persist_path.mkdir(parents=True, exist_ok=True)
            
            # Create ChromaDB client using new API
            self.client = chromadb.PersistentClient(
                path=str(persist_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"Loaded existing collection: {self.collection_name}")
            except Exception:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "SHL Assessment catalog"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
            
            self._initialized = True
            logger.info(f"ChromaDB initialized at {self.persist_directory}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ):
        """
        Add documents to collection
        
        Args:
            documents: List of document texts
            embeddings: List of embedding vectors
            metadatas: List of metadata dictionaries
            ids: List of unique document IDs
        """
        if not self._initialized:
            self.initialize()
        
        try:
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(documents)} documents to collection")
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query collection with embeddings
        
        Args:
            query_embeddings: Query embedding vectors
            n_results: Number of results to return
            where: Metadata filter
            where_document: Document content filter
            
        Returns:
            Query results
        """
        if not self._initialized:
            self.initialize()
        
        try:
            results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=["documents", "metadatas", "distances"]
            )
            
            logger.debug(f"Query returned {len(results['ids'][0])} results")
            return results
            
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise
    
    def get_by_ids(self, ids: List[str]) -> Dict[str, Any]:
        """
        Get documents by IDs
        
        Args:
            ids: List of document IDs
            
        Returns:
            Documents with metadata
        """
        if not self._initialized:
            self.initialize()
        
        try:
            results = self.collection.get(
                ids=ids,
                include=["documents", "metadatas"]
            )
            return results
        except Exception as e:
            logger.error(f"Failed to get documents by IDs: {e}")
            raise
    
    def delete_collection(self):
        """Delete the collection"""
        if not self._initialized:
            self.initialize()
        
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = None
            logger.warning(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete collection: {e}")
            raise
    
    def recreate_collection(self):
        """Delete and recreate collection"""
        try:
            self.delete_collection()
        except Exception:
            pass
        
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"description": "SHL Assessment catalog"}
        )
        logger.info(f"Recreated collection: {self.collection_name}")
    
    def count_documents(self) -> int:
        """Get count of documents in collection"""
        if not self._initialized:
            self.initialize()
        
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Failed to count documents: {e}")
            return 0
    
    def update_documents(
        self,
        ids: List[str],
        documents: Optional[List[str]] = None,
        embeddings: Optional[List[List[float]]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Update existing documents
        
        Args:
            ids: Document IDs to update
            documents: Updated document texts
            embeddings: Updated embeddings
            metadatas: Updated metadata
        """
        if not self._initialized:
            self.initialize()
        
        try:
            self.collection.update(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logger.info(f"Updated {len(ids)} documents")
        except Exception as e:
            logger.error(f"Failed to update documents: {e}")
            raise
    
    def delete_documents(self, ids: List[str]):
        """Delete documents by IDs"""
        if not self._initialized:
            self.initialize()
        
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents")
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            raise
    
    def persist(self):
        """Persist collection to disk - Auto-handled by PersistentClient"""
        # PersistentClient automatically persists changes
        logger.info("ChromaDB changes auto-persisted")


# Global ChromaDB instance
chroma_manager = ChromaDBManager()


def get_chroma_client() -> ChromaDBManager:
    """Get ChromaDB manager instance"""
    if not chroma_manager._initialized:
        chroma_manager.initialize()
    return chroma_manager


def init_chroma():
    """Initialize ChromaDB on startup"""
    chroma_manager.initialize()
    logger.info("ChromaDB initialization complete")


async def close_chroma():
    """Close ChromaDB on shutdown"""
    # PersistentClient handles cleanup automatically
    logger.info("ChromaDB closed")