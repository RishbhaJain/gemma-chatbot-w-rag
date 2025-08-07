#!/usr/bin/env python3
"""
Hinglish Audio Processing Server
Main FastAPI application with WebSocket support for real-time audio processing
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from audio_pipeline import AudioPipeline
from language_detector import LanguageDetector
from tts_manager import HinglishTTSManager
from ollama_client import OllamaClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Hinglish Audio Processing API",
    description="Advanced audio processing pipeline with Hindi/English TTS and Hinglish STT",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
audio_pipeline: Optional[AudioPipeline] = None
language_detector: Optional[LanguageDetector] = None
tts_manager: Optional[HinglishTTSManager] = None
ollama_client: Optional[OllamaClient] = None

# RAG system
rag_pipeline = None
rag_enabled = False

# Active WebSocket connections
active_connections: List[WebSocket] = []

async def initialize_rag_system():
    """Initialize RAG system if vector database exists"""
    global rag_pipeline, rag_enabled, ollama_client
    
    try:
        from pathlib import Path
        vector_db_path = Path("vector_db")
        
        if not vector_db_path.exists():
            logger.info("No vector database found - RAG system disabled")
            logger.info("To enable RAG: add PDFs to documents/raw/ and run: python setup_rag.py")
            return
        
        # Check if vector DB has content
        try:
            from rag import RAGPipeline
            
            # Initialize RAG pipeline
            rag_pipeline = RAGPipeline(
                chunk_size=512,
                chunk_overlap=50,
                embedding_model="all-MiniLM-L6-v2",
                vector_db_path="./vector_db",
                similarity_threshold=0.7,
                default_k=3
            )
            
            # Check health and stats
            health = rag_pipeline.health_check()
            if health.get('status') != 'healthy':
                logger.warning(f"RAG system health issues: {health}")
                return
            
            stats = rag_pipeline.get_system_stats()
            total_chunks = stats.get('vector_store', {}).get('total_chunks', 0)
            total_docs = stats.get('documents', {}).get('total_documents', 0)
            
            if total_chunks == 0:
                logger.info("Vector database is empty - RAG system disabled")
                logger.info("To add documents: put PDFs in documents/raw/ and run: python setup_rag.py")
                return
            
            # RAG system is ready
            rag_enabled = True
            logger.info(f"✅ RAG system initialized: {total_docs} documents, {total_chunks} chunks")
            
            # Initialize Ollama client with RAG
            if not ollama_client:
                ollama_client = OllamaClient()
                await ollama_client.initialize()
            
            ollama_client.initialize_rag(rag_pipeline)
            logger.info("✅ Ollama client enhanced with RAG")
            
        except ImportError:
            logger.info("RAG dependencies not available - install with: pip install -r requirements.txt")
        except Exception as e:
            logger.warning(f"Failed to initialize RAG system: {e}")
            
    except Exception as e:
        logger.error(f"Error during RAG initialization: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize all components on startup"""
    global audio_pipeline, language_detector, tts_manager, ollama_client, rag_pipeline, rag_enabled
    
    logger.info("Initializing Hinglish Audio Processing Server...")
    
    try:
        # Initialize language detector
        language_detector = LanguageDetector()
        logger.info("Language detector initialized")
        
        # Initialize TTS manager
        tts_manager = HinglishTTSManager()
        await tts_manager.initialize()
        logger.info("TTS manager initialized")
        
        # Initialize audio pipeline
        audio_pipeline = AudioPipeline(language_detector, tts_manager)
        await audio_pipeline.initialize()
        logger.info("Audio pipeline initialized")
        
        # Note: Ollama client will be initialized by AudioPipeline when needed
        ollama_client = None  # Placeholder for global reference
        logger.info("Ollama client will be initialized on first use")
        
        # Initialize RAG system if vector database exists
        await initialize_rag_system()
        
        logger.info("All components initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Hinglish Audio Processing Server...")
    
    if tts_manager:
        await tts_manager.cleanup()
    if audio_pipeline:
        await audio_pipeline.cleanup()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time audio processing"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Receive audio data or text message
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "audio":
                # Process audio input
                conversation_mode = message.get("conversationMode", "hinglish")
                response = await process_audio_message(message["data"], conversation_mode)
                await websocket.send_text(json.dumps(response))
                
            elif message["type"] == "text":
                # Process text input
                conversation_mode = message.get("conversationMode", "hinglish")
                response = await process_text_message(message["data"], conversation_mode)
                await websocket.send_text(json.dumps(response))
                
            elif message["type"] == "config":
                # Update configuration
                await update_config(message["data"])
                
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        active_connections.remove(websocket)

async def process_audio_message(audio_data: str, conversation_mode: str = "hinglish") -> Dict:
    """Process incoming audio data and return response with TTS"""
    try:
        # Decode base64 audio and save temporarily
        import base64
        audio_bytes = base64.b64decode(audio_data)
        temp_path = Path("temp") / "input.wav"
        temp_path.parent.mkdir(exist_ok=True)
        
        with open(temp_path, "wb") as f:
            f.write(audio_bytes)
        
        # Process through pipeline with conversation mode
        result = await audio_pipeline.process_audio(str(temp_path), conversation_mode)
        
        # Clean up temp file
        temp_path.unlink(missing_ok=True)
        
        return {
            "type": "audio_response",
            "transcription": result["transcription"],
            "response_text": result["response"],
            "audio_response": result["audio_base64"],
            "detected_language": result["detected_language"],
            "tts_engine": result["tts_engine"]
        }
        
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        return {
            "type": "error",
            "message": str(e)
        }

async def process_text_message(text: str, conversation_mode: str = "hinglish") -> Dict:
    """Process text input and return response with TTS"""
    try:
        # Initialize Ollama client if not available
        global ollama_client
        if not ollama_client:
            from ollama_client import OllamaClient
            ollama_client = OllamaClient()
            try:
                await ollama_client.initialize()
                logger.info("Ollama client initialized for text processing")
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama client: {e}")
                ollama_client = None
        
        # Get AI response (with RAG if available)
        if ollama_client:
            try:
                if rag_enabled:
                    # Use RAG-enhanced response
                    ai_response = await ollama_client.get_response_with_rag(
                        text, 
                        scenario=conversation_mode,
                        k=3,
                        similarity_threshold=0.7
                    )
                    logger.debug("Used RAG-enhanced response")
                else:
                    # Standard response
                    ai_response = await ollama_client.get_response(text, scenario=conversation_mode)
            except Exception as e:
                logger.warning(f"Ollama failed, using fallback: {e}")
                ai_response = f"Echo: {text} (Ollama not available)"
        else:
            # Fallback response when Ollama is not available
            ai_response = f"Echo: {text} (Ollama not available)"
        
        # Detect language and generate TTS
        detected_lang = language_detector.detect_language(ai_response)
        audio_result = await tts_manager.generate_speech(ai_response, detected_lang)
        
        return {
            "type": "text_response",
            "input_text": text,
            "response_text": ai_response,
            "audio_response": audio_result.audio_base64,
            "detected_language": detected_lang,
            "tts_engine": audio_result.engine
        }
        
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        return {
            "type": "error",
            "message": str(e)
        }

async def update_config(config: Dict):
    """Update system configuration"""
    try:
        if "tts_preferences" in config:
            await tts_manager.update_preferences(config["tts_preferences"])
        if "language_preferences" in config:
            language_detector.update_preferences(config["language_preferences"])
            
    except Exception as e:
        logger.error(f"Error updating config: {e}")

@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    """Upload audio file for processing"""
    try:
        # Save uploaded file
        temp_path = Path("temp") / file.filename
        temp_path.parent.mkdir(exist_ok=True)
        
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process audio
        result = await audio_pipeline.process_audio(str(temp_path))
        
        # Clean up
        temp_path.unlink(missing_ok=True)
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing uploaded audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_data = {
        "status": "healthy",
        "components": {
            "audio_pipeline": audio_pipeline is not None,
            "language_detector": language_detector is not None,
            "tts_manager": tts_manager is not None,
            "ollama_client": ollama_client is not None,
            "rag_system": rag_enabled
        }
    }
    
    # Add RAG details if enabled
    if rag_enabled and rag_pipeline:
        try:
            rag_stats = rag_pipeline.get_system_stats()
            health_data["rag_details"] = {
                "enabled": True,
                "documents": rag_stats.get('documents', {}).get('total_documents', 0),
                "chunks": rag_stats.get('vector_store', {}).get('total_chunks', 0),
                "embedding_model": rag_stats.get('configuration', {}).get('embedding_model', 'unknown')
            }
        except Exception as e:
            health_data["rag_details"] = {
                "enabled": True,
                "error": str(e)
            }
    else:
        health_data["rag_details"] = {
            "enabled": False,
            "message": "Add PDFs to documents/raw/ and run: python setup_rag.py"
        }
    
    return health_data

@app.get("/rag/status")
async def rag_status():
    """Get detailed RAG system status"""
    if not rag_enabled or not rag_pipeline:
        return {
            "enabled": False,
            "message": "RAG system not initialized",
            "instructions": "Add PDFs to documents/raw/ and run: python setup_rag.py"
        }
    
    try:
        stats = rag_pipeline.get_system_stats()
        health = rag_pipeline.health_check()
        
        return {
            "enabled": True,
            "status": health.get('status', 'unknown'),
            "statistics": stats,
            "health": health
        }
    except Exception as e:
        return {
            "enabled": True,
            "error": str(e)
        }

@app.get("/config")
async def get_config():
    """Get current system configuration"""
    return {
        "tts_engines": await tts_manager.get_available_engines() if tts_manager else [],
        "supported_languages": language_detector.get_supported_languages() if language_detector else [],
        "current_preferences": {
            "tts": await tts_manager.get_preferences() if tts_manager else {},
            "language": language_detector.get_preferences() if language_detector else {}
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 