"""
Document Processor for RAG System

Handles PDF ingestion, text extraction, chunking, and metadata extraction
for guidance counselor documents.
"""

import os
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
from datetime import datetime

import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """Represents a chunk of text from a document"""
    text: str
    metadata: Dict[str, Any]
    chunk_id: str
    doc_id: str

@dataclass 
class ProcessedDocument:
    """Represents a processed document with chunks and metadata"""
    doc_id: str
    title: str
    chunks: List[DocumentChunk]
    metadata: Dict[str, Any]
    total_chunks: int

class DocumentProcessor:
    """Processes PDF documents for RAG system"""
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
        )
        
        # Create necessary directories
        self.base_path = Path("documents")
        self.raw_path = self.base_path / "raw" 
        self.processed_path = self.base_path / "processed"
        self.metadata_path = self.base_path / "metadata"
        
        for path in [self.base_path, self.raw_path, self.processed_path, self.metadata_path]:
            path.mkdir(exist_ok=True)
    
    def generate_doc_id(self, file_path: str) -> str:
        """Generate unique document ID based on file content"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            return hashlib.md5(content).hexdigest()[:12]
        except Exception as e:
            logger.error(f"Error generating doc ID for {file_path}: {e}")
            return hashlib.md5(str(file_path).encode()).hexdigest()[:12]
    
    def extract_text_from_pdf(self, pdf_path: str) -> tuple[str, Dict[str, Any]]:
        """Extract text and metadata from PDF"""
        try:
            full_text = ""
            metadata = {
                "total_pages": 0,
                "title": "",
                "author": "",
                "subject": "",
                "creator": "",
                "file_size": os.path.getsize(pdf_path)
            }
            
            with pdfplumber.open(pdf_path) as pdf:
                metadata["total_pages"] = len(pdf.pages)
                
                # Extract PDF metadata
                if pdf.metadata:
                    metadata.update({
                        "title": pdf.metadata.get("Title", ""),
                        "author": pdf.metadata.get("Author", ""),
                        "subject": pdf.metadata.get("Subject", ""),
                        "creator": pdf.metadata.get("Creator", "")
                    })
                
                # Extract text from all pages
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            full_text += f"\n[Page {page_num}]\n{page_text}\n"
                    except Exception as e:
                        logger.warning(f"Could not extract text from page {page_num}: {e}")
                        continue
            
            # Fallback title from filename if not in metadata
            if not metadata["title"]:
                metadata["title"] = Path(pdf_path).stem.replace("_", " ").title()
            
            return full_text.strip(), metadata
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
            raise
    
    def create_chunks(self, text: str, doc_metadata: Dict[str, Any], doc_id: str) -> List[DocumentChunk]:
        """Split text into chunks with metadata"""
        try:
            # Split text into chunks
            text_chunks = self.text_splitter.split_text(text)
            
            chunks = []
            for i, chunk_text in enumerate(text_chunks):
                # Extract page number from chunk if available
                page_match = None
                lines = chunk_text.split('\n')
                for line in lines[:3]:  # Check first few lines
                    if line.startswith('[Page ') and ']' in line:
                        try:
                            page_match = int(line.split('[Page ')[1].split(']')[0])
                            break
                        except:
                            pass
                
                chunk_metadata = {
                    **doc_metadata,
                    "chunk_index": i,
                    "chunk_size": len(chunk_text),
                    "page_number": page_match,
                    "doc_id": doc_id
                }
                
                chunk_id = f"{doc_id}_chunk_{i:04d}"
                
                chunk = DocumentChunk(
                    text=chunk_text.strip(),
                    metadata=chunk_metadata,
                    chunk_id=chunk_id,
                    doc_id=doc_id
                )
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error creating chunks for document {doc_id}: {e}")
            raise
    
    def save_processed_document(self, processed_doc: ProcessedDocument) -> None:
        """Save processed document and metadata to disk"""
        try:
            # Save chunks
            chunks_file = self.processed_path / f"{processed_doc.doc_id}_chunks.json"
            chunks_data = [
                {
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "metadata": chunk.metadata
                }
                for chunk in processed_doc.chunks
            ]
            
            with open(chunks_file, 'w', encoding='utf-8') as f:
                json.dump(chunks_data, f, indent=2, ensure_ascii=False)
            
            # Save document metadata
            metadata_file = self.metadata_path / f"{processed_doc.doc_id}_metadata.json"
            doc_metadata = {
                "doc_id": processed_doc.doc_id,
                "title": processed_doc.title,
                "total_chunks": processed_doc.total_chunks,
                "metadata": processed_doc.metadata,
                "processed_at": datetime.now().isoformat(),
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap
            }
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(doc_metadata, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Saved processed document {processed_doc.doc_id} with {processed_doc.total_chunks} chunks")
            
        except Exception as e:
            logger.error(f"Error saving processed document {processed_doc.doc_id}: {e}")
            raise
    
    def process_pdf(self, pdf_path: str, title_override: Optional[str] = None) -> ProcessedDocument:
        """Process a PDF document end-to-end"""
        try:
            logger.info(f"Processing PDF: {pdf_path}")
            
            # Generate document ID
            doc_id = self.generate_doc_id(pdf_path)
            
            # Extract text and metadata
            text, metadata = self.extract_text_from_pdf(pdf_path)
            
            if not text.strip():
                raise ValueError(f"No text could be extracted from PDF: {pdf_path}")
            
            # Override title if provided
            title = title_override or metadata.get("title", Path(pdf_path).stem)
            
            # Create chunks
            chunks = self.create_chunks(text, metadata, doc_id)
            
            if not chunks:
                raise ValueError(f"No chunks created from PDF: {pdf_path}")
            
            # Create processed document
            processed_doc = ProcessedDocument(
                doc_id=doc_id,
                title=title,
                chunks=chunks,
                metadata=metadata,
                total_chunks=len(chunks)
            )
            
            # Save to disk
            self.save_processed_document(processed_doc)
            
            logger.info(f"Successfully processed PDF {pdf_path}: {len(chunks)} chunks created")
            return processed_doc
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            raise
    
    def load_processed_document(self, doc_id: str) -> Optional[ProcessedDocument]:
        """Load a previously processed document"""
        try:
            # Load metadata
            metadata_file = self.metadata_path / f"{doc_id}_metadata.json"
            if not metadata_file.exists():
                return None
                
            with open(metadata_file, 'r', encoding='utf-8') as f:
                doc_metadata = json.load(f)
            
            # Load chunks
            chunks_file = self.processed_path / f"{doc_id}_chunks.json"
            if not chunks_file.exists():
                return None
                
            with open(chunks_file, 'r', encoding='utf-8') as f:
                chunks_data = json.load(f)
            
            # Reconstruct chunks
            chunks = [
                DocumentChunk(
                    text=chunk_data["text"],
                    metadata=chunk_data["metadata"],
                    chunk_id=chunk_data["chunk_id"],
                    doc_id=doc_id
                )
                for chunk_data in chunks_data
            ]
            
            return ProcessedDocument(
                doc_id=doc_id,
                title=doc_metadata["title"],
                chunks=chunks,
                metadata=doc_metadata["metadata"],
                total_chunks=len(chunks)
            )
            
        except Exception as e:
            logger.error(f"Error loading processed document {doc_id}: {e}")
            return None
    
    def list_processed_documents(self) -> List[Dict[str, Any]]:
        """List all processed documents"""
        try:
            documents = []
            for metadata_file in self.metadata_path.glob("*_metadata.json"):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        doc_metadata = json.load(f)
                    documents.append(doc_metadata)
                except Exception as e:
                    logger.warning(f"Could not load metadata from {metadata_file}: {e}")
                    continue
            
            return sorted(documents, key=lambda x: x.get("processed_at", ""))
            
        except Exception as e:
            logger.error(f"Error listing processed documents: {e}")
            return [] 