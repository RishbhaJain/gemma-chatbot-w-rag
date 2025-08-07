#!/usr/bin/env python3
"""
Audio Processing Pipeline
End-to-end audio processing with Whisper STT and multi-engine TTS
"""

import asyncio
import base64
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

try:
    import whisper
    import torch
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    whisper = None

try:
    import librosa
    import soundfile as sf
    AUDIO_PROCESSING_AVAILABLE = True
except ImportError:
    AUDIO_PROCESSING_AVAILABLE = False
    librosa = None
    sf = None

from language_detector import LanguageDetector
from tts_manager import HinglishTTSManager

logger = logging.getLogger(__name__)

class AudioPipeline:
    """End-to-end audio processing pipeline with STT and TTS"""
    
    def __init__(self, language_detector: LanguageDetector, tts_manager: HinglishTTSManager):
        self.language_detector = language_detector
        self.tts_manager = tts_manager
        self.whisper_model = None
        
        # Configuration
        self.config = {
            "whisper_model": "base",  # base model for Hinglish
            "sample_rate": 16000,     # Whisper expects 16kHz
            "chunk_duration": 30,     # Maximum chunk duration in seconds
            "min_audio_length": 0.5,  # Minimum audio length to process
            "enable_preprocessing": True,
            "hinglish_mode": True     # Enable Hinglish-specific processing
        }
        
        self.temp_dir = Path(tempfile.gettempdir()) / "hinglish_audio"
        self.temp_dir.mkdir(exist_ok=True)
        
        logger.info("Audio Pipeline initialized")

    async def initialize(self):
        """Initialize the audio pipeline components"""
        logger.info("Initializing Audio Pipeline...")
        
        if not WHISPER_AVAILABLE:
            raise RuntimeError("Whisper not available. Install with: pip install openai-whisper")
        
        if not AUDIO_PROCESSING_AVAILABLE:
            logger.warning("Audio processing libraries not available. Some features may be limited.")
        
        # Load Whisper model
        try:
            logger.info(f"Loading Whisper model: {self.config['whisper_model']}")
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.whisper_model = await loop.run_in_executor(
                None, 
                whisper.load_model, 
                self.config['whisper_model']
            )
            logger.info("Whisper model loaded successfully")
            
            # Test model with a small audio snippet
            await self._test_whisper_model()
            
        except Exception as e:
            logger.error(f"Failed to initialize Whisper model: {e}")
            raise

    async def _test_whisper_model(self):
        """Test Whisper model with a simple audio test"""
        try:
            # Create a simple test audio (silence)
            import numpy as np
            test_audio = np.zeros(16000)  # 1 second of silence
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.whisper_model.transcribe,
                test_audio
            )
            logger.info("Whisper model test completed successfully")
            
        except Exception as e:
            logger.warning(f"Whisper model test failed: {e}")

    async def process_audio(self, audio_path: Union[str, Path], conversation_mode: str = "hinglish") -> Dict:
        """
        Process audio file through the complete pipeline
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Dictionary with transcription, AI response, and TTS audio
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        logger.info(f"Processing audio file: {audio_path}")
        
        try:
            # Step 1: Preprocess audio
            processed_audio_path = await self._preprocess_audio(audio_path)
            
            # Step 2: Speech-to-text with Whisper
            transcription_result = await self._transcribe_audio(processed_audio_path)
            
            # Step 3: Language detection
            detected_language = self.language_detector.detect_language(
                transcription_result["text"]
            )
            
            # Step 4: Get AI response with conversation mode
            ai_response = await self._get_ai_response(
                transcription_result["text"], 
                detected_language,
                conversation_mode
            )
            
            # Step 5: Generate TTS response
            tts_result = await self.tts_manager.generate_speech(
                ai_response["text"], 
                ai_response["language"]
            )
            
            # Clean up temporary files
            if processed_audio_path != audio_path:
                processed_audio_path.unlink(missing_ok=True)
            
            return {
                "transcription": transcription_result["text"],
                "transcription_language": detected_language,
                "transcription_confidence": transcription_result.get("confidence", 0.0),
                "response": ai_response["text"],
                "response_language": ai_response["language"],
                "audio_base64": tts_result.audio_base64,
                "tts_engine": tts_result.engine,
                "detected_language": detected_language,
                "processing_time": {
                    "transcription": transcription_result.get("duration", 0.0),
                    "tts": tts_result.duration,
                    "total": time.time() - self.start_time if hasattr(self, 'start_time') else 0.0
                }
            }
            
        except Exception as e:
            logger.error(f"Audio processing failed: {e}")
            raise

    async def _preprocess_audio(self, audio_path: Path) -> Path:
        """Preprocess audio for optimal Whisper performance"""
        if not self.config["enable_preprocessing"] or not AUDIO_PROCESSING_AVAILABLE:
            return audio_path
        
        try:
            # Load audio
            audio, sr = librosa.load(str(audio_path), sr=None)
            
            # Resample to 16kHz for Whisper
            if sr != self.config["sample_rate"]:
                audio = librosa.resample(
                    audio, 
                    orig_sr=sr, 
                    target_sr=self.config["sample_rate"]
                )
            
            # Normalize audio
            audio = librosa.util.normalize(audio)
            
            # Remove silence at the beginning and end
            audio, _ = librosa.effects.trim(audio, top_db=20)
            
            # Check minimum length
            min_samples = int(self.config["min_audio_length"] * self.config["sample_rate"])
            if len(audio) < min_samples:
                logger.warning(f"Audio too short: {len(audio)/self.config['sample_rate']:.2f}s")
                return audio_path
            
            # Save processed audio
            processed_path = self.temp_dir / f"processed_{audio_path.name}"
            sf.write(str(processed_path), audio, self.config["sample_rate"])
            
            logger.info(f"Audio preprocessed: {processed_path}")
            return processed_path
            
        except Exception as e:
            logger.warning(f"Audio preprocessing failed: {e}, using original")
            return audio_path

    async def _transcribe_audio(self, audio_path: Path) -> Dict:
        """Transcribe audio using Whisper with Hinglish support"""
        if not self.whisper_model:
            raise RuntimeError("Whisper model not initialized")
        
        start_time = time.time()
        
        try:
            # Prepare Whisper options for Hinglish
            transcribe_options = {
                "language": None,  # Let Whisper auto-detect
                "task": "transcribe",
                "fp16": torch.cuda.is_available(),  # Use FP16 if GPU available
            }
            
            # For Hinglish, we might want to try Hindi first, then English
            if self.config["hinglish_mode"]:
                # Try Hindi detection first
                transcribe_options["language"] = "hi"
            
            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._whisper_transcribe_with_options,
                str(audio_path),
                transcribe_options
            )
            
            transcribed_text = result["text"].strip()
            
            # If Hindi transcription gives poor results, try English
            if (self.config["hinglish_mode"] and 
                len(transcribed_text) < 10 and 
                transcribe_options["language"] == "hi"):
                
                logger.info("Retrying transcription with English")
                transcribe_options["language"] = "en"
                result = await loop.run_in_executor(
                    None,
                    self._whisper_transcribe_with_options,
                    str(audio_path),
                    transcribe_options
                )
                transcribed_text = result["text"].strip()
            
            duration = time.time() - start_time
            
            # Calculate confidence score from segments if available
            confidence = self._calculate_confidence(result)
            
            logger.info(f"Transcription completed in {duration:.2f}s: {transcribed_text[:100]}...")
            
            return {
                "text": transcribed_text,
                "language": result.get("language", "unknown"),
                "confidence": confidence,
                "duration": duration,
                "segments": result.get("segments", [])
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise

    def _whisper_transcribe_with_options(self, audio_path: str, options: Dict) -> Dict:
        """Helper method to run Whisper transcription with specific options"""
        return self.whisper_model.transcribe(audio_path, **options)

    def _calculate_confidence(self, whisper_result: Dict) -> float:
        """Calculate average confidence score from Whisper segments"""
        segments = whisper_result.get("segments", [])
        if not segments:
            return 0.0
        
        # Calculate average confidence from segments
        total_confidence = 0.0
        total_duration = 0.0
        
        for segment in segments:
            if "confidence" in segment and "end" in segment and "start" in segment:
                duration = segment["end"] - segment["start"]
                total_confidence += segment["confidence"] * duration
                total_duration += duration
        
        if total_duration > 0:
            return total_confidence / total_duration
        else:
            return 0.8  # Default confidence if no segment data

    async def _get_ai_response(self, text: str, language: str, conversation_mode: str = "hinglish") -> Dict:
        """
        Get AI response using OllamaClient (with RAG if available)
        """
        # Import here to avoid circular import
        from ollama_client import OllamaClient
        
        if not hasattr(self, 'ollama_client'):
            # Initialize Ollama client if not already done
            self.ollama_client = OllamaClient()
            try:
                await self.ollama_client.initialize()
                
                # Check for global RAG system and initialize it
                await self._check_and_initialize_rag()
                
            except Exception as e:
                logger.warning(f"Failed to initialize Ollama client: {e}")
                # Fallback to simple responses
                return self._get_fallback_response(text, language)
        
        try:
            # Check if ollama_client is properly initialized
            if not self.ollama_client:
                logger.warning("Ollama client is None, using fallback response")
                return self._get_fallback_response(text, language)
            
            # Get AI response (with RAG if available)
            if hasattr(self.ollama_client, 'rag_enabled') and self.ollama_client.rag_enabled:
                # Use RAG-enhanced response
                ai_response = await self.ollama_client.get_response_with_rag(
                    text, 
                    language_hint=language, 
                    scenario=conversation_mode,
                    k=3,
                    similarity_threshold=0.7
                )
                logger.debug("Audio pipeline used RAG-enhanced response")
            else:
                # Standard response
                ai_response = await self.ollama_client.get_response(text, language_hint=language, scenario=conversation_mode)
            
            # Detect language of response
            response_language = self.language_detector.detect_language(ai_response)
            
            return {
                "text": ai_response,
                "language": response_language
            }
            
        except Exception as e:
            logger.error(f"Ollama response failed: {e}")
            return self._get_fallback_response(text, language)

    async def _check_and_initialize_rag(self):
        """Check for global RAG system and initialize it in ollama_client if available"""
        try:
            from pathlib import Path
            vector_db_path = Path("vector_db")
            
            # Check if vector database exists
            if not vector_db_path.exists():
                logger.debug("No vector database found for audio pipeline")
                return
            
            # Try to initialize RAG
            try:
                from rag import RAGPipeline
                
                rag_pipeline = RAGPipeline(
                    chunk_size=512,
                    chunk_overlap=50,
                    embedding_model="all-MiniLM-L6-v2",
                    vector_db_path="./vector_db",
                    similarity_threshold=0.7,
                    default_k=3
                )
                
                # Check if it has content
                stats = rag_pipeline.get_system_stats()
                total_chunks = stats.get('vector_store', {}).get('total_chunks', 0)
                
                if total_chunks > 0:
                    # Initialize RAG in ollama client
                    self.ollama_client.initialize_rag(rag_pipeline)
                    logger.info(f"Audio pipeline initialized with RAG: {total_chunks} chunks available")
                else:
                    logger.debug("Vector database is empty for audio pipeline")
                    
            except ImportError:
                logger.debug("RAG dependencies not available for audio pipeline")
            except Exception as e:
                logger.warning(f"Failed to initialize RAG for audio pipeline: {e}")
                
        except Exception as e:
            logger.debug(f"Error checking RAG system for audio pipeline: {e}")

    def _get_fallback_response(self, text: str, language: str) -> Dict:
        """Fallback response when Ollama is not available"""
        if not text.strip():
            if language.startswith("hi"):
                response_text = "मुझे समझ नहीं आया। कृपया फिर से कहें।"
                response_lang = "hi"
            else:
                response_text = "I didn't understand. Please say that again."
                response_lang = "en"
        else:
            # Simple echo response for testing
            if language == "hi":
                response_text = f"आपने कहा: {text}। यह एक परीक्षण उत्तर है।"
                response_lang = "hi"
            elif language == "en":
                response_text = f"You said: {text}. This is a test response."
                response_lang = "en"
            else:  # Mixed language
                response_text = f"You said: {text}। यह एक mixed response है।"
                response_lang = "hi-en"
        
        return {
            "text": response_text,
            "language": response_lang
        }

    async def transcribe_only(self, audio_path: Union[str, Path]) -> Dict:
        """Transcribe audio without generating a response"""
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Preprocess and transcribe
        processed_audio_path = await self._preprocess_audio(audio_path)
        transcription_result = await self._transcribe_audio(processed_audio_path)
        
        # Language detection
        detected_language = self.language_detector.detect_language(
            transcription_result["text"]
        )
        
        # Clean up
        if processed_audio_path != audio_path:
            processed_audio_path.unlink(missing_ok=True)
        
        return {
            "transcription": transcription_result["text"],
            "language": detected_language,
            "confidence": transcription_result.get("confidence", 0.0),
            "duration": transcription_result.get("duration", 0.0)
        }

    async def text_to_speech(self, text: str, language: str = None) -> Dict:
        """Convert text to speech using the TTS manager"""
        if not language:
            language = self.language_detector.detect_language(text)
        
        tts_result = await self.tts_manager.generate_speech(text, language)
        
        return {
            "success": tts_result.success,
            "audio_base64": tts_result.audio_base64,
            "engine": tts_result.engine,
            "language": language,
            "duration": tts_result.duration,
            "error": tts_result.error
        }

    def set_whisper_model(self, model_name: str):
        """Change Whisper model (requires reinitialization)"""
        if model_name in ["tiny", "base", "small", "medium", "large"]:
            self.config["whisper_model"] = model_name
            logger.info(f"Whisper model set to: {model_name}")
            # Note: Will require calling initialize() again
        else:
            logger.warning(f"Invalid Whisper model: {model_name}")

    def update_config(self, new_config: Dict):
        """Update pipeline configuration"""
        self.config.update(new_config)
        logger.info(f"Updated audio pipeline config: {new_config}")

    def get_config(self) -> Dict:
        """Get current pipeline configuration"""
        return self.config.copy()

    async def cleanup(self):
        """Cleanup pipeline resources"""
        logger.info("Cleaning up Audio Pipeline...")
        
        # Clean up temporary files
        if self.temp_dir.exists():
            for temp_file in self.temp_dir.glob("*"):
                try:
                    temp_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete {temp_file}: {e}")
        
        # Clean up Whisper model
        if self.whisper_model:
            del self.whisper_model
            self.whisper_model = None
        
        # Clear GPU cache if using CUDA
        if torch and torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("Audio Pipeline cleanup completed")

if __name__ == "__main__":
    # Test the audio pipeline
    async def test_pipeline():
        from language_detector import LanguageDetector
        from tts_manager import HinglishTTSManager
        
        # Initialize components
        language_detector = LanguageDetector()
        tts_manager = HinglishTTSManager()
        await tts_manager.initialize()
        
        # Initialize pipeline
        pipeline = AudioPipeline(language_detector, tts_manager)
        await pipeline.initialize()
        
        # Test text-to-speech
        test_texts = [
            ("Hello, this is a test.", "en"),
            ("नमस्ते, यह एक परीक्षण है।", "hi")
        ]
        
        for text, lang in test_texts:
            print(f"\nTesting TTS: {text}")
            result = await pipeline.text_to_speech(text, lang)
            print(f"Success: {result['success']}")
            print(f"Engine: {result['engine']}")
            print(f"Duration: {result['duration']:.2f}s")
        
        await pipeline.cleanup()
        await tts_manager.cleanup()
    
    asyncio.run(test_pipeline()) 