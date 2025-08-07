#!/usr/bin/env python3
"""
Text-to-Speech Manager
Advanced TTS manager with multiple engines and fallback hierarchy for Hindi/English
"""

import asyncio
import base64
import io
import logging
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

try:
    import torch
    from TTS.api import TTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    TTS = None

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    gTTS = None

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    pyttsx3 = None

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    pygame = None

# Check for Indic Parler-TTS dependencies
try:
    from parler_tts import ParlerTTSForConditionalGeneration
    from transformers import AutoTokenizer
    import soundfile as sf
    INDIC_PARLER_AVAILABLE = True
except ImportError:
    INDIC_PARLER_AVAILABLE = False
    ParlerTTSForConditionalGeneration = None
    AutoTokenizer = None
    sf = None

logger = logging.getLogger(__name__)

class TTSEngine(Enum):
    """Available TTS engines"""
    INDIC_PARLER = "indic_parler"  # Primary choice for Indian languages
    COQUI = "coqui"
    GTTS = "gtts"
    PYTTSX3 = "pyttsx3"
    SYSTEM = "system"

@dataclass
class TTSResult:
    """TTS generation result"""
    success: bool
    audio_data: Optional[bytes]
    audio_base64: Optional[str]
    engine: str
    language: str
    error: Optional[str] = None
    duration: float = 0.0

@dataclass
class VoiceConfig:
    """Voice configuration for different engines"""
    engine: TTSEngine
    language: str
    voice_id: Optional[str] = None
    model_path: Optional[str] = None
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0

class HinglishTTSManager:
    """Advanced TTS manager with multiple engines and intelligent fallback"""
    
    def __init__(self):
        self.engines = {}
        self.preferences = {
            "primary_engine": TTSEngine.INDIC_PARLER,  # Changed to Indic Parler-TTS
            "fallback_order": [TTSEngine.INDIC_PARLER, TTSEngine.COQUI, TTSEngine.GTTS, TTSEngine.PYTTSX3],
            "hindi_voice": "rohit",          # Indic Parler-TTS speaker
            "english_voice": "mary",         # Indic Parler-TTS speaker  
            "hinglish_voice": "divya",       # Perfect for code-mixed content
            "speed": 1.0,
            "quality": "high"
        }
        
        # Voice configurations with Indian-specific models
        self.voice_configs = {
            "hi": {
                TTSEngine.INDIC_PARLER: VoiceConfig(
                    engine=TTSEngine.INDIC_PARLER,
                    language="hi",
                    model_path="ai4bharat/indic-parler-tts",
                    voice_id="Rohit",  # Recommended Hindi male voice
                    speed=1.0
                ),
                TTSEngine.COQUI: VoiceConfig(
                    engine=TTSEngine.COQUI,
                    language="hi",
                    model_path="tts_models/hi/male/glow",
                    speed=1.0
                ),
                TTSEngine.GTTS: VoiceConfig(
                    engine=TTSEngine.GTTS,
                    language="hi",
                    speed=1.0
                ),
                TTSEngine.PYTTSX3: VoiceConfig(
                    engine=TTSEngine.PYTTSX3,
                    language="hi",
                    voice_id="hindi",
                    speed=1.0
                )
            },
            "en": {
                TTSEngine.INDIC_PARLER: VoiceConfig(
                    engine=TTSEngine.INDIC_PARLER,
                    language="en",
                    model_path="ai4bharat/indic-parler-tts", 
                    voice_id="Mary",  # Recommended English female voice with Indian accent
                    speed=1.0
                ),
                TTSEngine.COQUI: VoiceConfig(
                    engine=TTSEngine.COQUI,
                    language="en",
                    model_path="tts_models/en/ljspeech/tacotron2-DDC",
                    speed=1.0
                ),
                TTSEngine.GTTS: VoiceConfig(
                    engine=TTSEngine.GTTS,
                    language="en",
                    speed=1.0
                ),
                TTSEngine.PYTTSX3: VoiceConfig(
                    engine=TTSEngine.PYTTSX3,
                    language="en",
                    voice_id="english",
                    speed=1.0
                )
            },
            "hinglish": {
                TTSEngine.INDIC_PARLER: VoiceConfig(
                    engine=TTSEngine.INDIC_PARLER,
                    language="hinglish",  # Auto-detects mixed language
                    model_path="ai4bharat/indic-parler-tts",
                    voice_id="Divya",  # Perfect for Hinglish
                    speed=1.0
                ),
                TTSEngine.COQUI: VoiceConfig(
                    engine=TTSEngine.COQUI,
                    language="hinglish",
                    model_path="tts_models/multilingual/multi-dataset/xtts_v2",
                    speed=1.0
                ),
                TTSEngine.GTTS: VoiceConfig(
                    engine=TTSEngine.GTTS,
                    language="hi",  # Fallback to Hindi
                    speed=1.0
                )
            }
        }
        
        self.temp_dir = Path(tempfile.gettempdir()) / "hinglish_tts"
        self.temp_dir.mkdir(exist_ok=True)
        
        logger.info("TTS Manager initialized")

    async def initialize(self):
        """Initialize all available TTS engines"""
        logger.info("Initializing Enhanced Hinglish TTS Manager...")
        
        # Initialize engines in order of preference
        await self._initialize_indic_parler()
        await self._initialize_coqui() 
        await self._initialize_gtts()
        await self._initialize_pyttsx3()
        
        logger.info(f"TTS Manager initialized with engines: {list(self.engines.keys())}")

    async def _initialize_indic_parler(self):
        """Initialize Indic Parler-TTS - Best for Indian languages"""
        if not INDIC_PARLER_AVAILABLE:
            logger.warning("Indic Parler-TTS not available")
            return
        
        try:
            device = "cuda:0" if torch.cuda.is_available() else "cpu"
            
            # Load the model (this will download ~1GB on first run)
            logger.info("Loading Indic Parler-TTS model (may take a few minutes on first run)...")
            model = ParlerTTSForConditionalGeneration.from_pretrained("ai4bharat/indic-parler-tts").to(device)
            tokenizer = AutoTokenizer.from_pretrained("ai4bharat/indic-parler-tts")
            description_tokenizer = AutoTokenizer.from_pretrained(model.config.text_encoder._name_or_path)
            
            self.engines["indic_parler"] = {
                "model": model,
                "tokenizer": tokenizer, 
                "description_tokenizer": description_tokenizer,
                "device": device
            }
            
            logger.info("✅ Indic Parler-TTS initialized successfully (21 languages, 69 voices)")
            
        except Exception as e:
            logger.error(f"Failed to load Indic Parler-TTS: {e}")
            logger.info("💡 Install with: pip install git+https://github.com/huggingface/parler-tts.git transformers torch soundfile")

    async def _initialize_coqui(self):
        """Initialize Coqui TTS models (fallback)"""
        if not TTS_AVAILABLE:
            return
        
        try:
            # Initialize Hindi model with better quality options
            hindi_models = [
                "tts_models/hi/female/glow",
                "tts_models/multilingual/multi-dataset/xtts_v2",
                "tts_models/multilingual/multi-dataset/your_tts",
                "tts_models/hi/male/glow"
            ]
            
            hindi_loaded = False
            for model in hindi_models:
                try:
                    self.engines[f"{TTSEngine.COQUI.value}_hi"] = TTS(model)
                    logger.info(f"Loaded Hindi Coqui model: {model}")
                    hindi_loaded = True
                    break
                except Exception as e:
                    logger.warning(f"Failed to load Hindi model {model}: {e}")
                    continue
            
            if not hindi_loaded:
                logger.warning("No Hindi Coqui models could be loaded")
            
            # Initialize English model with better quality options
            english_models = [
                "tts_models/multilingual/multi-dataset/xtts_v2",
                "tts_models/en/vctk/vits",
                "tts_models/en/jenny/jenny",
                "tts_models/en/ljspeech/glow-tts",
                "tts_models/en/ljspeech/tacotron2-DDC"
            ]
            
            english_loaded = False
            for model in english_models:
                try:
                    self.engines[f"{TTSEngine.COQUI.value}_en"] = TTS(model)
                    logger.info(f"Loaded English Coqui model: {model}")
                    english_loaded = True
                    break
                except Exception as e:
                    logger.warning(f"Failed to load English model {model}: {e}")
                    continue
            
            if not english_loaded:
                logger.warning("No English Coqui models could be loaded")
                
        except Exception as e:
            logger.error(f"Coqui TTS initialization failed: {e}")

    async def _initialize_gtts(self):
        """Initialize gTTS"""
        if not GTTS_AVAILABLE:
            return
        
        # gTTS doesn't need explicit initialization
        self.engines[TTSEngine.GTTS.value] = "gtts_available"
        
    async def _initialize_pyttsx3(self):
        """Initialize pyttsx3 with system voices"""
        if not PYTTSX3_AVAILABLE:
            return
        
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            
            # Find Hindi and English voices
            hindi_voices = []
            english_voices = []
            
            for voice in voices:
                voice_name = voice.name.lower()
                if any(term in voice_name for term in ['hindi', 'devanagari', 'भारत']):
                    hindi_voices.append(voice)
                elif any(term in voice_name for term in ['english', 'en-', 'us', 'uk']):
                    english_voices.append(voice)
            
            self.engines[f"{TTSEngine.PYTTSX3.value}_voices"] = {
                "engine": engine,
                "hindi_voices": hindi_voices,
                "english_voices": english_voices
            }
            
            logger.info(f"pyttsx3 initialized with {len(hindi_voices)} Hindi and {len(english_voices)} English voices")
            
        except Exception as e:
            logger.error(f"pyttsx3 initialization failed: {e}")

    async def generate_speech(self, text: str, language: str = "hi") -> TTSResult:
        """
        Generate speech from text using the best available engine
        
        Args:
            text: Text to convert to speech
            language: Target language ('hi', 'en', or 'hi-en' for mixed)
            
        Returns:
            TTSResult with audio data and metadata
        """
        if not text or not text.strip():
            return TTSResult(
                success=False,
                audio_data=None,
                audio_base64=None,
                engine="none",
                language=language,
                error="Empty text provided"
            )
        
        # Handle mixed language content
        if language == "hi-en":
            return await self._handle_mixed_language(text)
        
        # Try engines in preference order
        for engine in self.preferences["fallback_order"]:
            try:
                result = await self._generate_with_engine(text, language, engine)
                if result.success:
                    return result
                else:
                    logger.warning(f"Engine {engine.value} failed: {result.error}")
            except Exception as e:
                logger.warning(f"Engine {engine.value} error: {e}")
                continue
        
        # If all engines fail
        return TTSResult(
            success=False,
            audio_data=None,
            audio_base64=None,
            engine="none",
            language=language,
            error="All TTS engines failed"
        )

    async def _handle_mixed_language(self, text: str) -> TTSResult:
        """Handle mixed Hindi-English content"""
        # For now, detect primary language and use that
        # Future enhancement: split text by language and synthesize separately
        from language_detector import LanguageDetector
        
        detector = LanguageDetector()
        detected = detector.detect_detailed(text)
        
        primary_lang = detected.primary_language
        if primary_lang not in ["hi", "en"]:
            primary_lang = "hi"  # Default to Hindi
        
        return await self.generate_speech(text, primary_lang)

    async def _generate_with_engine(self, text: str, language: str, engine: TTSEngine) -> TTSResult:
        """Generate speech using specific engine"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            if engine == TTSEngine.INDIC_PARLER:
                # Get voice_id from language config
                voice_config = self.voice_configs.get(language, {}).get(TTSEngine.INDIC_PARLER)
                voice_id = voice_config.voice_id if voice_config else None
                result = await self._generate_indic_parler(text, language, voice_id)
            elif engine == TTSEngine.COQUI:
                result = await self._generate_coqui(text, language)
            elif engine == TTSEngine.GTTS:
                result = await self._generate_gtts(text, language)
            elif engine == TTSEngine.PYTTSX3:
                result = await self._generate_pyttsx3(text, language)
            else:
                raise ValueError(f"Unknown engine: {engine}")
            
            duration = asyncio.get_event_loop().time() - start_time
            result.duration = duration
            
            return result
            
        except Exception as e:
            return TTSResult(
                success=False,
                audio_data=None,
                audio_base64=None,
                engine=engine.value,
                language=language,
                error=str(e)
            )

    async def _generate_coqui(self, text: str, language: str) -> TTSResult:
        """Generate speech using Coqui TTS"""
        engine_key = f"{TTSEngine.COQUI.value}_{language}"
        
        if engine_key not in self.engines:
            raise ValueError(f"Coqui TTS not available for language: {language}")
        
        tts_engine = self.engines[engine_key]
        
        # Generate audio to temporary file
        temp_file = self.temp_dir / f"coqui_{language}_{hash(text)}.wav"
        
        # Run TTS generation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, 
            lambda: tts_engine.tts_to_file(text=text, file_path=str(temp_file))
        )
        
        # Read generated audio
        audio_data = temp_file.read_bytes()
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Clean up
        temp_file.unlink(missing_ok=True)
        
        return TTSResult(
            success=True,
            audio_data=audio_data,
            audio_base64=audio_base64,
            engine=TTSEngine.COQUI.value,
            language=language
        )

    async def _generate_gtts(self, text: str, language: str) -> TTSResult:
        """Generate speech using gTTS"""
        if TTSEngine.GTTS.value not in self.engines:
            raise ValueError("gTTS not available")
        
        # Map language codes
        lang_code = "hi" if language == "hi" else "en"
        
        # Generate TTS
        tts = gTTS(text=text, lang=lang_code, slow=False)
        
        # Save to memory
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_data = audio_buffer.getvalue()
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        return TTSResult(
            success=True,
            audio_data=audio_data,
            audio_base64=audio_base64,
            engine=TTSEngine.GTTS.value,
            language=language
        )

    async def _generate_pyttsx3(self, text: str, language: str) -> TTSResult:
        """Generate speech using pyttsx3"""
        engine_key = f"{TTSEngine.PYTTSX3.value}_{language}"
        
        if engine_key not in self.engines:
            raise ValueError(f"pyttsx3 not available for language: {language}")
        
        engine_config = self.engines[engine_key]
        engine = engine_config["engine"]
        voices = engine_config["voices"]
        
        # Set voice
        if voices:
            engine.setProperty('voice', voices[0].id)
        
        # Set speech rate
        engine.setProperty('rate', int(200 * self.preferences["speed"]))
        
        # Generate speech to file
        temp_file = self.temp_dir / f"pyttsx3_{language}_{hash(text)}.wav"
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self._pyttsx3_to_file,
            engine, text, str(temp_file)
        )
        
        # Read generated audio
        if temp_file.exists():
            audio_data = temp_file.read_bytes()
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            temp_file.unlink(missing_ok=True)
            
            return TTSResult(
                success=True,
                audio_data=audio_data,
                audio_base64=audio_base64,
                engine=TTSEngine.PYTTSX3.value,
                language=language
            )
        else:
            raise RuntimeError("pyttsx3 failed to generate audio file")

    def _pyttsx3_to_file(self, engine, text: str, file_path: str):
        """Helper method to save pyttsx3 output to file"""
        engine.save_to_file(text, file_path)
        engine.runAndWait()

    async def _generate_indic_parler(self, text: str, language: str, voice_id: str = None) -> TTSResult:
        """Generate speech using Indic Parler-TTS (Best for Indian languages)"""
        if "indic_parler" not in self.engines:
            raise RuntimeError("Indic Parler-TTS not available")
        
        engine_data = self.engines["indic_parler"]
        model = engine_data["model"]
        tokenizer = engine_data["tokenizer"]
        description_tokenizer = engine_data["description_tokenizer"]
        device = engine_data["device"]
        
        # Choose appropriate speaker based on language and voice_id
        speaker_map = {
            "hi": voice_id or "Rohit",
            "hindi": voice_id or "Rohit", 
            "en": voice_id or "Mary",
            "english": voice_id or "Mary",
            "hinglish": voice_id or "Divya"
        }
        
        speaker = speaker_map.get(language.lower(), "Mary")
        
        # Create voice description for the speaker
        description = f"{speaker} speaks with clear pronunciation in a natural, conversational tone with high recording quality."
        
        try:
            # Tokenize inputs
            description_input_ids = description_tokenizer(description, return_tensors="pt").to(device)
            prompt_input_ids = tokenizer(text, return_tensors="pt").to(device)
            
            # Generate audio
            with torch.no_grad():
                generation = model.generate(
                    input_ids=description_input_ids.input_ids,
                    attention_mask=description_input_ids.attention_mask,
                    prompt_input_ids=prompt_input_ids.input_ids,
                    prompt_attention_mask=prompt_input_ids.attention_mask
                )
            
            # Convert to audio array
            audio_arr = generation.cpu().numpy().squeeze()
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            sf.write(temp_file.name, audio_arr, model.config.sampling_rate)
            
            # Read and encode
            with open(temp_file.name, "rb") as f:
                audio_data = f.read()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Cleanup
            os.unlink(temp_file.name)
            
            return TTSResult(
                success=True,
                audio_data=audio_data,
                audio_base64=audio_base64,
                engine="indic_parler",
                language=language,
                duration=len(audio_arr) / model.config.sampling_rate,
                voice_used=speaker
            )
            
        except Exception as e:
            logger.error(f"Indic Parler-TTS generation failed: {e}")
            raise RuntimeError(f"Indic Parler-TTS failed: {e}")

    async def get_available_engines(self) -> List[str]:
        """Get list of available TTS engines"""
        return list(self.engines.keys())

    async def get_preferences(self) -> Dict:
        """Get current TTS preferences"""
        return self.preferences.copy()

    async def update_preferences(self, new_preferences: Dict):
        """Update TTS preferences"""
        self.preferences.update(new_preferences)
        logger.info(f"Updated TTS preferences: {self.preferences}")

    def set_voice_preference(self, language: str, engine: TTSEngine, voice_id: str):
        """Set voice preference for specific language and engine"""
        if language in self.voice_configs and engine in self.voice_configs[language]:
            self.voice_configs[language][engine].voice_id = voice_id
            logger.info(f"Set {language} voice for {engine.value}: {voice_id}")

    def set_speed(self, speed: float):
        """Set global speech speed (0.5 to 2.0)"""
        self.preferences["speed"] = max(0.5, min(2.0, speed))
        logger.info(f"Set speech speed to: {speed}")

    async def test_engine(self, engine: TTSEngine, language: str = "hi") -> bool:
        """Test if specific engine is working"""
        test_text = "नमस्ते" if language == "hi" else "Hello"
        
        try:
            result = await self._generate_with_engine(test_text, language, engine)
            return result.success
        except Exception as e:
            logger.warning(f"Engine test failed for {engine.value}: {e}")
            return False

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up TTS Manager...")
        
        # Clean up temporary files
        if self.temp_dir.exists():
            for temp_file in self.temp_dir.glob("*"):
                try:
                    temp_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete {temp_file}: {e}")
        
        # Clean up pygame
        if PYGAME_AVAILABLE and pygame.mixer.get_init():
            pygame.mixer.quit()
        
        logger.info("TTS Manager cleanup completed")

if __name__ == "__main__":
    # Test the TTS manager
    async def test_tts():
        manager = HinglishTTSManager()
        await manager.initialize()
        
        test_texts = [
            ("Hello, how are you?", "en"),
            ("नमस्ते, आप कैसे हैं?", "hi"),
            ("Hi, मैं ठीक हूँ।", "hi-en")
        ]
        
        for text, lang in test_texts:
            print(f"\nTesting: {text} (lang: {lang})")
            result = await manager.generate_speech(text, lang)
            print(f"Success: {result.success}")
            print(f"Engine: {result.engine}")
            print(f"Duration: {result.duration:.2f}s")
            if not result.success:
                print(f"Error: {result.error}")
        
        await manager.cleanup()
    
    asyncio.run(test_tts()) 