from dotenv import load_dotenv
from openai import OpenAI
from IPython.display import Markdown, display
import os

"""
1. Load ENV values for API_KEY and BASE_URL
2. If OLLAMA_BASE_URL and OLLAMA_API_KEY are provided, use Ollama for model inference
3. Prepare a Prompt to send to the Model
4. Send the Prompt
5. Display the Model's Response
6. Prepare a Prompt for the Model to generate a question
7. The Model generates the question
8. Save the generated question 
9. Set the new Prompt to be the generated question
10. Prompt the Model to answer the question
11. Save the Model's Response
12. Display Response as Markdown
"""


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


# 3. Basic example of sending a prompt to a Model
messages: list = [{"role": "user", "content": "What is 2+2?"}]


# 4. Basic example of a model sending back a response
response = openai.chat.completions.create(
    model=ollama_model,
    messages=messages
)


# 5. Display the response from the model
print(response.choices[0].message.content)


# 6. Generate a question for assessing IQ
question = "Please propose a hard, challenging question to assess someone's IQ. Please respond only with the question."
messages = [{"role": "user", "content": question}]


# 7. Use Ollama to generate an IQ question
response = openai.chat.completions.create(
    model=ollama_model,
    messages=messages
)


# 8. Save the output of the Model's response
question = response.choices[0].message.content

print(question)


# 9. Set the Model's response to be a prompt back to the Model
message = [{"role": "user", "content": question}]


# 10. Ask the Model to answer the generated IQ question
response = openai.chat.completions.create(
    model=ollama_model,
    messages=messages
)


# 11. Save the output of the Model's response
answer = response.choices[0].message.content


# 12. Display the answer in Markdown format
display(Markdown(answer))

