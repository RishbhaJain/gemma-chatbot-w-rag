#!/usr/bin/env python3
"""
Language Detection Module
Advanced language detection for Hindi vs English content with Devanagari script recognition
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

try:
    from langdetect import detect, detect_langs
    from langdetect.lang_detect_exception import LangDetectException
except ImportError:
    detect = None
    detect_langs = None
    LangDetectException = Exception

logger = logging.getLogger(__name__)

@dataclass
class DetectionResult:
    """Language detection result with confidence scores"""
    primary_language: str
    confidence: float
    script_type: str
    is_mixed: bool
    language_distribution: Dict[str, float]

class LanguageDetector:
    """Advanced language detector for Hindi/English and Devanagari script detection"""
    
    def __init__(self):
        self.preferences = {
            "default_language": "hi",  # Default to Hindi for ambiguous cases
            "mixed_threshold": 0.3,    # Threshold for considering text as mixed
            "confidence_threshold": 0.7  # Minimum confidence for reliable detection
        }
        
        # Devanagari Unicode ranges
        self.devanagari_range = [
            (0x0900, 0x097F),  # Devanagari
            (0xA8E0, 0xA8FF),  # Devanagari Extended
        ]
        
        # Common Hindi words and patterns
        self.hindi_indicators = {
            "words": ["है", "हैं", "का", "की", "के", "में", "से", "को", "और", "या", "तो", "भी", "अब", "यह", "वह"],
            "patterns": [
                r"[\u0900-\u097F]+",  # Devanagari characters
                r"\b(hai|hain|ka|ki|ke|mein|se|ko|aur|ya|to|bhi|ab|yah|vah)\b"  # Romanized Hindi
            ]
        }
        
        # English indicators
        self.english_indicators = {
            "words": ["the", "and", "is", "are", "was", "were", "in", "on", "at", "to", "for", "of", "with"],
            "patterns": [
                r"\b[a-zA-Z]+\b",  # English words
                r"\b(is|are|was|were|the|and|in|on|at|to|for|of|with)\b"
            ]
        }
        
        logger.info("Language detector initialized")

    def detect_language(self, text: str) -> str:
        """
        Detect the primary language of the given text
        Returns: 'hi' for Hindi, 'en' for English, 'hi-en' for mixed
        """
        if not text or not text.strip():
            return self.preferences["default_language"]
        
        result = self._analyze_text(text)
        
        # Determine primary language based on analysis
        if result.is_mixed:
            return "hi-en"  # Mixed language
        else:
            return result.primary_language

    def detect_detailed(self, text: str) -> DetectionResult:
        """Get detailed language detection results"""
        return self._analyze_text(text)

    def _analyze_text(self, text: str) -> DetectionResult:
        """Perform comprehensive text analysis"""
        if not text or not text.strip():
            return DetectionResult(
                primary_language=self.preferences["default_language"],
                confidence=0.0,
                script_type="unknown",
                is_mixed=False,
                language_distribution={}
            )
        
        # Clean text
        cleaned_text = self._clean_text(text)
        
        # Script analysis
        script_analysis = self._analyze_script(cleaned_text)
        
        # Statistical analysis using multiple methods
        statistical_result = self._statistical_analysis(cleaned_text)
        
        # Pattern-based analysis
        pattern_result = self._pattern_analysis(cleaned_text)
        
        # Combine results
        combined_result = self._combine_analyses(
            script_analysis, statistical_result, pattern_result, cleaned_text
        )
        
        return combined_result

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for analysis"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove URLs, emails, and other non-linguistic content
        text = re.sub(r'http[s]?://\S+|www\.\S+', '', text)
        text = re.sub(r'\S+@\S+\.\S+', '', text)
        text = re.sub(r'[^\w\s\u0900-\u097F\u0020-\u007E]', '', text)
        
        return text.strip()

    def _analyze_script(self, text: str) -> Dict[str, float]:
        """Analyze script composition of the text"""
        total_chars = len(text.replace(' ', ''))
        if total_chars == 0:
            return {"devanagari": 0.0, "latin": 0.0, "other": 0.0}
        
        devanagari_count = 0
        latin_count = 0
        other_count = 0
        
        for char in text:
            if char.isspace():
                continue
                
            char_code = ord(char)
            
            # Check if character is Devanagari
            is_devanagari = any(
                start <= char_code <= end 
                for start, end in self.devanagari_range
            )
            
            if is_devanagari:
                devanagari_count += 1
            elif char.isascii() and char.isalpha():
                latin_count += 1
            else:
                other_count += 1
        
        return {
            "devanagari": devanagari_count / total_chars,
            "latin": latin_count / total_chars,
            "other": other_count / total_chars
        }

    def _statistical_analysis(self, text: str) -> Dict[str, float]:
        """Use statistical language detection if available"""
        if not detect or not detect_langs:
            logger.warning("langdetect not available, using fallback analysis")
            return self._fallback_analysis(text)
        
        try:
            # Get language probabilities
            langs = detect_langs(text)
            result = {}
            
            for lang_prob in langs:
                if lang_prob.lang in ['hi', 'en']:
                    result[lang_prob.lang] = lang_prob.prob
                elif lang_prob.lang in ['ur', 'ne', 'mr']:  # Related languages
                    result['hi'] = result.get('hi', 0) + (lang_prob.prob * 0.5)
                
            # Normalize probabilities
            total = sum(result.values())
            if total > 0:
                result = {k: v/total for k, v in result.items()}
            
            return result
            
        except (LangDetectException, Exception) as e:
            logger.warning(f"Statistical analysis failed: {e}")
            return self._fallback_analysis(text)

    def _pattern_analysis(self, text: str) -> Dict[str, float]:
        """Analyze text using predefined patterns and indicators"""
        text_lower = text.lower()
        words = text_lower.split()
        
        hindi_score = 0
        english_score = 0
        total_words = len(words)
        
        if total_words == 0:
            return {"hi": 0.0, "en": 0.0}
        
        # Check for Hindi indicators
        for word in self.hindi_indicators["words"]:
            if word in text_lower:
                hindi_score += text_lower.count(word)
        
        for pattern in self.hindi_indicators["patterns"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            hindi_score += len(matches)
        
        # Check for English indicators
        for word in self.english_indicators["words"]:
            if word in words:
                english_score += words.count(word)
        
        for pattern in self.english_indicators["patterns"]:
            matches = re.findall(pattern, text, re.IGNORECASE)
            english_score += len(matches) * 0.5  # Lower weight for common patterns
        
        # Normalize scores
        total_score = hindi_score + english_score
        if total_score == 0:
            return {"hi": 0.5, "en": 0.5}
        
        return {
            "hi": hindi_score / total_score,
            "en": english_score / total_score
        }

    def _fallback_analysis(self, text: str) -> Dict[str, float]:
        """Fallback analysis when statistical detection is not available"""
        # Simple character-based analysis
        script_analysis = self._analyze_script(text)
        
        # High Devanagari ratio indicates Hindi
        if script_analysis["devanagari"] > 0.3:
            return {"hi": 0.8, "en": 0.2}
        # High Latin ratio indicates English
        elif script_analysis["latin"] > 0.7:
            return {"en": 0.8, "hi": 0.2}
        # Mixed or ambiguous
        else:
            return {"hi": 0.5, "en": 0.5}

    def _combine_analyses(self, script_analysis: Dict, statistical_result: Dict, 
                         pattern_result: Dict, text: str) -> DetectionResult:
        """Combine different analysis results into final detection"""
        
        # Weight different analyses
        weights = {
            "script": 0.4,
            "statistical": 0.4,
            "pattern": 0.2
        }
        
        # Convert script analysis to language probabilities
        script_lang_prob = {}
        if script_analysis["devanagari"] > 0.1:
            script_lang_prob["hi"] = script_analysis["devanagari"]
        if script_analysis["latin"] > 0.1:
            script_lang_prob["en"] = script_analysis["latin"]
        
        # Normalize script probabilities
        script_total = sum(script_lang_prob.values())
        if script_total > 0:
            script_lang_prob = {k: v/script_total for k, v in script_lang_prob.items()}
        else:
            script_lang_prob = {"hi": 0.5, "en": 0.5}
        
        # Combine all analyses
        combined_scores = {"hi": 0.0, "en": 0.0}
        
        for lang in ["hi", "en"]:
            combined_scores[lang] = (
                script_lang_prob.get(lang, 0) * weights["script"] +
                statistical_result.get(lang, 0) * weights["statistical"] +
                pattern_result.get(lang, 0) * weights["pattern"]
            )
        
        # Normalize final scores
        total_score = sum(combined_scores.values())
        if total_score > 0:
            combined_scores = {k: v/total_score for k, v in combined_scores.items()}
        
        # Determine primary language and mixed status
        primary_lang = max(combined_scores, key=combined_scores.get)
        confidence = combined_scores[primary_lang]
        
        # Check if text is mixed language
        min_lang_ratio = min(combined_scores.values())
        is_mixed = min_lang_ratio > self.preferences["mixed_threshold"]
        
        # Determine script type
        if script_analysis["devanagari"] > 0.5:
            script_type = "devanagari"
        elif script_analysis["latin"] > 0.5:
            script_type = "latin"
        else:
            script_type = "mixed"
        
        return DetectionResult(
            primary_language=primary_lang,
            confidence=confidence,
            script_type=script_type,
            is_mixed=is_mixed,
            language_distribution=combined_scores
        )

    def is_hindi_text(self, text: str) -> bool:
        """Check if text is primarily Hindi"""
        result = self.detect_language(text)
        return result in ["hi", "hi-en"]

    def is_english_text(self, text: str) -> bool:
        """Check if text is primarily English"""
        result = self.detect_language(text)
        return result in ["en", "hi-en"]

    def has_devanagari_script(self, text: str) -> bool:
        """Check if text contains Devanagari script"""
        script_analysis = self._analyze_script(text)
        return script_analysis["devanagari"] > 0.0

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return ["hi", "en", "hi-en"]

    def get_preferences(self) -> Dict:
        """Get current preferences"""
        return self.preferences.copy()

    def update_preferences(self, new_preferences: Dict):
        """Update detection preferences"""
        self.preferences.update(new_preferences)
        logger.info(f"Updated language detection preferences: {self.preferences}")

    def set_default_language(self, lang: str):
        """Set default language for ambiguous cases"""
        if lang in ["hi", "en"]:
            self.preferences["default_language"] = lang
            logger.info(f"Set default language to: {lang}")
        else:
            logger.warning(f"Unsupported default language: {lang}")

if __name__ == "__main__":
    # Test the language detector
    detector = LanguageDetector()
    
    test_texts = [
        "Hello, how are you?",
        "नमस्ते, आप कैसे हैं?",
        "Hi, मैं ठीक हूँ। How about you?",
        "Aap kaise hain? I am fine.",
        "यह एक mixed language sentence है।"
    ]
    
    for text in test_texts:
        result = detector.detect_detailed(text)
        print(f"\nText: {text}")
        print(f"Primary Language: {result.primary_language}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Script Type: {result.script_type}")
        print(f"Is Mixed: {result.is_mixed}")
        print(f"Distribution: {result.language_distribution}") 