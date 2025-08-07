"""
RAG Retriever for Guidance Counselor Chatbot

Handles query processing, context retrieval, and result ranking
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .vector_store import VectorStore

logger = logging.getLogger(__name__)

@dataclass
class RetrievalResult:
    """Represents a retrieval result with context and metadata"""
    context: str
    source_chunks: List[Dict[str, Any]]
    total_chunks: int
    avg_similarity: float
    sources: List[str]

class RAGRetriever:
    """Retrieves relevant context for user queries"""
    
    def __init__(
        self,
        vector_store: VectorStore,
        default_k: int = 3,
        similarity_threshold: float = 0.7,
        max_context_length: int = 2000
    ):
        self.vector_store = vector_store
        self.default_k = default_k
        self.similarity_threshold = similarity_threshold
        self.max_context_length = max_context_length
    
    def _preprocess_query(self, query: str) -> str:
        """Preprocess the query for better retrieval"""
        # Remove extra whitespace and normalize
        query = " ".join(query.strip().split())
        
        # Add context hints for better retrieval
        guidance_keywords = [
            "study", "career", "college", "exam", "stress", "anxiety",
            "family", "friends", "future", "job", "course", "subject"
        ]
        
        query_lower = query.lower()
        has_guidance_context = any(keyword in query_lower for keyword in guidance_keywords)
        
        if not has_guidance_context:
            # Add guidance context to generic queries
            query = f"guidance counselor advice for {query}"
        
        return query
    
    def _create_metadata_filter(self, query: str) -> Optional[Dict[str, Any]]:
        """Create metadata filter based on query content"""
        query_lower = query.lower()
        
        # Topic-based filtering
        filters = {}
        
        # Age/Grade level filtering
        if any(term in query_lower for term in ["high school", "12th", "class 12", "senior"]):
            filters["grade_level"] = "high_school"
        elif any(term in query_lower for term in ["college", "university", "undergraduate"]):
            filters["grade_level"] = "college"
        
        # Subject area filtering
        if any(term in query_lower for term in ["career", "job", "profession", "work"]):
            filters["topic"] = "career_guidance"
        elif any(term in query_lower for term in ["study", "exam", "academic", "learning"]):
            filters["topic"] = "academic_support"
        elif any(term in query_lower for term in ["stress", "anxiety", "mental", "emotional"]):
            filters["topic"] = "emotional_support"
        
        return filters if filters else None
    
    def _rank_chunks(self, chunks: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Rank chunks based on relevance and quality"""
        if not chunks:
            return chunks
        
        # Add relevance scoring
        for chunk in chunks:
            chunk["relevance_score"] = chunk["similarity"]
            
            # Boost score for certain indicators
            text = chunk["text"].lower()
            query_lower = query.lower()
            
            # Boost if chunk contains query terms
            query_terms = set(query_lower.split())
            text_terms = set(text.split())
            term_overlap = len(query_terms.intersection(text_terms))
            chunk["relevance_score"] += (term_overlap / len(query_terms)) * 0.1
            
            # Boost for guidance-specific content
            guidance_indicators = [
                "guidance", "counselor", "advice", "recommend", "suggest",
                "should", "consider", "important", "help", "support"
            ]
            indicator_count = sum(1 for indicator in guidance_indicators if indicator in text)
            chunk["relevance_score"] += indicator_count * 0.05
            
            # Boost for complete sentences and paragraphs
            if len(chunk["text"]) > 100 and "." in chunk["text"]:
                chunk["relevance_score"] += 0.05
        
        # Sort by relevance score
        return sorted(chunks, key=lambda x: x["relevance_score"], reverse=True)
    
    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into coherent context"""
        if not chunks:
            return ""
        
        context_parts = []
        current_length = 0
        
        for i, chunk in enumerate(chunks):
            text = chunk["text"].strip()
            
            # Check if adding this chunk would exceed max length
            if current_length + len(text) > self.max_context_length and context_parts:
                break
            
            # Format chunk with source info
            metadata = chunk.get("metadata", {})
            title = metadata.get("title", "Unknown Source")
            page = metadata.get("page_number")
            
            source_info = f"[Source: {title}"
            if page:
                source_info += f", Page {page}"
            source_info += "]"
            
            formatted_chunk = f"{source_info}\n{text}\n"
            context_parts.append(formatted_chunk)
            current_length += len(formatted_chunk)
        
        return "\n".join(context_parts)
    
    def _extract_sources(self, chunks: List[Dict[str, Any]]) -> List[str]:
        """Extract unique sources from chunks"""
        sources = set()
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            title = metadata.get("title", "Unknown Source")
            author = metadata.get("author", "")
            
            if author:
                source = f"{title} by {author}"
            else:
                source = title
            
            sources.add(source)
        
        return list(sources)
    
    async def retrieve(
        self, 
        query: str, 
        k: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> RetrievalResult:
        """Retrieve relevant context for a query"""
        try:
            logger.info(f"Retrieving context for query: {query[:100]}...")
            
            # Use defaults if not specified
            k = k or self.default_k
            similarity_threshold = similarity_threshold or self.similarity_threshold
            
            # Preprocess query
            processed_query = self._preprocess_query(query)
            logger.debug(f"Processed query: {processed_query}")
            
            # Create metadata filter
            metadata_filter = self._create_metadata_filter(query)
            logger.debug(f"Metadata filter: {metadata_filter}")
            
            # Search for similar chunks
            similar_chunks = self.vector_store.search_similar(
                query=processed_query,
                k=k * 2,  # Get more chunks for better ranking
                similarity_threshold=similarity_threshold,
                metadata_filter=metadata_filter
            )
            
            if not similar_chunks:
                logger.warning(f"No relevant chunks found for query: {query}")
                return RetrievalResult(
                    context="",
                    source_chunks=[],
                    total_chunks=0,
                    avg_similarity=0.0,
                    sources=[]
                )
            
            # Rank chunks
            ranked_chunks = self._rank_chunks(similar_chunks, query)
            
            # Take top k chunks after ranking
            final_chunks = ranked_chunks[:k]
            
            # Format context
            context = self._format_context(final_chunks)
            
            # Extract sources
            sources = self._extract_sources(final_chunks)
            
            # Calculate average similarity
            avg_similarity = sum(chunk["similarity"] for chunk in final_chunks) / len(final_chunks)
            
            result = RetrievalResult(
                context=context,
                source_chunks=final_chunks,
                total_chunks=len(final_chunks),
                avg_similarity=avg_similarity,
                sources=sources
            )
            
            logger.info(f"Retrieved {len(final_chunks)} chunks with avg similarity {avg_similarity:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Error during retrieval: {e}")
            return RetrievalResult(
                context="",
                source_chunks=[],
                total_chunks=0,
                avg_similarity=0.0,
                sources=[]
            )
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get statistics about retrieval performance"""
        try:
            vector_stats = self.vector_store.get_collection_stats()
            
            return {
                "vector_store_stats": vector_stats,
                "retrieval_config": {
                    "default_k": self.default_k,
                    "similarity_threshold": self.similarity_threshold,
                    "max_context_length": self.max_context_length
                }
            }
        except Exception as e:
            logger.error(f"Error getting retrieval stats: {e}")
            return {}
    
    def update_config(
        self,
        default_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        max_context_length: Optional[int] = None
    ) -> None:
        """Update retrieval configuration"""
        if default_k is not None:
            self.default_k = max(1, min(default_k, 10))  # Limit between 1-10
        
        if similarity_threshold is not None:
            self.similarity_threshold = max(0.0, min(similarity_threshold, 1.0))  # Limit 0-1
        
        if max_context_length is not None:
            self.max_context_length = max(500, min(max_context_length, 5000))  # Limit 500-5000
        
        logger.info(f"Updated retrieval config: k={self.default_k}, threshold={self.similarity_threshold}, max_length={self.max_context_length}")
    
    async def test_retrieval(self, test_queries: List[str]) -> Dict[str, Any]:
        """Test retrieval with a set of queries"""
        results = []
        
        for query in test_queries:
            try:
                result = await self.retrieve(query)
                results.append({
                    "query": query,
                    "chunks_found": result.total_chunks,
                    "avg_similarity": result.avg_similarity,
                    "sources": result.sources,
                    "context_length": len(result.context)
                })
            except Exception as e:
                results.append({
                    "query": query,
                    "error": str(e)
                })
        
        return {
            "test_results": results,
            "total_queries": len(test_queries),
            "successful_retrievals": len([r for r in results if "error" not in r])
        } 