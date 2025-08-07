#!/usr/bin/env python3
"""
RAG System Setup Script

This script preloads PDF documents and builds the vector database.
Run this once after adding your guidance counselor PDF books.

Usage:
    python setup_rag.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def setup_rag_system():
    """Setup the RAG system with preloaded documents"""
    
    print("🎓 Setting up RAG System for Guidance Counselor Chatbot")
    print("=" * 60)
    
    try:
        # Import RAG components
        from rag import RAGPipeline
        
        print("\n1️⃣ Initializing RAG Pipeline...")
        rag_pipeline = RAGPipeline(
            chunk_size=512,
            chunk_overlap=50,
            embedding_model="all-MiniLM-L6-v2",
            vector_db_path="./vector_db",
            similarity_threshold=0.7,
            default_k=3
        )
        print("✅ RAG Pipeline initialized")
        
        print("\n2️⃣ Checking system health...")
        health = rag_pipeline.health_check()
        if health.get('status') != 'healthy':
            print(f"⚠️ System health issues: {health}")
        else:
            print("✅ System is healthy")
        
        print("\n3️⃣ Looking for PDF documents...")
        docs_dir = Path("documents/raw")
        
        if not docs_dir.exists():
            print(f"📁 Creating documents directory: {docs_dir}")
            docs_dir.mkdir(parents=True, exist_ok=True)
            print("💡 Add your PDF guidance books to documents/raw/ and run again")
            return False
        
        # Find PDF files
        pdf_files = list(docs_dir.glob("*.pdf"))
        
        if not pdf_files:
            print("❌ No PDF files found in documents/raw/")
            print("💡 Add your guidance counselor PDF books to documents/raw/ directory")
            print("\nRecommended PDF types:")
            print("  • Career guidance books")
            print("  • Student psychology resources")
            print("  • Study skills guides")
            print("  • Stress management books")
            print("  • Indian education system guides")
            return False
        
        print(f"📚 Found {len(pdf_files)} PDF files:")
        for pdf_file in pdf_files:
            print(f"  • {pdf_file.name}")
        
        print(f"\n4️⃣ Processing {len(pdf_files)} documents...")
        
        # Process documents in batch
        pdf_paths = [str(pdf_file) for pdf_file in pdf_files]
        result = await rag_pipeline.add_documents_batch(pdf_paths, force_reprocess=False)
        
        print(f"✅ Successfully processed {result['successful']} documents")
        if result['failed'] > 0:
            print(f"❌ Failed to process {result['failed']} documents")
            for res in result['results']:
                if not res['success']:
                    print(f"  • Failed: {res.get('pdf_path', 'unknown')} - {res.get('error', 'unknown error')}")
        
        print("\n5️⃣ Vector database statistics...")
        stats = rag_pipeline.get_system_stats()
        
        print(f"📊 Total Documents: {stats.get('documents', {}).get('total_documents', 0)}")
        print(f"📄 Total Chunks: {stats.get('vector_store', {}).get('total_chunks', 0)}")
        print(f"👥 Unique Authors: {stats.get('documents', {}).get('unique_authors', 0)}")
        print(f"📖 Total Pages: {stats.get('documents', {}).get('total_pages', 0)}")
        
        if stats.get('vector_store', {}).get('total_chunks', 0) == 0:
            print("⚠️ No chunks created - check if PDFs contain extractable text")
            return False
        
        print("\n6️⃣ Testing retrieval system...")
        test_queries = [
            "How to choose a career path?",
            "I'm stressed about exams",
            "Study techniques for better focus"
        ]
        
        for query in test_queries:
            result = await rag_pipeline.query(query, k=2, similarity_threshold=0.6)
            if result.total_chunks > 0:
                print(f"✅ '{query}' → Found {result.total_chunks} relevant chunks")
            else:
                print(f"❌ '{query}' → No relevant context found")
        
        print("\n🎉 RAG System Setup Complete!")
        print("\nNext steps:")
        print("1. Start your chatbot: python main.py")
        print("2. The RAG system will automatically enhance responses")
        print("3. Responses will include citations from your PDF books")
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("💡 Install with: pip install -r requirements.txt")
        return False
        
    except Exception as e:
        logger.error(f"Error during RAG setup: {e}")
        print(f"❌ Setup failed: {e}")
        return False

def main():
    """Main entry point"""
    print("RAG System Setup for Guidance Counselor Chatbot\n")
    
    # Check if vector_db already exists
    vector_db_path = Path("vector_db")
    if vector_db_path.exists():
        print("📊 Existing vector database found.")
        response = input("Do you want to rebuild it? (y/N): ").strip().lower()
        if response == 'y':
            import shutil
            shutil.rmtree(vector_db_path)
            print("🗑️ Cleared existing vector database")
        else:
            print("ℹ️ Using existing vector database")
    
    # Run setup
    success = asyncio.run(setup_rag_system())
    
    if success:
        print("\n✅ RAG system is ready for use!")
        sys.exit(0)
    else:
        print("\n❌ RAG setup incomplete")
        sys.exit(1)

if __name__ == "__main__":
    main() 