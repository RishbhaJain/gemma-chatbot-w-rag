#!/usr/bin/env python3
"""
Example usage of the prompts system for Hinglish Chatbot
Demonstrates various ways to use prompts for different scenarios
"""

import asyncio
from prompts import (
    get_system_prompt, 
    build_custom_prompt, 
    get_specialized_prompt,
    get_cultural_prompt,
    DEFAULT_PROMPT,
    VOICE_PROMPT,
    CHAT_PROMPT,
    COUNSELOR_PROMPT
)
from ollama_client import OllamaClient

async def example_basic_prompts():
    """Example of basic prompt usage"""
    print("=== Basic Prompts ===")
    
    # Basic prompts
    print("Hinglish prompt:", get_system_prompt("hinglish")[:100] + "...")
    print("Hindi prompt:", get_system_prompt("hindi_only")[:100] + "...")
    print("English prompt:", get_system_prompt("english_only")[:100] + "...")
    print()

async def example_specialized_prompts():
    """Example of specialized prompt usage"""
    print("=== Specialized Prompts ===")
    
    # Voice assistant prompt
    voice_prompt = build_custom_prompt("hinglish", "voice_assistant")
    print("Voice prompt:", voice_prompt[:150] + "...")
    print()
    
    # Educational prompt
    educational_prompt = build_custom_prompt("hindi_only", "educational")
    print("Educational prompt:", educational_prompt[:150] + "...")
    print()
    
    # Technical help prompt
    tech_prompt = build_custom_prompt("hinglish", "technical_help")
    print("Technical prompt:", tech_prompt[:150] + "...")
    print()
    
    # Guidance counselor prompt
    counselor_prompt = build_custom_prompt("hinglish", "guidance_counselor")
    print("Counselor prompt:", counselor_prompt[:150] + "...")
    print()

async def example_cultural_context():
    """Example of cultural context prompts"""
    print("=== Cultural Context Prompts ===")
    
    # Festival context
    festival_prompt = build_custom_prompt(
        base_type="hinglish",
        scenario="casual_chat",
        cultural_context="festivals"
    )
    print("Festival context:", festival_prompt[:200] + "...")
    print()
    
    # Food context
    food_prompt = build_custom_prompt(
        base_type="hindi_only",
        cultural_context="food"
    )
    print("Food context:", food_prompt[:200] + "...")
    print()

async def example_ollama_client_usage():
    """Example of using prompts with OllamaClient"""
    print("=== OllamaClient with Custom Prompts ===")
    
    try:
        client = OllamaClient()
        await client.initialize()
        
        # Basic conversation
        print("Basic conversation:")
        response = await client.get_response("नमस्ते, आप कैसे हैं?", language_hint="hi")
        print(f"Response: {response[:100]}...")
        print()
        
        # Voice-optimized conversation
        print("Voice-optimized conversation:")
        response = await client.get_response(
            "Tell me about Diwali", 
            language_hint="en", 
            scenario="voice_assistant",
            cultural_context="festivals"
        )
        print(f"Response: {response[:100]}...")
        print()
        
        # Educational conversation
        print("Educational conversation:")
        response = await client.get_response(
            "समझाएं कि photosynthesis कैसे काम करता है", 
            language_hint="hinglish", 
            scenario="educational"
        )
        print(f"Response: {response[:100]}...")
        print()
        
        # Guidance counselor conversation
        print("Guidance counselor conversation:")
        response = await client.get_response(
            "I'm failing in math and my father is so angry. He says I'm wasting money and should just help on the farm", 
            language_hint="en", 
            scenario="guidance_counselor"
        )
        print(f"Response: {response[:100]}...")
        print()
        
    except Exception as e:
        print(f"Note: OllamaClient not available for demo: {e}")
        print("This is normal if Ollama is not running.")

async def example_quick_access_prompts():
    """Example of quick access prompts"""
    print("=== Quick Access Prompts ===")
    
    print("Default prompt:", DEFAULT_PROMPT[:100] + "...")
    print("Voice prompt:", VOICE_PROMPT[:100] + "...")
    print("Chat prompt:", CHAT_PROMPT[:100] + "...")
    print("Counselor prompt:", COUNSELOR_PROMPT[:100] + "...")
    print()

async def example_custom_scenarios():
    """Example of creating custom scenarios"""
    print("=== Custom Scenarios ===")
    
    # Customer service scenario
    customer_service_prompt = build_custom_prompt(
        base_type="hinglish",
        additional_instructions="""You are a customer service representative for an Indian e-commerce company. 
        Be helpful, polite, and understand common Indian shopping concerns. 
        Handle complaints with empathy and provide practical solutions."""
    )
    print("Customer service:", customer_service_prompt[:200] + "...")
    print()
    
    # Travel guide scenario
    travel_prompt = build_custom_prompt(
        base_type="hinglish",
        scenario="casual_chat",
        cultural_context="festivals",
        additional_instructions="""You are a knowledgeable travel guide for India. 
        Share interesting facts about places, festivals, and local customs. 
        Recommend authentic experiences and hidden gems."""
    )
    print("Travel guide:", travel_prompt[:200] + "...")
    print()

async def main():
    """Run all examples"""
    print("🎭 Hinglish Chatbot Prompts System Examples\n")
    
    await example_basic_prompts()
    await example_specialized_prompts()
    await example_cultural_context()
    await example_quick_access_prompts()
    await example_custom_scenarios()
    await example_ollama_client_usage()
    
    print("✅ All examples completed!")

if __name__ == "__main__":
    asyncio.run(main()) 