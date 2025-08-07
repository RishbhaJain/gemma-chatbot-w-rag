"""
RAG Pipeline for Guidance Counselor Chatbot

Main orchestration class that combines document processing, vector storage, and retrieval
"""

import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from .document_processor import DocumentProcessor, ProcessedDocument
from .vector_store import VectorStore
from .retriever import RAGRetriever, RetrievalResult

logger = logging.getLogger(__name__)

class RAGPipeline:
    """Main RAG pipeline that orchestrates all components"""
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        embedding_model: str = "all-MiniLM-L6-v2",
        vector_db_path: str = "./vector_db",
        similarity_threshold: float = 0.7,
        default_k: int = 3
    ):
        # Initialize components
        self.document_processor = DocumentProcessor(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        self.vector_store = VectorStore(
            persist_directory=vector_db_path,
            embedding_model=embedding_model
        )
        
        self.retriever = RAGRetriever(
            vector_store=self.vector_store,
            similarity_threshold=similarity_threshold,
            default_k=default_k
        )
        
        self.config = {
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "embedding_model": embedding_model,
            "vector_db_path": vector_db_path,
            "similarity_threshold": similarity_threshold,
            "default_k": default_k
        }
        
        logger.info("RAG Pipeline initialized successfully")
    
    async def add_document(
        self, 
        pdf_path: str, 
        title_override: Optional[str] = None,
        force_reprocess: bool = False
    ) -> Dict[str, Any]:
        """Add a PDF document to the RAG system"""
        try:
            logger.info(f"Adding document: {pdf_path}")
            
            # Check if file exists
            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            # Generate document ID
            doc_id = self.document_processor.generate_doc_id(pdf_path)
            
            # Check if already processed (unless force reprocess)
            if not force_reprocess:
                existing_doc = self.document_processor.load_processed_document(doc_id)
                if existing_doc:
                    logger.info(f"Document {doc_id} already processed, skipping...")
                    return {
                        "success": True,
                        "doc_id": doc_id,
                        "title": existing_doc.title,
                        "chunks": existing_doc.total_chunks,
                        "status": "already_exists"
                    }
            
            # Process document
            processed_doc = self.document_processor.process_pdf(
                pdf_path=pdf_path,
                title_override=title_override
            )
            
            # Add chunks to vector store
            self.vector_store.add_chunks(processed_doc.chunks)
            
            logger.info(f"Successfully added document {doc_id} with {processed_doc.total_chunks} chunks")
            
            return {
                "success": True,
                "doc_id": processed_doc.doc_id,
                "title": processed_doc.title,
                "chunks": processed_doc.total_chunks,
                "status": "processed"
            }
            
        except Exception as e:
            logger.error(f"Error adding document {pdf_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "pdf_path": pdf_path
            }
    
    async def add_documents_batch(
        self, 
        pdf_paths: List[str], 
        force_reprocess: bool = False
    ) -> Dict[str, Any]:
        """Add multiple PDF documents in batch"""
        try:
            logger.info(f"Processing batch of {len(pdf_paths)} documents")
            
            results = []
            successful = 0
            failed = 0
            
            for pdf_path in pdf_paths:
                result = await self.add_document(
                    pdf_path=pdf_path,
                    force_reprocess=force_reprocess
                )
                results.append(result)
                
                if result["success"]:
                    successful += 1
                else:
                    failed += 1
            
            return {
                "total_documents": len(pdf_paths),
                "successful": successful,
                "failed": failed,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error in batch document processing: {e}")
            return {
                "total_documents": len(pdf_paths),
                "successful": 0,
                "failed": len(pdf_paths),
                "error": str(e)
            }
    
    async def query(
        self, 
        question: str,
        k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        include_metadata: bool = False
    ) -> RetrievalResult:
        """Query the RAG system for relevant context"""
        try:
            logger.info(f"Querying RAG system: {question[:100]}...")
            
            result = await self.retriever.retrieve(
                query=question,
                k=k,
                similarity_threshold=similarity_threshold
            )
            
            # Optionally include detailed metadata
            if not include_metadata:
                # Simplified result without internal metadata
                for chunk in result.source_chunks:
                    if "metadata" in chunk:
                        # Keep only essential metadata
                        essential_metadata = {
                            "title": chunk["metadata"].get("title", ""),
                            "author": chunk["metadata"].get("author", ""),
                            "page_number": chunk["metadata"].get("page_number", ""),
                        }
                        chunk["metadata"] = essential_metadata
            
            return result
            
        except Exception as e:
            logger.error(f"Error querying RAG system: {e}")
            return RetrievalResult(
                context="",
                source_chunks=[],
                total_chunks=0,
                avg_similarity=0.0,
                sources=[]
            )
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the RAG system"""
        try:
            return self.document_processor.list_processed_documents()
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []
    
    def remove_document(self, doc_id: str) -> Dict[str, Any]:
        """Remove a document from the RAG system"""
        try:
            logger.info(f"Removing document: {doc_id}")
            
            # Remove from vector store
            chunks_deleted = self.vector_store.delete_document(doc_id)
            
            # Remove processed files
            base_path = Path("documents")
            metadata_file = base_path / "metadata" / f"{doc_id}_metadata.json"
            chunks_file = base_path / "processed" / f"{doc_id}_chunks.json"
            
            files_deleted = 0
            if metadata_file.exists():
                metadata_file.unlink()
                files_deleted += 1
            
            if chunks_file.exists():
                chunks_file.unlink()
                files_deleted += 1
            
            logger.info(f"Removed document {doc_id}: {chunks_deleted} chunks, {files_deleted} files")
            
            return {
                "success": True,
                "doc_id": doc_id,
                "chunks_deleted": chunks_deleted,
                "files_deleted": files_deleted
            }
            
        except Exception as e:
            logger.error(f"Error removing document {doc_id}: {e}")
            return {
                "success": False,
                "doc_id": doc_id,
                "error": str(e)
            }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        try:
            # Vector store stats
            vector_stats = self.vector_store.get_collection_stats()
            
            # Document processor stats
            documents = self.document_processor.list_processed_documents()
            
            # Calculate document statistics
            total_pages = sum(doc.get("metadata", {}).get("total_pages", 0) for doc in documents)
            unique_authors = len(set(doc.get("metadata", {}).get("author", "") for doc in documents if doc.get("metadata", {}).get("author")))
            
            return {
                "vector_store": vector_stats,
                "documents": {
                    "total_documents": len(documents),
                    "total_pages": total_pages,
                    "unique_authors": unique_authors,
                    "documents_list": documents
                },
                "configuration": self.config,
                "system_health": self.health_check()
            }
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {"error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Perform system health check"""
        try:
            # Check vector store health
            vector_health = self.vector_store.health_check()
            
            # Check document processor
            documents = self.document_processor.list_processed_documents()
            doc_processor_healthy = len(documents) >= 0  # Basic check
            
            # Overall system health
            system_healthy = (
                vector_health.get("status") == "healthy" and
                doc_processor_healthy
            )
            
            return {
                "status": "healthy" if system_healthy else "unhealthy",
                "vector_store": vector_health,
                "document_processor": {
                    "status": "healthy" if doc_processor_healthy else "unhealthy",
                    "documents_available": len(documents)
                },
                "timestamp": json.loads(json.dumps({"timestamp": "now"}))  # Simple timestamp
            }
            
        except Exception as e:
            logger.error(f"Error during health check: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def test_system(self) -> Dict[str, Any]:
        """Run comprehensive system tests"""
        try:
            logger.info("Running RAG system tests...")
            
            test_queries = [
                "How to choose a career?",
                "I'm stressed about exams",
                "What should I study in college?",
                "Family pressure about career choices",
                "How to deal with academic pressure?"
            ]
            
            # Test retrieval
            retrieval_results = await self.retriever.test_retrieval(test_queries)
            
            # Test vector store
            vector_health = self.vector_store.health_check()
            
            # System stats
            stats = self.get_system_stats()
            
            return {
                "test_status": "completed",
                "retrieval_test": retrieval_results,
                "vector_store_health": vector_health,
                "system_stats": stats,
                "recommendations": self._generate_recommendations(stats, retrieval_results)
            }
            
        except Exception as e:
            logger.error(f"Error during system test: {e}")
            return {
                "test_status": "failed",
                "error": str(e)
            }
    
    def _generate_recommendations(self, stats: Dict[str, Any], retrieval_results: Dict[str, Any]) -> List[str]:
        """Generate system optimization recommendations"""
        recommendations = []
        
        try:
            # Check document count
            total_docs = stats.get("documents", {}).get("total_documents", 0)
            if total_docs < 5:
                recommendations.append("Consider adding more guidance counselor documents for better coverage")
            
            # Check retrieval success rate
            successful_retrievals = retrieval_results.get("successful_retrievals", 0)
            total_queries = retrieval_results.get("total_queries", 1)
            success_rate = successful_retrievals / total_queries
            
            if success_rate < 0.8:
                recommendations.append("Consider lowering similarity threshold for better retrieval coverage")
            
            # Check vector store health
            if stats.get("system_health", {}).get("vector_store", {}).get("status") != "healthy":
                recommendations.append("Vector store requires attention - check logs for issues")
            
            # Check chunk count
            total_chunks = stats.get("vector_store", {}).get("total_chunks", 0)
            if total_chunks > 10000:
                recommendations.append("Large number of chunks - consider optimizing chunk size or using filters")
            
        except Exception as e:
            logger.warning(f"Error generating recommendations: {e}")
            recommendations.append("Unable to generate recommendations due to analysis error")
        
        return recommendations
    
    def export_configuration(self) -> Dict[str, Any]:
        """Export current system configuration"""
        return {
            "rag_pipeline_config": self.config,
            "system_stats": self.get_system_stats(),
            "export_timestamp": json.loads(json.dumps({"timestamp": "now"}))
        }
    
    async def import_documents_from_directory(
        self, 
        directory_path: str,
        file_pattern: str = "*.pdf",
        force_reprocess: bool = False
    ) -> Dict[str, Any]:
        """Import all PDF documents from a directory"""
        try:
            directory = Path(directory_path)
            if not directory.exists():
                raise FileNotFoundError(f"Directory not found: {directory_path}")
            
            # Find all PDF files
            pdf_files = list(directory.glob(file_pattern))
            pdf_paths = [str(pdf_file) for pdf_file in pdf_files]
            
            if not pdf_paths:
                return {
                    "total_documents": 0,
                    "successful": 0,
                    "failed": 0,
                    "message": f"No PDF files found in {directory_path}"
                }
            
            # Process batch
            result = await self.add_documents_batch(
                pdf_paths=pdf_paths,
                force_reprocess=force_reprocess
            )
            
            logger.info(f"Imported {result['successful']} documents from {directory_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error importing documents from {directory_path}: {e}")
            return {
                "total_documents": 0,
                "successful": 0,
                "failed": 0,
                "error": str(e)
            } 