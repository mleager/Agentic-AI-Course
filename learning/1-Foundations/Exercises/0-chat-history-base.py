# Exercise for Lab 1
# 1. Ask the LLM to pick a business area that might be worth exploring for an Agentic AI opportunity.
# 2. Ask the LLM to present a pain-point in that industry - something challenging that might be ripe for an Agentic solution.
# 3. Have the LLM call propose the Agentic AI solution.


from dotenv import load_dotenv
from openai import OpenAI
import os


# 1. Set ollama base URL and API key from environment variables
ollama_base_url = os.getenv('OLLAMA_BASE_URL')
ollama_api_key = os.getenv('OLLAMA_API_KEY')
ollama_model = "gemma3:12b"

if ollama_base_url:
    print(f"Base URL for Ollama: {ollama_base_url}")


# 2. If Ollama base URL and API key are provided, use Ollama for model inference
if ollama_api_key:
    openai = OpenAI(
        base_url=ollama_base_url,
        api_key=ollama_api_key
    )
    print("Using Ollama model...")
else:
    openai = OpenAI()
    print("Using Remote API Key...")


# 3. Create all 3 prompts at once
prompt_one = "Please pick a business area that might be worth exploring for an Agentic AI opportunity."
prompt_two = "Please present a pain-point in that industry, something challenging that might be ripe for an Agentic solution."
prompt_three = "Please propose an Agentic AI solution to the pain-point."


# 4. Ask the LLM the first prompt
messages: list = [{"role": "user", "content": prompt_one}]


# 5. Ask the LLM for the first prompt's response
response = openai.chat.completions.create(
    model=ollama_model,
    messages=messages
)

# 6. Save Model's Response
answer_one = response.choices[0].message.content

# 7. Append the response to our history
messages.append({"role": "assistant", "content": answer_one})


# 8. Add the next prompt to our history
messages.append({"role": "user", "content": prompt_two})


# 9. Ask the LLM for the Pain Point solution
response = openai.chat.completions.create(
    model=ollama_model,
    messages=messages
)


# 10. Save Model's 2nd Response
answer_two = response.choices[0].message.content

# 11. Append the response to our history
messages.append({"role": "assistant", "content": answer_two})


# 12. Add the Agentic AI Solution prompt to our history
messages.append({"role": "user", "content": prompt_three})


# 13. Ask the LLM for the final Agentic AI solution
response = openai.chat.completions.create(
    model=ollama_model,
    messages=messages
)


# 14. Save final Agentic AI Solution's Response
answer_three = response.choices[0].message.content

print(f"Business area: {answer_one}")
print(f"Pain-point: {answer_two}")
print(f"Agentic AI solution: {answer_three}")

