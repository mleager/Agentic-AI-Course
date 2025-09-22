# Use one of the Agentic Design Patterns to implement the main function of:  
# "../../agents/1_foundations/2_lab2.ipynb"

# In 2_lab2.ipynb, it uses a Validator Pattern
# The last LLM call compares the LLM's responses and selects the best one

# Chosen Workflow Pattern: Orchestrator - Worker

# 1. Generate a complex question to ask all models
# 2. Receive Models' Answers  
# 3. Store Model Name and Answer in a List of LLMResult Objects
# 4. Have a reasoning model review all answers
# 5. Return a List of Model Names with Ranking and brief Explanation of why they were given their rank

import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from IPython.display import Markdown, display

load_dotenv(override=True)

# Globals
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_BASE_URL = os.getenv('GEMINI_BASE_URL')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL')
OLLAMA_API_KEY = "ollama"

# Data Structures
class LLMResult(BaseModel):
    model: str
    answer: str

# class ModelRanking(BaseModel):
#     rank: str
#     reason: str

# Step 1: Generate Question
def generator(prompt: str) -> str:
    message: list = [{"role": "user", "content": prompt}]

    openai = OpenAI()
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=message
    )
    return response.choices[0].message.content or ""

prompt = "Please come up with a challenging, nuanced question that I can ask a number of LLMs to evaluate their intelligence. "
prompt += "Please respond only with the question, no explanation."

question = generator(prompt)
print(f"Generated Question: {question}")

# Step 2 & 3: Get Model Answers and Store in LLMResult Objects
results: list[LLMResult] = []
messages: list = [{"role": "user", "content": question}]

def gemini_answer() -> None:
    gemini = OpenAI(
        api_key=GEMINI_API_KEY,
        base_url=GEMINI_BASE_URL
    )

    model = "gemini-2.5-flash-lite"
    try:
        response = gemini.chat.completions.create(
            model=model,
            messages=messages
        )
        answer = response.choices[0].message.content or ""
        results.append(LLMResult(model=model, answer=answer))
        print(f"✓ Got response from {model}")
    except Exception as e:
        print(f"✗ Error with {model}: {e}")

def openai_answer() -> None:
    openai = OpenAI()

    model = "gpt-4o-mini"
    try:
        response = openai.chat.completions.create(
            model=model,
            messages=messages
        )
        answer = response.choices[0].message.content or ""
        results.append(LLMResult(model=model, answer=answer))
        print(f"✓ Got response from {model}")
    except Exception as e:
        print(f"✗ Error with {model}: {e}")

def ollama_answer() -> None:
    ollama = OpenAI(
        api_key=OLLAMA_API_KEY,
        base_url=OLLAMA_BASE_URL
    )

    model = "gemma3:12b"
    try:
        response = ollama.chat.completions.create(
            model=model,
            messages=messages
        )
        answer = response.choices[0].message.content or ""
        results.append(LLMResult(model=model, answer=answer))
        print(f"✓ Got response from {model}")
    except Exception as e:
        print(f"✗ Error with {model}: {e}")

# Execute all model calls
print("\nGathering responses from models...")
openai_answer()
gemini_answer()
ollama_answer()

# Step 4: Format responses for the reasoning model
together = ""
for i, res in enumerate(results, 1):
    together += f"## Response {i} from {res.model}:\n"
    together += f"{res.answer}\n\n"

# Create the comparison prompt
compare = f"""You are judging the responses of {len(results)} models. Each model was given the following question:

{question}

Please rank each model between 1 and {len(results)}, with 1 being the best, and {len(results)} being the worst.
Please output your response in JSON and only in JSON. It should contain the rank and a brief explanation why, following this exact format:

{{
    "result": {{
        "<MODEL_NAME>": {{
            "rank": "<RANK>",
            "reason": "<BRIEF_EXPLANATION>"
        }}
    }}
}}

Here is the content to review for ranking:

{together}
"""

print("\nHaving reasoning model evaluate responses...")

# Step 5: Get ranking from reasoning model
ranking_response = generator(compare)

# Parse and display results
try:
    json_ranking: dict = json.loads(ranking_response)
    rankings: dict = json_ranking["result"]

    # Sort by rank for better display
    sorted_rankings = sorted(rankings.items(), key=lambda x: int(x[1]["rank"]))

    print(f"\n🏆 MODEL RANKINGS 🏆")
    print("=" * 50)

    output = ""
    for model_name, ranking_data in sorted_rankings:
        rank = ranking_data["rank"]
        reason = ranking_data["reason"]
        output += f"**Rank {rank}: {model_name}**\n"
        output += f"*Reason:* {reason}\n\n"

    display(Markdown(output))

    # Also display the original question and summary
    summary_output = f"""
## Original Question
{question}

## Summary
- **Total Models Evaluated:** {len(results)}
- **Winner:** {sorted_rankings[0][0]} 
- **Evaluation Criteria:** Intelligence, reasoning, and response quality
"""
    display(Markdown(summary_output))

except (json.JSONDecodeError, KeyError) as e:
    print(f"Error parsing ranking response: {e}")
    print(f"Raw response: {ranking_response}")

    # Fallback display
    output = "**Error in ranking - showing raw response:**\n\n"
    output += ranking_response
    display(Markdown(output))

