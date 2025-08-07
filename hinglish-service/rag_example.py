#!/usr/bin/env python3
"""
RAG System Example for Guidance Counselor Chatbot

This script demonstrates how to:
1. Initialize the RAG pipeline
2. Add PDF documents
3. Query the system
4. Integrate with the existing chatbot

Usage:
    python rag_example.py
"""

import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main example function"""
    
    print("🎓 RAG System Example for Guidance Counselor Chatbot")
    print("=" * 60)
    
    try:
        # Step 1: Initialize RAG Pipeline
        print("\n1️⃣ Initializing RAG Pipeline...")
        from rag import RAGPipeline
        
        rag_pipeline = RAGPipeline(
            chunk_size=512,
            chunk_overlap=50,
            embedding_model="all-MiniLM-L6-v2",
            vector_db_path="./vector_db",
            similarity_threshold=0.7,
            default_k=3
        )
        
        print("✅ RAG Pipeline initialized successfully!")
        
        # Step 2: Check system health
        print("\n2️⃣ Checking system health...")
        health = rag_pipeline.health_check()
        print(f"System Status: {health.get('status', 'unknown')}")
        
        # Step 3: Add sample documents (if any PDFs are available)
        print("\n3️⃣ Adding documents...")
        
        # Check for sample PDFs in documents/raw directory
        sample_docs_dir = Path("documents/raw")
        if sample_docs_dir.exists():
            pdf_files = list(sample_docs_dir.glob("*.pdf"))
            if pdf_files:
                print(f"Found {len(pdf_files)} PDF files to process...")
                result = await rag_pipeline.add_documents_batch([str(pdf) for pdf in pdf_files[:2]])  # Process first 2
                print(f"✅ Successfully processed {result['successful']} documents")
            else:
                print("ℹ️ No PDF files found in documents/raw directory")
                print("💡 Add some guidance counselor PDF books to test the system!")
        else:
            print("ℹ️ Creating documents/raw directory for PDFs...")
            sample_docs_dir.mkdir(parents=True, exist_ok=True)
            print("💡 Add PDF files to documents/raw/ and run again!")
        
        # Step 4: Test queries
        print("\n4️⃣ Testing RAG queries...")
        
        test_queries = [
            "How should I choose my career path?",
            "I'm feeling stressed about my board exams",
            "My parents want me to study engineering but I'm interested in arts",
            "How can I manage time between studies and family responsibilities?",
            "What are good study techniques for better concentration?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Query {i}: {query}")
            
            result = await rag_pipeline.query(
                question=query,
                k=3,
                similarity_threshold=0.6
            )
            
            if result.total_chunks > 0:
                print(f"✅ Found {result.total_chunks} relevant chunks")
                print(f"📚 Sources: {', '.join(result.sources)}")
                print(f"📊 Avg. Similarity: {result.avg_similarity:.3f}")
                print(f"📄 Context preview: {result.context[:200]}...")
            else:
                print("❌ No relevant context found")
        
        # Step 5: Integration with Ollama Client
        print("\n5️⃣ Testing integration with Ollama Client...")
        
        from ollama_client import OllamaClient
        
        # Initialize Ollama client
        ollama_client = OllamaClient()
        await ollama_client.initialize()
        
        # Initialize RAG in Ollama client
        ollama_client.initialize_rag(rag_pipeline)
        
        # Test RAG-enhanced response
        test_question = "I'm confused about choosing between science and commerce stream"
        print(f"\n📝 Testing question: {test_question}")
        
        # Compare standard vs RAG-enhanced response
        standard_response = await ollama_client.get_response(test_question)
        rag_response = await ollama_client.get_response_with_rag(test_question)
        
        print(f"\n🤖 Standard Response: {standard_response[:200]}...")
        print(f"\n📚 RAG-Enhanced Response: {rag_response[:200]}...")
        
        # Step 6: System statistics
        print("\n6️⃣ System Statistics...")
        stats = rag_pipeline.get_system_stats()
        
        print(f"📊 Total Documents: {stats.get('documents', {}).get('total_documents', 0)}")
        print(f"📄 Total Chunks: {stats.get('vector_store', {}).get('total_chunks', 0)}")
        print(f"👥 Unique Authors: {stats.get('documents', {}).get('unique_authors', 0)}")
        print(f"📖 Total Pages: {stats.get('documents', {}).get('total_pages', 0)}")
        
        print("\n✅ RAG System Example completed successfully!")
        
        # Cleanup
        await ollama_client.cleanup()
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("💡 Install with: pip install -r requirements.txt")
    
    except Exception as e:
        logger.error(f"Error during example execution: {e}")
        print(f"❌ Example failed: {e}")

async def quick_test():
    """Quick test without full setup"""
    print("🚀 Quick RAG Test (No Documents)")
    print("=" * 40)
    
    try:
        from rag import RAGPipeline
        
        # Initialize with minimal setup
        rag_pipeline = RAGPipeline()
        
        # Health check
        health = rag_pipeline.health_check()
        print(f"✅ System Health: {health.get('status', 'unknown')}")
        
        # Test empty query (should return empty result)
        result = await rag_pipeline.query("test query")
        print(f"📝 Empty database test: {result.total_chunks} chunks found")
        
        print("✅ Basic RAG system is working!")
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")

if __name__ == "__main__":
    import sys
    
    print("RAG System Example for Guidance Counselor Chatbot")
    print("Choose an option:")
    print("1. Full example (requires PDF documents)")
    print("2. Quick test (no documents needed)")
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        asyncio.run(quick_test())
    else:
        print("\nRunning full example...")
        print("💡 Tip: Use 'python rag_example.py quick' for quick test")
        asyncio.run(main()) 