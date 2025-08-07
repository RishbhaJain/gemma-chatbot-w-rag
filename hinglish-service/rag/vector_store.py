"""
Vector Store for RAG System

Handles embedding generation, storage, and similarity search using ChromaDB
"""

import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np

from .document_processor import DocumentChunk

logger = logging.getLogger(__name__)

class VectorStore:
    """Manages document embeddings and similarity search"""
    
    def __init__(
        self, 
        persist_directory: str = "./vector_db",
        embedding_model: str = "all-MiniLM-L6-v2",
        collection_name: str = "guidance_docs"
    ):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(exist_ok=True)
        
        self.embedding_model_name = embedding_model
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except ValueError:
            # Collection doesn't exist, create it
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "Guidance counselor documents for RAG"}
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        try:
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Add document chunks to the vector store"""
        try:
            if not chunks:
                logger.warning("No chunks provided to add to vector store")
                return
            
            logger.info(f"Adding {len(chunks)} chunks to vector store")
            
            # Prepare data for ChromaDB
            texts = [chunk.text for chunk in chunks]
            ids = [chunk.chunk_id for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]
            
            # Generate embeddings
            logger.info("Generating embeddings...")
            embeddings = self.generate_embeddings(texts)
            
            # Add to collection
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"Successfully added {len(chunks)} chunks to vector store")
            
        except Exception as e:
            logger.error(f"Error adding chunks to vector store: {e}")
            raise
    
    def search_similar(
        self, 
        query: str, 
        k: int = 5,
        similarity_threshold: float = 0.0,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar chunks based on query"""
        try:
            logger.debug(f"Searching for similar chunks: query='{query[:100]}...', k={k}")
            
            # Generate query embedding
            query_embedding = self.generate_embeddings([query])[0]
            
            # Prepare where clause for metadata filtering
            where_clause = metadata_filter if metadata_filter else None
            
            # Search in collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
            
            # Process results
            similar_chunks = []
            if results['documents'] and results['documents'][0]:
                documents = results['documents'][0]
                metadatas = results['metadatas'][0]
                distances = results['distances'][0]
                
                for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                    # Convert distance to similarity score (ChromaDB uses cosine distance)
                    similarity = 1 - distance
                    
                    # Apply similarity threshold
                    if similarity >= similarity_threshold:
                        similar_chunks.append({
                            "text": doc,
                            "metadata": metadata,
                            "similarity": similarity,
                            "rank": i + 1
                        })
            
            logger.debug(f"Found {len(similar_chunks)} similar chunks above threshold {similarity_threshold}")
            return similar_chunks
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {e}")
            return []
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific chunk by ID"""
        try:
            results = self.collection.get(
                ids=[chunk_id],
                include=["documents", "metadatas"]
            )
            
            if results['documents'] and results['documents'][0]:
                return {
                    "text": results['documents'][0],
                    "metadata": results['metadatas'][0]
                }
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving chunk {chunk_id}: {e}")
            return None
    
    def delete_document(self, doc_id: str) -> int:
        """Delete all chunks for a specific document"""
        try:
            # Find all chunks for this document
            results = self.collection.get(
                where={"doc_id": doc_id},
                include=["documents"]
            )
            
            if results['ids']:
                chunk_ids = results['ids']
                self.collection.delete(ids=chunk_ids)
                logger.info(f"Deleted {len(chunk_ids)} chunks for document {doc_id}")
                return len(chunk_ids)
            else:
                logger.warning(f"No chunks found for document {doc_id}")
                return 0
                
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return 0
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection"""
        try:
            count = self.collection.count()
            
            # Get sample of documents to analyze
            sample_results = self.collection.get(
                limit=min(100, count),
                include=["metadatas"]
            )
            
            # Analyze document types
            doc_ids = set()
            authors = set()
            titles = set()
            
            for metadata in sample_results.get('metadatas', []):
                if metadata:
                    doc_ids.add(metadata.get('doc_id', ''))
                    authors.add(metadata.get('author', ''))
                    titles.add(metadata.get('title', ''))
            
            return {
                "total_chunks": count,
                "unique_documents": len(doc_ids),
                "unique_authors": len(authors),
                "unique_titles": len(titles),
                "embedding_model": self.embedding_model_name,
                "collection_name": self.collection_name
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}
    
    def reset_collection(self) -> None:
        """Reset the entire collection (use with caution!)"""
        try:
            logger.warning("Resetting vector store collection - all data will be lost!")
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Guidance counselor documents for RAG"}
            )
            logger.info("Vector store collection reset successfully")
            
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
            raise
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health of the vector store"""
        try:
            # Test basic operations
            health_status = {
                "status": "healthy",
                "client_connected": True,
                "collection_accessible": True,
                "embedding_model_loaded": True,
                "issues": []
            }
            
            # Test client connection
            try:
                self.client.heartbeat()
            except Exception as e:
                health_status["client_connected"] = False
                health_status["issues"].append(f"Client connection failed: {e}")
            
            # Test collection access
            try:
                self.collection.count()
            except Exception as e:
                health_status["collection_accessible"] = False
                health_status["issues"].append(f"Collection access failed: {e}")
            
            # Test embedding model
            try:
                self.generate_embeddings(["test"])
            except Exception as e:
                health_status["embedding_model_loaded"] = False
                health_status["issues"].append(f"Embedding model failed: {e}")
            
            # Overall status
            if health_status["issues"]:
                health_status["status"] = "unhealthy"
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error during health check: {e}")
            return {
                "status": "unhealthy",
                "issues": [f"Health check failed: {e}"]
            } 