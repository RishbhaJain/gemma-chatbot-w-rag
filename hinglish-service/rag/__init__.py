"""
RAG (Retrieval Augmented Generation) System for Guidance Counselor Chatbot

This module provides document ingestion, embedding, storage, and retrieval
capabilities to enhance the chatbot with knowledge from guidance counselor books/PDFs.
"""

from .document_processor import DocumentProcessor
from .vector_store import VectorStore
from .retriever import RAGRetriever
from .rag_pipeline import RAGPipeline

__version__ = "1.0.0"
__all__ = ["DocumentProcessor", "VectorStore", "RAGRetriever", "RAGPipeline"] 