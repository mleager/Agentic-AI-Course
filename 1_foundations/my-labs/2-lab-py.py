import os
import json
import logging
import re
from typing import List, Tuple
from openai import OpenAI
from dotenv import load_dotenv
import concurrent.futures

# Models: gpt-4o-mini, gpt-5-nano, gemini-2.5-flash, gemini-2.0-flash-lite
# 1. Generate a complex question
# 2. Have multiple models generate answers to the same question
# 3. Use original model to Rank the answers based on their relevance

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
OLLAMA_API_KEY = os.getenv('OLLAMA_API_KEY')
GEMINI_BASE_URL = 'https://generativelanguage.googleapis.com/v1beta/openai/'
OLLAMA_BASE_URL = 'https://localhost:11434/v1'


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMResult:
    def __init__(self, model: str, answer: str):
        self.model = model
        self.answer = answer


# Models to submit their answers to the complex question
class Model:
    def __init__(self, model_name, api_key, base_url=None):
        self.api_key = api_key
        self.model_name = model_name
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=api_key)

    def generate(self, prompt: str) -> LLMResult:
        message: list = [{"role": "user", "content": prompt}]

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=message 
            )
            logger.info(f"{self.model_name} generated a response...")
            content = response.choices[0].message.content or ""
            return LLMResult(model=self.model_name, answer=content)
        except Exception as e:
            logger.error(f"Error in {self.model_name}: {e}")
            return LLMResult(model=self.model_name, answer="")


class Validator(Model):
    def __init__(self, api_key, base_url=None):
        super().__init__("gpt-4o-mini", api_key, base_url)
        self.history = []

    def add_user_history(self, prompt: str):
        message = {"role": "user", "content": prompt}
        self.history.append(message)

    def add_assistant_history(self, prompt: str) -> None:
        message = {"role": "assistant", "content": prompt}
        self.history.append(message)

    def get_last_question(self) -> str:
        for message in reversed(self.history):
            if message["role"] == "user":
                return message["content"]
        logger.warning(f"No user history found.")
        return ""

    def generate_question(self):
        prompt = """Please create a complex, nuanced question about the current state of American politics. 
        Please keep the response concise. 
        Please only respond with the question, not an answer. Thank you."""

        self.add_user_history(prompt)
        answer = super().generate(prompt)
        self.add_assistant_history(answer.answer)

        logger.info(f"{self.model_name} generated a question...")

    def generate_review(self, results: List[LLMResult]) -> str:
        models_str = "\n".join([f"{model.model}: {model.answer}" for model in results])
        prompt = f"""I asked a complex, nuanced question to several peers. 
        Please review their responses, and rank them between 1 and {len(results)}.
        Rank 1 is the most relevant, and Rank {len(results)} is the least relevant.

        **I asked them all this same question:**

        {self.get_last_question()}

        **The responses for each are below:**

        {models_str}

        Please rank them in order of relevance, from most to least relevant using only JSON format.
        Please include only the model name and rank, in the following format:

        ```json
        {
            "results": [
                {"model": "model1", "rank": "1"},
                {"model": "model2", "rank": "2"},
                {"model": "model3", "rank": "3"},
                ...
            ]
        }
        ```
        """
        self.add_user_history(prompt)
        answer = super().generate(prompt)
        self.add_assistant_history(answer.answer)
        logger.info(f"{self.model_name} reviewed {len(results)} questions...")
        return answer.answer

    def output_rank(self, answer: str) -> str:
        try:
            response = json.loads(answer)
            rankings = response["results"]

            rankings.sort(key=lambda x: int(x["rank"]))

            output = ""
            for rank in rankings:
                model_name = rank["model"]
                model_rank = str(rank["rank"])
                output += f"{model_rank} : {model_name}\n"

            return output

        except Exception as e:
            return f"Error: {e}"


def get_model_responses(models: List[Model], question: str) -> List[LLMResult]:
    max_workers = min(len(models), 5)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_model = {executor.submit(model.generate, question): model for model in models}
        # futures = [executor.submit(model.generate, question) for model in models]

        results = []
        for future in concurrent.futures.as_completed(future_to_model, timeout=10):
            model = future_to_model[future]
            try:
                result = future.result()
                results.append(result)
                logger.info(f"{model.model_name} completed successfully")
            except Exception as e:
                logger.error(f"{model.model_name} failed: {e}")
                results.append(LLMResult(model=model.model_name, answer=f"Error: {e}"))

    return results

    #     results = []
    #     for future in concurrent.futures.as_completed(futures):
    #         try:
    #             result = future.result(timeout=10)
    #             results.append(result)
    #         except Exception as e:
    #             logger.error(f"Error: {e}")
    #             results.append(LLMResult(model="Unknown", answer=""))
    #
    # return results

def main():
    load_dotenv(override=True)
    validator = Validator(OPENAI_API_KEY)
    validator.generate_question()

    models = [
        Model("gpt-5-mini", OPENAI_API_KEY),
        Model("gemini-2.5-flash-lite", GEMINI_API_KEY, GEMINI_BASE_URL),
        Model("gemma3:12b", OLLAMA_API_KEY, OLLAMA_BASE_URL),
    ]

    results = get_model_responses(models, validator.get_last_question())

    json_rankings = validator.generate_review(results)
    print(validator.output_rank(json_rankings))


if __name__ == "__main__":
    main()

