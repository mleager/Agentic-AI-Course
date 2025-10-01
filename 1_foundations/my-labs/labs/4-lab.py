import os
import json
import time
import requests
import logging
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

RESUME = "../../resume/resume.md"
SUMMARY = "../../summary/summary.txt"
LOG_FILE = "pushover.log"
MONITOR_LOG = "monitor.log"
MODEL = "gpt-4o-mini"

# load_dotenv(override=True)

def setup_logging(logger_name: str, filename: str):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.FileHandler(filename=filename)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

logger = setup_logging("chatbot", LOG_FILE)
monitor = setup_logging("monitor", MONITOR_LOG)

def monitor_response_time(start_time: float):
    current = time.time()
    response_time = current - start_time
    if response_time > 5:
        logger.warning(f"Long response time: {response_time} seconds")
    else:
        monitor.info(f"Response time for OpenAI Response: {response_time} seconds")

def get_resume_material(filename=RESUME, max_attempts=3) -> str:
    attempts = 0
    current = filename

    while attempts < max_attempts:
        if os.path.isfile(current):
            try:
                with open(current, 'r') as file:
                    content = file.read()
                    if content:
                        logger.info(f"Successfully loaded resume: {current}")
                        return content
            except Exception as e:
                logger.error(f"Error reading file: {e}")

        logger.warning(f"File not found: {current}. Retrying...")
        attempts += 1

        if attempts < max_attempts:
            current = input(f"Enter resume file location (attempt {attempts}/{max_attempts}): ")
            if not current:
                logger.info("User chose to use fallback resume data.")
                break

    logger.warning(f"Failed to find resume file after {attempts} attempts. Using default resume.")
    return "DevOps Engineer with experience using common tools and technologies like Terraform, Kubernetes, and Docker."

def get_summary_material(filename=SUMMARY, max_attempts=3) -> str:
    attempts = 0
    current = filename

    while attempts < max_attempts:
        if os.path.isfile(current):
            try:
                with open(current, 'r') as file:
                    content = file.read()
                    if content:
                        logger.info(f"Successfully loaded summary: {current}")
                        return content
            except Exception as e:
                logger.error(f"Error reading file: {e}")

        logger.warning(f"File not found: {current}. Retrying...")
        attempts += 1

        if attempts < max_attempts:
            current = input(f"Enter summary file location (attempt {attempts}/{max_attempts}): ")
            if not current:
                logger.info("User chose to use fallback summary data.")
                break

    logger.warning(f"Failed to find summary file after {attempts} attempts. Using default summary.")
    return "Self taught, disciplined, great communicator with strong DevOps background."


class Pushover:
    def push(self, text) -> bool:
        logger.info(f"Sending push notification...")
        try:
            response = requests.post("https://api.pushover.net/1/messages.json",
                data={
                    "token": os.getenv("PUSHOVER_TOKEN"),
                    "user": os.getenv("PUSHOVER_USER"),
                    "message": text,
                },
                timeout=10
            )
            response.raise_for_status()
            logger.info("Push notification sent successfully.")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending push notification: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False

    def record_user_details(self, email, name="Not provided", notes="Not provided") -> dict:
        logger.info("Calling record_user_details tool...")
        try:
            success = self.push(f"Recording {name} with email {email} and notes {notes}")
            logger.info("Recorded user details." if success else "Failed to record user details.")
            return {"recorded": "ok" if success else "error"}
        except Exception as e:
            logger.error(f"Error recording user details: {e}")
            return {"recorded": "error"}

    def record_unknown_question(self, question) -> dict:
        logger.info("Calling record_unknown_question tool...")
        try:
            success = self.push(f"Recording question with an unknown answer: {question}")
            logger.info("Recorded unknown question." if success else "Failed to record unknown question.")
            return {"recorded": "ok" if success else "error"}
        except Exception as e:
            logger.error(f"Error recording unknown question: {e}")
            return {"recorded": "error"}


class Tools:
    def __init__(self):
        self.record_user_details_json = {
            "name": "record_user_details",
            "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "The email address of this user"
                    },
                    "name": {
                        "type": "string",
                        "description": "The user's name, if they provided it"
                    }
                    ,
                    "notes": {
                        "type": "string",
                        "description": "Any additional information about the conversation that's worth recording to give context"
                    }
                },
                "required": ["email"],
                "additionalProperties": False
            }
        }

        self.record_unknown_question_json = {
        "name": "record_unknown_question",
        "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question that couldn't be answered"
                },
            },
            "required": ["question"],
            "additionalProperties": False
            }
        }

        self.tools_list: list[dict[str, object]] = [
            {"type": "function", "function": self.record_user_details_json},
            {"type": "function", "function": self.record_unknown_question_json},
        ]


class Chatbot:
    def __init__(self):
        self.name = "Mark"
        self.openai = OpenAI()
        self.tools = Tools()
        self.pushover = Pushover()

        self.resume = get_resume_material()
        self.summary = get_summary_material()

        # try:
        #     with open(RESUME, "r") as r:
        #         self.resume = r.read()
        #     with open(SUMMARY, "r") as s:
        #         self.summary = s.read()
        #     logger.info("Resume and summary loaded successfully.")
        # except FileNotFoundError as e:
        #     logger.warning(f"Error reading resume and summary: {e}")
        #     self.resume = "DevOps Engineer with experience using common tools and technologies like Terraform, Kubernetes, and Docker."
        #     self.summary = "Self taught, disciplined, great communicator."

        logger.info("Chatbot initialized successfully.")

    def handle_tool_call(self, tool_calls) -> list:
        logger.info(f"Handling {len(tool_calls)} tool calls...")
        results = []

        for tool_call in tool_calls:
            try:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                if tool_name == "record_user_details":
                    result = self.pushover.record_user_details(**arguments)
                elif tool_name == "record_unknown_question":
                    result = self.pushover.record_unknown_question(**arguments)
                else:
                    result = {"error": f"Tool '{tool_name}' not found"}

                results.append({
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_call_id": tool_call.id
                })

            except json.JSONDecodeError as e:
                logger.error(f"Error parsing tool arguments: {e}")
                results.append({
                    "role": "tool",
                    "content": json.dumps({"error": "Invalid tool arguments"}),
                    "tool_call_id": tool_call.id
                })
            except Exception as e:
                logger.error(f"Error handling tool call {tool_call.function.name}: {e}")
                results.append({
                    "role": "tool",
                    "content": json.dumps({"error": str(e)}),
                    "tool_call_id": tool_call.id
                })

        return results

    def system_prompt(self):
        system_prompt = f"""
        You are an AI assistant that is assuming the identity of Mark. Users will ask you questions about Mark's resume and work experience.
        You will be given his resume, a summary about him, and you are to answer as Mark.

        Here are some guidelines to follow:
        1. Answer in the most concise yet articulate way you can.
        2. Draw from the resume and summary to give accurate information, otherwise respond with something vague that ties into the resume content.
        3. If asked how you would solve a question or problem, provide a step-by-step solution.
        4. Make sure to include any relevant information from the context provided.
        5. Be as detailed as possible in your response.

        Tools available:
        - {self.tools.record_user_details_json["name"]}: {self.tools.record_user_details_json["description"]}
        - {self.tools.record_unknown_question_json["name"]}: {self.tools.record_unknown_question_json["description"]}

        Context:
        {self.resume}

        Summary:
        {self.summary}
        """
        return system_prompt

    def chat(self, message, history=None) -> str:
        if history is None:
            history = []
        messages: list[dict[str, str]] = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]

        try:
            done = False
            max_retries = 5
            retries = 0

            while not done and retries < max_retries:
                retries += 1
                logger.info(f"OpenAI API call #{retries}")

                start = time.time()

                response = self.openai.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=self.tools.tools_list
                )

                finish_reason = response.choices[0].finish_reason
                if finish_reason == "tool_calls":
                    message_obj = response.choices[0].message
                    tool_calls = message_obj.tool_calls
                    results = self.handle_tool_call(tool_calls)
                    messages.append(message_obj)
                    messages.extend(results)
                else:
                    done = True

                monitor_response_time(start)

            if retries >= max_retries:
                logger.warning("Failed to complete conversation after multiple retries.")
                return "Failed to complete conversation. Please try again."

            return response.choices[0].message.content or "Response not found. Please try again."

        except Exception as e:
            logger.error(f"Error in chat method: {e}")
            return "An error occurred. Please try again."


if __name__ == "__main__":
    load_dotenv(override=True)

    logger.info("Starting application...")

    try:
        me = Chatbot()
        logger.info("Launching Gradio interface...")
        gr.ChatInterface(me.chat, type="messages").launch()

    except KeyboardInterrupt:
        logger.info("Application shutdown.")
        exit(0)

    except Exception as e:
        logger.error(f"Unexpected error in chat: {e}")
        exit(1)

