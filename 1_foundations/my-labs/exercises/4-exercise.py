import logging
import os
from openai import OpenAI
from openai.types.responses import ResponseInputParam
from pydantic import BaseModel
import gradio as gr

#### WARN: Come Back to This Later ####
## Additions:
### Evaluator to check Model Responses
# --> Return more in-depth repsonse objects for better analysis
# --> Save response statistics (rerun count, avg grade, etc.)
### Model to check or rephase user's questions/input
# --> check user intent?
# --> try most elegant response based on context and previous responses
### Use RAG to provide larger reference/revelent data
# --> load documents, embedding, searching, caching
### Add Metrics tracking

CHAT_MODEL = "gpt-4o-mini"
EVAL_MODEL = "gpt-5-nano"
SYSTEM = "system"
USER = "user"
NAME = "Mark"
RESUME = "resume.md"
SUMMARY = "summary.md"


def setup_logger(logger_name: str, filename: str) -> logging.Logger:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    if not logger.hasHandlers():
        handler = logging.FileHandler(filename)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logger("chatbot", "chatbot.log")
monitor = setup_logger("monitor", "monitor.log")
grading = setup_logger("grading", "grading.log")


class Config:
    def open_file(self, filename: str) -> str:
        try:
            with open(filename, "r") as file:
                data = file.read()
            return data
        except FileNotFoundError:
            logger.error(f"File '{filename}' not found.")
            return ""

    def get_reference_data(self, filename: str, fallback: str) -> str:
        attempts = 0
        max_attempts = 3

        file = self.open_file(filename)
        if file:
            return file

        while attempts < max_attempts:
            current = input("Please enter the filename for reference data: ")
            if not current:
                break
            if os.path.isfile(current):
                file = self.open_file(current)
                return file

            attempts += 1

        logger.error(f"Unable to find reference data after {max_attempts} attempts.")
        return fallback

    def resume_fallback(self) -> str:
        fallback = """
        I am a DevOps engineer with experience in managing and maintaining infrastructure.
        I have experience with setting up, managing, and optimizing cloud infrastructure, as well as automating tasks using tools like Terraform and Ansible.
        I am also proficient in using tools like Docker, Kubernetes, and Helm for managing and deploying applications.
        I am also familiar with using CI/CD pipelines, monitoring, and logging tools like Prometheus, Grafana, and ELK stack.
        I am also familiar with using tools like AWS, Azure, and GCP for managing cloud resources and services.
        I have built AI services, tools, and workflows to improve lead generation, customer management, inventory management, sales tracking, 
        and created an internal Chatbot with a RAG database containing the employee handbook and other business operations that employees can reference.
        """
        return fallback

    def summary_fallback(self) -> str:
        fallback = """
        I enjoy music, cooking, video games, art, and travel. I have a strong work ethic and a passion for teamwork.
        I have a strong communication and organizational skills, as well as a strong analytical and problem-solving abilities.
        I have a strong sense of humor and enjoy engaging in debates and discussions.
        I have a strong sense of empathy and can help others navigate their feelings and experiences.
        I have a strong sense of responsibility and can help others make decisions and make informed decisions.
        I have a strong sense of time management and can help others stay focused and organized.
        I have a strong sense of creativity and enjoy experimenting with new ideas and technologies.
        I have a strong sense of self-care and enjoy taking care of my physical and mental health.
        I have a strong sense of social skills and enjoy engaging in meaningful conversations and interactions with others.
        I have a strong sense of motivation and enjoy working hard to achieve my goals.
        I have a strong sense of values and enjoy following the company's mission and vision.
        I have a strong sense of empathy and can help others navigate their feelings and experiences.
        I have a strong sense of responsibility and can help others make decisions and make informed decisions.
        I have a strong sense of time management and can help others stay focused and organized.
        """
        return fallback


class ResponseGrade(BaseModel):
    grade: int


class Evaluator:
    def __init__(self):
        self.model = EVAL_MODEL
        self.client = OpenAI(timeout=10)

    def eval_system_prompt(self) -> str:
        system_prompt = f"""
        You are a helpful assistant that will be given a question and a response.
        You are evaluating the given response to evaluate the quality of the assistant's response.
        Check for the following:
        - Does the response address the user's question/input?
        - Does the response provide relevant and informative information?
        - Does the response contain any errors or misunderstandings?

        Please grade the quality of the response using the following 1-5 scale:
        5: Great response
        4: Satisfactory response
        3: Needs improvement
        2: Poor response
        1: Very poor response

        Please return the grade using the following JSON format:
        {"grade": <grade>}
        """
        return system_prompt

    def eval_user_message(self, message: str, reply: str) -> str:
        user_prompt = f"Here is the user's message: {message}\n\n"
        user_prompt += f"Here is the assistant's response: {reply}\n\n"
        user_prompt += "Please grade the quality of the response with 1-5, replying with JSON {'grade': <grade>}"
        return user_prompt

    def evaluate(self, message, reply) -> ResponseGrade:
        system_prompt = self.eval_system_prompt()
        user_prompt = self.eval_user_message(message, reply)
        messages: ResponseInputParam = [
            {"role": SYSTEM, "content": system_prompt},
            {"role": USER, "content": user_prompt},
        ]
        try:
            logger.info("Sending evaluation request...")
            response = self.client.responses.parse(
                model=EVAL_MODEL, input=messages, text_format=ResponseGrade
            )
            result = response.output_parsed
            if result:
                grading.info(f"Received evaluation: {result}")
                return result
            else:
                grading.info("No evaluation received...")
                logger.info("Failed to evaluate response... Returning default grade: 0")
                return ResponseGrade(grade=0)
        except Exception as e:
            logger.error(f"Error evaluating response: {e}")
            return ResponseGrade(grade=0)


class Chatbot:
    def __init__(self):
        self.model = CHAT_MODEL
        self.client = OpenAI(timeout=10)
        self.evaluator = Evaluator()
        self.config = Config()
        self.resume_fallback = Config().resume_fallback()
        self.summary_fallback = Config().summary_fallback()

        self.name = NAME
        self.resume = self.config.get_reference_data(RESUME, self.resume_fallback)
        self.summary = self.config.get_reference_data(SUMMARY, self.summary_fallback)

    def system_prompt(self) -> str:
        system_prompt = f"""
        You are assuming the role of {self.name}. You have access to their resume and other relevant information.
        You'll be answering questions about their background, experiences, and skills.
        The user asking the questions will be recruiters and hiring managers.
        Please embellish the responses to be as informative and detailed as possible, while also being concise.

        ## Resume
        {self.resume}

        ## Other relevant information
        {self.summary}
        """
        return system_prompt
    
    def rerun(self, message: str, reply: str, grade: int) -> str:
        logger.info("Rerunning the chat...")
        system_prompt = self.system_prompt()
        updated_system_prompt = system_prompt + f"\n\n## Previous answer rejected"
        updated_system_prompt += f"\nYou tried to reply, but the response quality was not satisfactory."
        updated_system_prompt += f"\n\nYour attempted response: {reply}"
        updated_system_prompt += f"\nYour response was grade as a {grade} out of 5"
        updated_system_prompt += "\nPlease provide a new response that addresses the user's question/input below."
        updated_system_prompt += f"\nUser's question was:\n{message}"

        try:
            messages: ResponseInputParam = [
                {"role": SYSTEM, "content": updated_system_prompt},
                {"role": USER, "content": message},            
            ]
            response = self.client.responses.create(model=CHAT_MODEL, input=messages)
            return response.output_text
        except Exception as e:
            logger.error(f"Error rerunning the chat: {e}")
            return "I'm sorry, I encountered an error while rerunning the chat. Please try again later."

    def chat(self, message: str, history) -> str:
        if history:
            history = [{"role": h['role'], "content": h['content'] } for h in history]

        system_prompt = self.system_prompt()
        messages: list = [{"role": SYSTEM, "content": system_prompt}] + history + [{"role": USER, "content": message}]

        try:
            logger.info("Sending chat request...")
            response = self.client.responses.create(model=CHAT_MODEL, input=messages)
            reply = response.output_text
            logger.info(f"Received response: {reply}")

            eval = self.evaluator.evaluate(message, reply)
            grade = eval.grade
            if grade >= 3:
                grading.info(f"Received evaluation grade: {eval.grade}")
                return reply
            else:
                grading.info(f"Received a poor evaluation grade: {eval.grade}")
                improved_reply = self.rerun(message, reply, grade)

                re_eval = self.evaluator.evaluate(message, improved_reply)
                grading.info(f"Received a re-evaluation grade: {re_eval.grade}")
                return improved_reply

        except Exception as e:
            logger.error(f"Error chatting with OpenAI: {e}")
            return "I'm sorry, I encountered an error while chatting with the AI model. Please try again later."


if __name__ == "__main__":
    try:
        chatbot = Chatbot()
        gr.ChatInterface(fn=chatbot.chat, type='messages').launch()
    except Exception as e:
        logger.error(f"Error launching Gradio chat interface: {e}")
        exit(1)
