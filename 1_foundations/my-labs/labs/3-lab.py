import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
import gradio as gr


load_dotenv(override=True)


NAME = "Mark Leager"
OPENAI_MODEL = "gpt-4o-mini"
GEMINI_MODEL = "gemini-2.0-flash"

CHATBOT = OpenAI()
EVALUATOR = OpenAI(api_key=os.getenv("GEMINI_API_KEY"), base_url=os.getenv("GEMINI_BASE_URL"))

NAME = "Mark Leager"

with open(f"../../resume/resume.md", "r") as f:
    RESUME = f.read()

with open(f"../../resume/summary.txt", "r") as f:
    SUMMARY = f.read()


SYSTEM_PROMPT = f"You are acting as {NAME}. You are answering questions on {NAME}'s website, \
particularly questions related to {NAME}'s career, background, skills and experience. \
Your responsibility is to represent {NAME} for interactions on the website as faithfully as possible. \
You are given a summary of {NAME}'s background and LinkedIn profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer, say so."

SYSTEM_PROMPT += f"\n\n## Summary:\n{SUMMARY}\n\n## LinkedIn Profile:\n{RESUME}\n\n"
SYSTEM_PROMPT += f"With this context, please chat with the user, always staying in character as {NAME}."


EVAL_SYSTEM_PROMPT = f"""You are an evaluator that decides whether a response to a question is acceptable quality.

You are evaluating an Agent playing the role of {NAME} on their professional website.

EVALUATION CRITERIA:
1. **Accuracy**: Does the response accurately reflect {NAME}'s background and experience?
2. **Relevance**: Does the response directly address the user's question?
3. **Professionalism**: Is the tone appropriate for a potential client or employer?
4. **Completeness**: Does the response provide sufficient detail without being overly verbose?
5. **Authenticity**: Does it sound like {NAME} speaking about their own experience?

CONTEXT ABOUT {NAME}:

## Summary:
{SUMMARY}

## LinkedIn Profile:
{RESUME}

INSTRUCTIONS:
- Only mark as unacceptable if there are clear issues with accuracy, relevance, or professionalism
- Be generous with responses that demonstrate {NAME}'s qualifications appropriately
- Focus on whether the response helps a recruiter/client understand {NAME}'s value proposition
"""


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


def evaluator_user_prompt(message: str, reply: str, history: list) -> str:
    history_text = ""
    for msg in history:
        role = "User" if msg["role"] == "user" else "Agent"
        history_text += f"{role}: {msg['content']}"

    user_prompt = f"Here's the conversation between the User and the Agent:\n\n{history_text}\n\n"
    user_prompt += f"Here's the latest message from the User: \n\n{message}\n\n"
    user_prompt += f"Here's the latest response from the Agent: \n\n{reply}\n\n"
    user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
    return user_prompt


def evaluate(message: str, reply: str, history: list) -> Evaluation:
    history = [{"role": h["role"], "content": h["content"]} for h in history]
    messages: list = [{"role": "system", "content": EVAL_SYSTEM_PROMPT}] + [{"role": "user", "content": evaluator_user_prompt(message, reply, history)}]
    response = EVALUATOR.beta.chat.completions.parse(model=GEMINI_MODEL, messages=messages, response_format=Evaluation)
    return response.choices[0].message.parsed or Evaluation(is_acceptable=False, feedback="No evaluation provided")


def rerun(message: str, reply: str, history: list, feedback: str) -> str:
    updated_system_prompt = SYSTEM_PROMPT + f"\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
    updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
    updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"
    messages: list = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
    response = CHATBOT.responses.create(model=OPENAI_MODEL, input=messages)
    return response.output_text


def chat(message: str, history: list[dict[str, str]]) -> str:
    messages: list = [{"role": "system", "content": SYSTEM_PROMPT}] + history + [{"role": "user", "content": message}]
    response = CHATBOT.responses.create(model=OPENAI_MODEL, input=messages)
    reply = response.output_text

    evaluation = evaluate(message, reply, history)

    # If the response is not acceptable, rerun the chat and provide feedback
    if evaluation.is_acceptable:
        print("Passed evaluation - returning reply")
    else:
        print("Failed evaluation - retrying")
        print(evaluation.feedback)
        reply = rerun(message, reply, history, evaluation.feedback)
    return reply


def main():
    # load_dotenv(override=True)

    gr.ChatInterface(fn=chat, type="messages").launch()


if __name__ == "__main__":
    main()
