#!/usr/bin/env python3
"""
Demo: How to maintain conversation context with LLMs
Shows the difference between stateless calls and context preservation
"""

import os
import logging
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationManager:
    def __init__(self):
        load_dotenv()
        self.setup_client()
        # This is our conversation memory - the key concept!
        self.conversation_history: List[Dict[str, str]] = []

    def setup_client(self):
        """Setup OpenAI client (same as before)"""
        ollama_base_url = os.getenv('OLLAMA_BASE_URL')
        ollama_api_key = os.getenv('OLLAMA_API_KEY')

        if ollama_base_url and ollama_api_key:
            self.client = OpenAI(base_url=ollama_base_url, api_key=ollama_api_key)
            self.model = "gemma3:12b"
            logger.info("Using Ollama")
        else:
            self.client = OpenAI()
            self.model = "gpt-3.5-turbo"
            logger.info("Using OpenAI")

    def add_user_message(self, content: str) -> None:
        """Add a user message to conversation history"""
        self.conversation_history.append({
            "role": "user", 
            "content": content
        })
        logger.info(f"Added USER message: {content[:50]}...")

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant response to conversation history"""
        self.conversation_history.append({
            "role": "assistant", 
            "content": content
        })
        logger.info(f"Added ASSISTANT message: {content[:50]}...")

    def get_llm_response(self) -> str:
        """
        Send the ENTIRE conversation history to the LLM
        This is the key - we send everything each time!
        """
        logger.info(f"Sending {len(self.conversation_history)} messages to LLM")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,  # Send ALL messages
                temperature=0.7,
                max_tokens=1000
            )

            assistant_response = response.choices[0].message.content

            # Automatically add the response to our history
            self.add_assistant_message(assistant_response)

            return assistant_response

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def print_conversation_state(self) -> None:
        """Debug helper to see the conversation state"""
        print("\n" + "="*50)
        print("CURRENT CONVERSATION STATE:")
        print("="*50)
        for i, message in enumerate(self.conversation_history):
            role = message["role"].upper()
            content = message["content"][:100] + "..." if len(message["content"]) > 100 else message["content"]
            print(f"{i+1}. {role}: {content}")
        print("="*50 + "\n")

def demonstrate_conversation_flow():
    """Demonstrate how conversation context works"""

    print("🚀 DEMONSTRATION: How LLM Conversation Context Works\n")

    # Create our conversation manager
    conv = ConversationManager()

    # STEP 1: Ask for business area
    print("STEP 1: Asking for business area...")
    conv.add_user_message("Please pick a business area that might be worth exploring for an Agentic AI opportunity.")

    business_area_response = conv.get_llm_response()
    print(f"✅ Got business area response")

    # Show what's in memory now
    conv.print_conversation_state()

    # STEP 2: Ask for pain point (LLM remembers the business area!)
    print("STEP 2: Asking for pain point in THAT business area...")
    conv.add_user_message("Please present a pain-point in that industry, something challenging that might be ripe for an Agentic solution.")

    pain_point_response = conv.get_llm_response()
    print(f"✅ Got pain point response")

    # Show what's in memory now
    conv.print_conversation_state()

    # STEP 3: Ask for solution (LLM remembers business area AND pain point!)
    print("STEP 3: Asking for solution to THAT specific pain point...")
    conv.add_user_message("Please propose an Agentic AI solution to the pain-point.")

    solution_response = conv.get_llm_response()
    print(f"✅ Got solution response")

    # Final conversation state
    conv.print_conversation_state()

    # Display final results
    print("\n" + "🎯 FINAL RESULTS:")
    print("="*60)
    print(f"🏢 Business Area:\n{business_area_response}\n")
    print(f"⚠️  Pain Point:\n{pain_point_response}\n")
    print(f"🤖 Solution:\n{solution_response}\n")

if __name__ == "__main__":
    demonstrate_conversation_flow()

