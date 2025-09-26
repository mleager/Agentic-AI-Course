import os
import logging
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
import gradio as gr

# Needs to be completely refactored...
# Additions to make to this file:
# 1. Reorganize Classes and methods
# 2. Implement more robust error handling
# 3. Add more features like file upload, resume suggestion, etc.
# 4. Incorporate data and config classes?

NAME = "Mark Leager"
OPENAI_MODEL = "gpt-4o-mini"
GEMINI_MODEL = "gemini-2.0-flash"

load_dotenv(override=True, dotenv_path="../../../.env")


# Create a logger
def setup_logging():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler('agent.log')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger

logger = setup_logging()


def get_resume_material(filename: str) -> str:
    path = f"../../resume/{filename}"
    if not os.path.isfile(path):
        logger.error(f"File not found: {path}")
        return "File not found"
    
    try:
        with open(path, "r") as f:
            material = f.read()

        logger.info(f"Successfully read file: {path}")
        return material
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return "Error reading file"

RESUME = get_resume_material("resume.md")
SUMMARY = get_resume_material("summary.txt")


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


class EvaluatorModel:
    def __init__(self):
        self.model = GEMINI_MODEL
        self.base_url = os.getenv("GEMINI_BASE_URL")
        self.client = OpenAI(api_key=os.getenv("GEMINI_API_KEY"), base_url=self.base_url)
        logger.info("EvaluatorModel initialized...")


    def evaluate(self, message: str, reply: str, history: list) -> Evaluation:
        logger.info("Evaluating Agent response...")
        try: 
            history = [{"role": h["role"], "content": h["content"]} for h in history]
            messages: list = [
                {"role": "system", "content": self.evaluator_system_prompt(NAME, RESUME, SUMMARY)}, 
                {"role": "user", "content": self.evaluator_user_prompt(message, reply, history)}
            ]
            response = self.client.beta.chat.completions.parse(
                model=self.model, 
                messages=messages, 
                response_format=Evaluation
            )
            evaluation = response.choices[0].message.parsed or Evaluation(is_acceptable=False, feedback="No evaluation provided")
            logger.info(f"Evaluation result: {evaluation.is_acceptable}")
            return evaluation
            # return response.choices[0].message.parsed or Evaluation(is_acceptable=False, feedback="No evaluation provided")
        except Exception as e:
            logger.error(f"Error evaluating Agent response: {e}")
            return Evaluation(is_acceptable=False, feedback=f"Error: {str(e)}")


    def evaluator_system_prompt(self, name, resume, summary: str) -> str:
        evaluator_system_prompt = f"""You are an evaluator that decides whether a response to a question is acceptable quality.

    You are evaluating an Agent playing the role of {name} on their professional website.

    EVALUATION CRITERIA:
    1. **Accuracy**: Does the response accurately reflect {name}'s background and experience?
    2. **Relevance**: Does the response directly address the user's question?
    3. **Professionalism**: Is the tone appropriate for a potential client or employer?
    4. **Completeness**: Does the response provide sufficient detail without being overly verbose?
    5. **Authenticity**: Does it sound like {name} speaking about their own experience?

    CONTEXT ABOUT {name}:

    ## Summary:
    {summary}

    ## LinkedIn Profile:
    {resume}

    INSTRUCTIONS:
    - Only mark as unacceptable if there are clear issues with accuracy, relevance, or professionalism
    - Be generous with responses that demonstrate {name}'s qualifications appropriately
    - Focus on whether the response helps a recruiter/client understand {name}'s value proposition
    """
        return evaluator_system_prompt


    def evaluator_user_prompt(self, message: str, reply: str, history: list) -> str:
        history_text = ""
        for msg in history:
            role = "User" if msg["role"] == "user" else "Agent"
            history_text += f"{role}: {msg['content']}"

        user_prompt = f"Here's the conversation between the User and the Agent:\n\n{history_text}\n\n"
        user_prompt += f"Here's the latest message from the User: \n\n{message}\n\n"
        user_prompt += f"Here's the latest response from the Agent: \n\n{reply}\n\n"
        user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
        return user_prompt


class Chatbot:
    def __init__(self, resume=RESUME, summary=SUMMARY):
        self.resume = resume
        self.summary = summary
        self.model = OPENAI_MODEL
        self.client = OpenAI()
        self.evaluator = EvaluatorModel()
        logger.info(f"Chatbot initialized...")


    # def prompt_for_resume_input(self):
    #     message = input("Resume not found. Please enter or paste your resume text here:\n")
    #     if len(message.strip()) > 1:
    #         self.resume = message


    def chatbot_system_prompt(self, name, resume, summary: str) -> str:
        system_prompt = f"You are acting as {name}. You are answering questions on {name}'s website, \
    particularly questions related to {name}'s career, background, skills and experience. \
    Your responsibility is to represent {name} for interactions on the website as faithfully as possible. \
    You are given a summary of {name}'s background and LinkedIn profile which you can use to answer questions. \
    Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
    If you don't know the answer, say so."

        system_prompt += f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{resume}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {name}."
        return system_prompt


    def rerun(self, message: str, reply: str, history: list, feedback: str) -> str:
        logger.info("Rerunning chat...")
        system_prompt = self.chatbot_system_prompt(NAME, self.resume, self.summary)

        updated_system_prompt = system_prompt + f"\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
        updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
        updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"

        try:
            messages: list = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
            response = self.client.responses.create(model=self.model, input=messages)
            return response.output_text
        except Exception as e:
            logger.error(f"Error rerunning chat: {e}")
            return "Error: Unable to rerun chat"


    def chat(self, message: str, history: list[dict[str, str]]) -> str:
        history = [{"role": h["role"], "content": h["content"]} for h in history]
        messages: list = [{"role": "system", "content": self.chatbot_system_prompt(NAME, self.resume, self.summary)}] + history + [{"role": "user", "content": message}]
        response = self.client.responses.create(model=self.model, input=messages)
        reply = response.output_text

        evaluation = self.evaluator.evaluate(message, reply, history)

        # If the response is not acceptable, rerun the chat and provide feedback
        if evaluation.is_acceptable:
            logger.info("Passed evaluation - returning reply")
        else:
            logger.info("Failed evaluation - retrying")
            logger.info(evaluation.feedback)
            reply = self.rerun(message, reply, history, evaluation.feedback)
        return reply
    

def main():
    logger.info("Initializing Application Startup...")
    try:
        chatbot = Chatbot()

        # if RESUME == "Error reading file":
        #     logger.error("Error reading resume file")
        #     chatbot.prompt_for_resume_input()

        logger.info("Launching Gradio Chat Interface...")
        gr.ChatInterface(fn=chatbot.chat, type="messages").launch()

    except KeyboardInterrupt:
        logger.info("Chatbot shutdown")
        exit(0)

    except Exception as e:
        logger.error(f"Error starting application: {e}")


if __name__ == "__main__":
    main()
