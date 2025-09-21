#!/usr/bin/env python3
"""
Agentic AI Business Opportunity Explorer
Exercise for Lab 1 - Foundation concepts
"""

import os
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AgenticAIExplorer:
    def __init__(self):
        load_dotenv()  # Actually load the environment variables!
        self.setup_client()

    def setup_client(self) -> None:
        """Initialize OpenAI client based on environment configuration."""
        ollama_base_url = os.getenv('OLLAMA_BASE_URL')
        ollama_api_key = os.getenv('OLLAMA_API_KEY')

        if ollama_base_url and ollama_api_key:
            self.client = OpenAI(
                base_url=ollama_base_url,
                api_key=ollama_api_key
            )
            self.model = "gemma3:12b"
            logger.info(f"Using Ollama model at {ollama_base_url}")
        else:
            self.client = OpenAI()
            self.model = "gpt-3.5-turbo"  # Default OpenAI model
            logger.info("Using OpenAI API")

    def get_llm_response(self, messages: List[Dict[str, str]]) -> str:
        """Get response from LLM with error handling."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages, # type: ignore
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise

    def explore_business_opportunity(self) -> Dict[str, str]:
        """Execute the three-step business opportunity exploration."""
        prompts = {
            "business_area": "Please pick a business area that might be worth exploring for an Agentic AI opportunity.",
            "pain_point": "Please present a pain-point in that industry, something challenging that might be ripe for an Agentic solution.",
            "solution": "Please propose an Agentic AI solution to the pain-point."
        }

        messages = []
        results = {}

        for step, prompt in prompts.items():
            logger.info(f"Processing step: {step}")
            messages.append({"role": "user", "content": prompt})

            try:
                response = self.get_llm_response(messages)
                results[step] = response
                messages.append({"role": "assistant", "content": response})
                logger.info(f"Completed step: {step}")
            except Exception as e:
                logger.error(f"Failed at step {step}: {e}")
                raise

        return results

def main():
    """Main execution function."""
    try:
        explorer = AgenticAIExplorer()
        results = explorer.explore_business_opportunity()

        print("\n" + "="*60)
        print("AGENTIC AI BUSINESS OPPORTUNITY ANALYSIS")
        print("="*60)
        print(f"\n🏢 Business Area:\n{results['business_area']}")
        print(f"\n⚠️  Pain Point:\n{results['pain_point']}")
        print(f"\n🤖 Agentic AI Solution:\n{results['solution']}")
        print("\n" + "="*60)

    except Exception as e:
        logger.error(f"Application failed: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())

