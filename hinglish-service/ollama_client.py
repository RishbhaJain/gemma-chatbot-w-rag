#!/usr/bin/env python3
"""
Ollama Client for Hinglish Chatbot
Interface with Ollama API for Gemma 3n model with Hinglish context processing
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Union, Any

from prompts import get_system_prompt, build_custom_prompt, VOICE_PROMPT

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    ollama = None

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    aiohttp = None

logger = logging.getLogger(__name__)

class OllamaClient:
    """Ollama client for Gemma 3n with Hinglish support"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model_name = "gemma3n:latest"  # Using Gemma 2 9B model
        self.session = None
        
        # Hinglish-specific configuration
        self.config = {
            "temperature": 0.7,
            "max_tokens": 500,
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1,
            "timeout": 30,
            "hinglish_mode": True,
            "cultural_context": True
        }
        
        # Load system prompts from external file
        self.default_prompt_type = "hinglish"
        
        # Enhanced conversation history for better context
        self.conversation_history = []
        self.max_history_length = 15  # Increased for better memory
        self.conversation_context = {
            "user_name": None,
            "topics_discussed": [],
            "user_preferences": {},
            "conversation_mood": "neutral",
            "last_question_asked": None
        }
        
        # RAG system integration
        self.rag_pipeline = None
        self.rag_enabled = False
        
        logger.info(f"Ollama client initialized for {self.base_url}")

    async def initialize(self):
        """Initialize the Ollama client and check model availability"""
        logger.info("Initializing Ollama client...")
        
        if not OLLAMA_AVAILABLE and not AIOHTTP_AVAILABLE:
            raise RuntimeError("Neither ollama package nor aiohttp available. Install with: pip install ollama aiohttp")
        
        # Create HTTP session
        if AIOHTTP_AVAILABLE:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config["timeout"])
            )
        
        # Check if Ollama is running
        try:
            await self._check_ollama_status()
            logger.info("Ollama server is running")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {e}")
            raise
        
        # Check if model is available
        try:
            await self._ensure_model_available()
            logger.info(f"Model {self.model_name} is available")
        except Exception as e:
            logger.error(f"Model {self.model_name} not available: {e}")
            raise
        
        logger.info("Ollama client initialized successfully")

    async def _check_ollama_status(self):
        """Check if Ollama server is running"""
        if OLLAMA_AVAILABLE:
            try:
                # Use ollama package if available
                models = await asyncio.get_event_loop().run_in_executor(
                    None, ollama.list
                )
                return True
            except Exception as e:
                logger.error(f"Ollama status check failed: {e}")
                raise
        
        elif self.session:
            # Fallback to direct HTTP
            try:
                async with self.session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        return True
                    else:
                        raise Exception(f"Ollama returned status {response.status}")
            except Exception as e:
                logger.error(f"HTTP status check failed: {e}")
                raise

    async def _ensure_model_available(self):
        """Ensure the required model is available"""
        try:
            # List available models
            if OLLAMA_AVAILABLE:
                models_response = await asyncio.get_event_loop().run_in_executor(
                    None, ollama.list
                )
                available_models = [model['name'] for model in models_response['models']]
            else:
                async with self.session.get(f"{self.base_url}/api/tags") as response:
                    models_data = await response.json()
                    available_models = [model['name'] for model in models_data['models']]
            
            # Check if our model is available
            if self.model_name not in available_models:
                logger.warning(f"Model {self.model_name} not found. Available models: {available_models}")
                
                # Try to pull the model
                logger.info(f"Attempting to pull model {self.model_name}...")
                await self._pull_model()
            
        except Exception as e:
            logger.error(f"Failed to check model availability: {e}")
            raise

    async def _pull_model(self):
        """Pull the required model"""
        try:
            if OLLAMA_AVAILABLE:
                await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: ollama.pull(self.model_name)
                )
            else:
                # Use HTTP API
                pull_data = {"name": self.model_name}
                async with self.session.post(
                    f"{self.base_url}/api/pull", 
                    json=pull_data
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Failed to pull model: {response.status}")
            
            logger.info(f"Successfully pulled model {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to pull model {self.model_name}: {e}")
            raise

    async def get_response(self, user_input: str, language_hint: str = None, scenario: str = None, cultural_context: str = None) -> str:
        """
        Get AI response for user input
        
        Args:
            user_input: User's input text
            language_hint: Detected language hint ('hi', 'en', 'hi-en')
            
        Returns:
            AI response text
        """
        if not user_input or not user_input.strip():
            return "मुझे समझ नहीं आया। कृपया कुछ कहें।" if language_hint == "hi" else "I didn't understand. Please say something."
        
        try:
            # Select appropriate system prompt
            system_prompt = self._get_system_prompt(language_hint, scenario, cultural_context)
            
            # Build conversation context
            messages = self._build_messages(user_input, system_prompt)
            
            # Generate response
            response = await self._generate_response(messages)
            
            # Update conversation history
            self._update_history(user_input, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to get AI response: {e}")
            error_msg = "क्षमा करें, कुछ तकनीकी समस्या है।" if language_hint == "hi" else "Sorry, there's a technical issue."
            return error_msg

    def _get_system_prompt(self, language_hint: str = None, scenario: str = None, cultural_context: str = None) -> str:
        """Get appropriate system prompt based on language and context"""
        # Determine base prompt type
        if not self.config["hinglish_mode"]:
            base_type = "english_only"
        elif language_hint == "hi":
            base_type = "hindi_only"
        elif language_hint == "en":
            base_type = "english_only"
        else:  # Mixed or unknown
            base_type = "hinglish"
        
        # Build custom prompt if additional context provided
        if scenario or cultural_context:
            return build_custom_prompt(
                base_type=base_type,
                scenario=scenario,
                cultural_context=cultural_context
            )
        
        return get_system_prompt(base_type)
    
    def set_voice_mode(self, enabled: bool = True):
        """Enable/disable voice-optimized prompts"""
        self.config["voice_mode"] = enabled
    
    def get_voice_prompt(self) -> str:
        """Get voice-optimized prompt"""
        return VOICE_PROMPT

    def _build_messages(self, user_input: str, system_prompt: str) -> List[Dict]:
        """Build message list for enhanced conversational flow"""
        # Enhanced system prompt with conversation context
        enhanced_prompt = self._enhance_system_prompt(system_prompt, user_input)
        messages = [{"role": "system", "content": enhanced_prompt}]
        
        # Add conversation history for context (more recent messages for better flow)
        recent_history = self.conversation_history[-8:]  # Last 8 exchanges for better context
        for entry in recent_history:
            messages.append({"role": "user", "content": entry["user"]})
            messages.append({"role": "assistant", "content": entry["assistant"]})
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    def _enhance_system_prompt(self, base_prompt: str, current_input: str) -> str:
        """Enhance system prompt with conversational context"""
        enhancements = []
        
        # Add conversation continuity instructions
        if self.conversation_history:
            enhancements.append("\n\nConversational context:")
            enhancements.append("- This is an ongoing conversation. Reference previous exchanges naturally when relevant.")
            enhancements.append("- Ask follow-up questions based on what the user has shared before.")
            enhancements.append("- Remember the user's concerns, interests, and previous topics.")
            
            # Add specific context based on history
            if self.conversation_context["topics_discussed"]:
                topics = ", ".join(self.conversation_context["topics_discussed"][-3:])
                enhancements.append(f"- Recent topics discussed: {topics}")
            
            if self.conversation_context["user_name"]:
                enhancements.append(f"- User's name: {self.conversation_context['user_name']}")
            
            if self.conversation_context["last_question_asked"]:
                enhancements.append(f"- You previously asked: {self.conversation_context['last_question_asked']}")
                enhancements.append("- Follow up on this appropriately if the user responds to it.")
        
        # Add conversational behavior instructions
        enhancements.append("\n\nConversational guidelines:")
        enhancements.append("- Always acknowledge what the user just said before responding.")
        enhancements.append("- Ask engaging follow-up questions to keep the conversation flowing.")
        enhancements.append("- Show genuine interest in the user's thoughts and feelings.")
        enhancements.append("- Make connections between current and previous topics when natural.")
        enhancements.append("- Use the user's name occasionally if you know it.")
        enhancements.append("- Respond in a warm, friendly tone that encourages more sharing.")
        
        return base_prompt + "".join(enhancements)

    async def _generate_response(self, messages: List[Dict]) -> str:
        """Generate response using Ollama"""
        try:
            if OLLAMA_AVAILABLE:
                # Use ollama package
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._ollama_chat,
                    messages
                )
                return response['message']['content']
            
            else:
                # Use HTTP API
                return await self._http_chat(messages)
                
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            raise

    def _ollama_chat(self, messages: List[Dict]) -> Dict:
        """Use ollama package for chat"""
        return ollama.chat(
            model=self.model_name,
            messages=messages,
            options={
                "temperature": self.config["temperature"],
                "top_p": self.config["top_p"],
                "num_predict": self.config["max_tokens"]
            }
        )

    async def _http_chat(self, messages: List[Dict]) -> str:
        """Use HTTP API for chat"""
        chat_data = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.config["temperature"],
                "top_p": self.config["top_p"],
                "num_predict": self.config["max_tokens"]
            }
        }
        
        async with self.session.post(
            f"{self.base_url}/api/chat",
            json=chat_data
        ) as response:
            if response.status == 200:
                result = await response.json()
                return result['message']['content']
            else:
                raise Exception(f"HTTP chat failed: {response.status}")

    def _update_history(self, user_input: str, ai_response: str):
        """Update conversation history with enhanced context tracking"""
        import re
        
        # Add to conversation history
        self.conversation_history.append({
            "user": user_input,
            "assistant": ai_response,
            "timestamp": time.time()
        })
        
        # Extract and update conversation context
        self._extract_conversation_context(user_input, ai_response)
        
        # Keep only recent history
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
    
    def _extract_conversation_context(self, user_input: str, ai_response: str):
        """Extract meaningful context from the conversation"""
        import re
        
        # Extract user name if mentioned
        name_patterns = [
            r"मेरा नाम (.+?) है",
            r"मैं (.+?) हूं",
            r"my name is (.+?)[\.\,\!]",
            r"i am (.+?)[\.\,\!]",
            r"call me (.+?)[\.\,\!]"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                name = match.group(1).strip()
                if len(name.split()) <= 2:  # Reasonable name length
                    self.conversation_context["user_name"] = name
                break
        
        # Extract topics/subjects mentioned
        topic_keywords = [
            "school", "college", "study", "exam", "job", "career", "family", "friends",
            "math", "science", "english", "hindi", "future", "dreams", "pressure",
            "स्कूल", "कॉलेज", "पढ़ाई", "परीक्षा", "नौकरी", "करियर", "परिवार", "दोस्त",
            "गणित", "विज्ञान", "अंग्रेजी", "हिंदी", "भविष्य", "सपने", "दबाव"
        ]
        
        mentioned_topics = []
        text_to_check = (user_input + " " + ai_response).lower()
        for topic in topic_keywords:
            if topic in text_to_check:
                mentioned_topics.append(topic)
        
        # Add new topics to discussion history
        for topic in mentioned_topics:
            if topic not in self.conversation_context["topics_discussed"]:
                self.conversation_context["topics_discussed"].append(topic)
        
        # Keep only recent topics (last 10)
        if len(self.conversation_context["topics_discussed"]) > 10:
            self.conversation_context["topics_discussed"] = self.conversation_context["topics_discussed"][-10:]
        
        # Extract questions asked by AI for follow-up
        question_patterns = [
            r"(.+\?)\s*$",  # Sentences ending with ?
            r"(क्या .+?\?)",  # Hindi questions starting with क्या
            r"(कैसे .+?\?)",  # Hindi questions starting with कैसे
            r"(कौन .+?\?)",   # Hindi questions starting with कौन
        ]
        
        for pattern in question_patterns:
            match = re.search(pattern, ai_response)
            if match:
                question = match.group(1).strip()
                if len(question) < 200:  # Reasonable question length
                    self.conversation_context["last_question_asked"] = question
                break
        
        # Detect conversation mood based on keywords
        positive_words = ["good", "great", "happy", "excited", "अच्छा", "खुश", "प्रसन्न"]
        negative_words = ["sad", "worried", "stressed", "problem", "डर", "चिंता", "परेशान", "समस्या"]
        
        if any(word in text_to_check for word in positive_words):
            self.conversation_context["conversation_mood"] = "positive"
        elif any(word in text_to_check for word in negative_words):
            self.conversation_context["conversation_mood"] = "concerned"
        else:
            self.conversation_context["conversation_mood"] = "neutral"

    async def stream_response(self, user_input: str, language_hint: str = None, scenario: str = None, cultural_context: str = None):
        """
        Get streaming response for real-time chat
        
        Args:
            user_input: User's input text
            language_hint: Detected language hint
            scenario: Specialized scenario for context
            cultural_context: Cultural context for appropriate responses
            
        Yields:
            Response chunks as they arrive
        """
        try:
            system_prompt = self._get_system_prompt(language_hint, scenario, cultural_context)
            messages = self._build_messages(user_input, system_prompt)
            
            if OLLAMA_AVAILABLE:
                # Stream using ollama package
                response_text = ""
                stream = ollama.chat(
                    model=self.model_name,
                    messages=messages,
                    stream=True,
                    options={
                        "temperature": self.config["temperature"],
                        "top_p": self.config["top_p"],
                        "num_predict": self.config["max_tokens"]
                    }
                )
                
                for chunk in stream:
                    content = chunk['message']['content']
                    response_text += content
                    yield content
                
                # Update history with complete response
                self._update_history(user_input, response_text)
            
            else:
                # Stream using HTTP API
                chat_data = {
                    "model": self.model_name,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": self.config["temperature"],
                        "top_p": self.config["top_p"],
                        "num_predict": self.config["max_tokens"]
                    }
                }
                
                response_text = ""
                async with self.session.post(
                    f"{self.base_url}/api/chat",
                    json=chat_data
                ) as response:
                    async for line in response.content:
                        if line:
                            try:
                                chunk_data = json.loads(line.decode('utf-8'))
                                content = chunk_data.get('message', {}).get('content', '')
                                if content:
                                    response_text += content
                                    yield content
                            except json.JSONDecodeError:
                                continue
                
                self._update_history(user_input, response_text)
                
        except Exception as e:
            logger.error(f"Streaming response failed: {e}")
            error_msg = "क्षमा करें, स्ट्रीमिंग में समस्या है।" if language_hint == "hi" else "Sorry, streaming failed."
            yield error_msg

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")

    def get_history(self) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history.copy()

    def update_config(self, new_config: Dict):
        """Update client configuration"""
        self.config.update(new_config)
        logger.info(f"Updated Ollama config: {new_config}")

    def get_config(self) -> Dict:
        """Get current configuration"""
        return self.config.copy()

    def set_model(self, model_name: str):
        """Change the model"""
        self.model_name = model_name
        logger.info(f"Model changed to: {model_name}")

    async def test_connection(self) -> Dict:
        """Test connection and model availability"""
        try:
            await self._check_ollama_status()
            test_response = await self.get_response("Hello, testing connection.", "en")
            
            return {
                "status": "success",
                "model": self.model_name,
                "test_response": test_response[:100] + "..." if len(test_response) > 100 else test_response
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up Ollama client...")
        
        if self.session and not self.session.closed:
            await self.session.close()
        
        self.conversation_history = []
        logger.info("Ollama client cleanup completed")
    
    def clear_conversation(self):
        """Clear conversation history and context"""
        self.conversation_history = []
        self.conversation_context = {
            "user_name": None,
            "topics_discussed": [],
            "user_preferences": {},
            "conversation_mood": "neutral",
            "last_question_asked": None
        }

    def get_conversation_history(self):
        """Get current conversation history"""
        return self.conversation_history.copy()
    
    def get_conversation_context(self):
        """Get current conversation context for debugging/analysis"""
        return self.conversation_context.copy()
    
    def set_user_name(self, name: str):
        """Manually set user name for personalization"""
        self.conversation_context["user_name"] = name
    
    def add_user_preference(self, key: str, value: str):
        """Add user preference for better personalization"""
        self.conversation_context["user_preferences"][key] = value
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the current conversation state"""
        history_count = len(self.conversation_history)
        topics = ", ".join(self.conversation_context["topics_discussed"][-3:]) if self.conversation_context["topics_discussed"] else "None"
        
        summary = f"""Conversation Summary:
- Messages exchanged: {history_count}
- User name: {self.conversation_context['user_name'] or 'Unknown'}
- Recent topics: {topics}
- Conversation mood: {self.conversation_context['conversation_mood']}
- Last question asked: {self.conversation_context['last_question_asked'] or 'None'}"""
        
        return summary
    
    # RAG Integration Methods
    
    def initialize_rag(self, rag_pipeline):
        """Initialize RAG pipeline for enhanced responses"""
        try:
            self.rag_pipeline = rag_pipeline
            self.rag_enabled = True
            logger.info("RAG pipeline initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {e}")
            self.rag_enabled = False
    
    async def get_response_with_rag(
        self, 
        user_input: str, 
        language_hint: str = None, 
        scenario: str = "guidance_counselor",
        cultural_context: str = None,
        k: int = 3,
        similarity_threshold: float = 0.7
    ) -> str:
        """Get AI response enhanced with RAG retrieval"""
        try:
            if not self.rag_enabled or not self.rag_pipeline:
                logger.warning("RAG not enabled, falling back to standard response")
                return await self.get_response(user_input, language_hint, scenario, cultural_context)
            
            # Retrieve relevant context
            logger.debug(f"Retrieving context for: {user_input[:100]}...")
            retrieval_result = await self.rag_pipeline.query(
                question=user_input,
                k=k,
                similarity_threshold=similarity_threshold
            )
            
            # Check if relevant context was found
            if retrieval_result.total_chunks == 0:
                logger.info("No relevant context found, using standard response")
                return await self.get_response(user_input, language_hint, scenario, cultural_context)
            
            # Format context and sources
            context = retrieval_result.context
            sources = retrieval_result.sources
            sources_text = "; ".join(sources) if sources else "Various guidance resources"
            
            # Build RAG-enhanced prompt
            from prompts import COUNSELOR_RAG_PROMPT
            
            enhanced_prompt = COUNSELOR_RAG_PROMPT.format(
                retrieved_context=context,
                source_citations=sources_text
            )
            
            # Build messages with RAG context
            messages = self._build_messages(user_input, enhanced_prompt)
            
            # Get response from Ollama
            response = await self._call_ollama(messages)
            
            # Update conversation history
            self._update_history(user_input, response)
            
            logger.info(f"Generated RAG-enhanced response using {retrieval_result.total_chunks} chunks")
            return response
            
        except Exception as e:
            logger.error(f"Error in RAG-enhanced response: {e}")
            # Fall back to standard response
            return await self.get_response(user_input, language_hint, scenario, cultural_context)
    
    def get_rag_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics"""
        if not self.rag_enabled or not self.rag_pipeline:
            return {"rag_enabled": False, "error": "RAG not initialized"}
        
        try:
            return {
                "rag_enabled": True,
                "system_stats": self.rag_pipeline.get_system_stats(),
                "health": self.rag_pipeline.health_check()
            }
        except Exception as e:
            logger.error(f"Error getting RAG stats: {e}")
            return {"rag_enabled": True, "error": str(e)}
    
    async def test_rag_system(self) -> Dict[str, Any]:
        """Test the RAG system with sample queries"""
        if not self.rag_enabled or not self.rag_pipeline:
            return {"error": "RAG not initialized"}
        
        try:
            test_queries = [
                "How should I choose my career?",
                "I'm feeling stressed about my exams",
                "My parents want me to be an engineer but I want to study art"
            ]
            
            results = []
            for query in test_queries:
                start_time = time.time()
                response = await self.get_response_with_rag(query)
                end_time = time.time()
                
                results.append({
                    "query": query,
                    "response_length": len(response),
                    "response_time": end_time - start_time,
                    "has_citations": "Source:" in response or "[Source" in response
                })
            
            return {
                "test_results": results,
                "rag_system_test": await self.rag_pipeline.test_system() if hasattr(self.rag_pipeline, 'test_system') else None
            }
            
        except Exception as e:
            logger.error(f"Error testing RAG system: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    # Test the Ollama client
    async def test_ollama():
        client = OllamaClient()
        
        try:
            await client.initialize()
            
            # Test different language inputs
            test_inputs = [
                ("Hello, how are you?", "en"),
                ("नमस्ते, आप कैसे हैं?", "hi"),
                ("Hi, मैं ठीक हूँ। How about you?", "hi-en")
            ]
            
            for text, lang in test_inputs:
                print(f"\nTesting: {text} (lang: {lang})")
                response = await client.get_response(text, lang)
                print(f"Response: {response}")
            
            # Test streaming
            print("\nTesting streaming response:")
            async for chunk in client.stream_response("Tell me about India", "en"):
                print(chunk, end="", flush=True)
            print()  # New line
            
        except Exception as e:
            print(f"Test failed: {e}")
        
        finally:
            await client.cleanup()
    
    asyncio.run(test_ollama()) 