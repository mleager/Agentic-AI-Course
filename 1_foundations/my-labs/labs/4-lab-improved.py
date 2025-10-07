import os
import re
import json
import time
import bleach
import logging
import requests
from functools import lru_cache
from dotenv import load_dotenv
from openai import OpenAI
import gradio as gr

RESUME = os.getenv(key="RESUME", default="../../resume/resume.md")
SUMMARY = os.getenv(key="SUMMARY", default="../../summary/summary.txt")
LOG_FILE = "pushover.log"
MONITOR_LOG = "monitor.log"
MODEL = "gpt-4o-mini"


def monitor_response_time(start_time):
    current = time.time()
    response_time = current - start_time
    monitor.info(f"Response time for OpenAI Response: {response_time} seconds")


def setup_logging(logger_name: str, filename: str):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    if not logger.hasHandlers():
        handler = logging.FileHandler(filename=filename)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logging("chatbot", LOG_FILE)
monitor = setup_logging("monitor", MONITOR_LOG)


def resume_fallback() -> str:
    fallback = """
    DevOps Engineer with experience using common tools and technologies like Terraform, Kubernetes, and Docker.

    Have built custom workflows and developed applications using AI technologies and frameworks.

    Focus on automation and continuous improvement, leveraging AI technologies to drive efficiency and reliability.
    """
    return fallback


def summary_fallback() -> str:
    fallback = """
    Self-taught, disciplined, great communicator.

    I've worked on various projects, including infrastructure as code, DevOps, and AI-driven projects.

    My focus has always been on improving the efficiency and reliability of my teams and applications.
    """
    return fallback


# INFO: Continue to work on this
@lru_cache(maxsize=2)
def get_cached_content(content_type: str, file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()
            logger.info(f"Cached {content_type} content from: {file_path}")
            return content

    except Exception as e:
        logger.error(f"Error caching {content_type}: {e}")
        return ""


def get_reference_material(
    filetype: str, filepath: str, fallback: str, max_attempts=3
) -> str:
    if os.path.isfile(filepath):
        try:
            content = get_cached_content(filetype, filepath)
            if content:
                logger.info(f"Successfully loaded {filetype}: {filepath}")
                return content

        except Exception as e:
            logger.error(f"Error reading file: {e}")
    
    attempts = 0
    current = filepath

    while attempts < max_attempts:
        try:
            current = input(
                f"Enter {filetype} file location (attempt {attempts}/{max_attempts}): "
            )
            if not current:
                logger.info("User chose to use fallback resume data.")
                break

            if os.path.isfile(current):
                content = get_cached_content(filetype, current)
                if content:
                    logger.info(f"Successfully loaded {filetype}: {current}")
                    return content

            logger.warning(f"File not found: {current}. Retrying...")
            attempts += 1

        except Exception as e:
            logger.error(f"Error validating {filetype} file: {e}")

    logger.warning(
        f"Failed to find {filetype} file after {attempts} attempts. Using fallback data."
    )
    return fallback


# INFO: Santize input, validate email, set rate limit
class SecurityValidator:
    def __init__(self):
        self.max_message_length = 2000
        self.rate_limit_window = 60
        self.max_requests_per_window = 10
        self.user_requests: dict[str, list] = {}

    def sanitize_input(self, text) -> str:
        if not isinstance(text, str):
            try:
                text = str(text)
            except Exception as e:
                logger.error(f"Error sanitizing input: {e}")
                raise ValueError("Input must be a string")

        sanitized = bleach.clean(text=text, tags=[], attributes={}, strip=True)

        if len(sanitized) > self.max_message_length:
            sanitized = sanitized[: self.max_message_length]
            logger.warning(
                f"Message length exceeded maximum allowed length. Truncated to {self.max_message_length} characters."
            )

        return sanitized.strip()

    def validate_email(self, email: str) -> bool:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def check_rate_limit(self, user_id: str = "default") -> bool:
        """Returns False if rate limit met or exceeded, otherwise returns True."""
        current_time = time.time()

        if user_id not in self.user_requests:
            self.user_requests[user_id] = []

        self.user_requests[user_id] = [
            req_time
            for req_time in self.user_requests[user_id]
            if current_time - req_time < self.rate_limit_window
        ]

        request_count = len(self.user_requests[user_id])
        if request_count >= self.max_requests_per_window:
            logger.warning(f"Rate limit exceeded for user {user_id}.")
            return False

        self.user_requests[user_id].append(current_time)
        return True


# INFO: Validate environment variables
class ConfigValidator:
    @staticmethod
    def validate_environment():
        required_vars = ["PUSHOVER_TOKEN", "PUSHOVER_USER", "OPENAI_API_KEY"]
        missing_vars = []

        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")

        logger.info("Environment variables validated.")


# INFO: Added SecurityValidator to Validate Email
class Pushover:
    def __init__(self):
        self.secval = SecurityValidator()

    def push(self, text) -> bool:
        logger.info("Sending push notification...")
        try:
            response = requests.post(
                "https://api.pushover.net/1/messages.json",
                data={
                    "token": os.getenv("PUSHOVER_TOKEN"),
                    "user": os.getenv("PUSHOVER_USER"),
                    "message": text,
                },
                timeout=10,
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

    def record_user_details(
        self, email, name="Not provided", notes="Not provided"
    ) -> dict:
        logger.info("Calling 'record_user_details' tool...")
        try:
            # INFO: email validation
            if not self.secval.validate_email(email):
                logger.warning(f"Invalid email address: {email}")
                return {"recorded": "error"}

            success = self.push(
                f"Recording {name} with email {email} and notes {notes}"
            )
            logger.info(
                "Recorded user details."
                if success
                else "Failed to record user details."
            )
            return {"recorded": "ok" if success else "error"}

        except Exception as e:
            logger.error(f"Error recording user details: {e}")
            return {"recorded": "error"}

    def record_unknown_question(self, question) -> dict:
        logger.info("Calling 'record_unknown_question' tool...")
        try:
            success = self.push(
                f"Recording question with an unknown answer: {question}"
            )
            logger.info(
                "Recorded unknown question."
                if success
                else "Failed to record unknown question."
            )

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
                        "description": "The email address of this user",
                    },
                    "name": {
                        "type": "string",
                        "description": "The user's name, if they provided it",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Any additional information about the conversation that's worth recording to give context",
                    },
                },
                "required": ["email"],
                "additionalProperties": False,
            },
        }

        self.record_unknown_question_json = {
            "name": "record_unknown_question",
            "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question that couldn't be answered",
                    },
                },
                "required": ["question"],
                "additionalProperties": False,
            },
        }

        self.tools_list: list[dict[str, object]] = [
            {"type": "function", "function": self.record_user_details_json},
            {"type": "function", "function": self.record_unknown_question_json},
        ]


# INFO: Added SecurityValidator for Rate Limit & Sanitize Input
class Chatbot:
    def __init__(self):
        self.name = "Mark"
        self.openai = OpenAI()
        self.tools = Tools()
        self.pushover = Pushover()

        # INFO: Improvements
        self.secval = SecurityValidator()

        resume_fallback_str = resume_fallback()
        summary_fallback_str = summary_fallback()

        self.resume = get_reference_material("Resume", RESUME, resume_fallback_str)
        self.summary = get_reference_material("Summary", SUMMARY, summary_fallback_str)

        logger.info("Chatbot initialized successfully.")

    def handle_tool_call(self, tool_calls) -> list:
        logger.info(f"Handling {len(tool_calls)} tool calls...")
        results = []

        tool_methods = {
            "record_user_details": self.pushover.record_user_details, 
            "record_unknown_question": self.pushover.record_unknown_question
        }

        for tool_call in tool_calls:
            try:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                # INFO: Create a dict of tool_name and function and call the tool method
                tool_method = tool_methods.get(tool_name, None)
                if tool_method:
                    result = tool_method(**arguments)
                else:
                    result = {"error": f"Tool '{tool_name}' not found"}

                # INFO: Use hasattr() to check if tool method exists before calling
                # if hasattr(self.pushover, tool_name):
                #     tool_meth = getattr(self.pushover, tool_name)
                #     result = tool_meth(**arguments)
                # else:
                #     result = {"error": f"Tool '{tool_name}' not found"}

                results.append(
                    {
                        "role": "tool",
                        "content": json.dumps(result),
                        "tool_call_id": tool_call.id,
                    }
                )

            except json.JSONDecodeError as e:
                logger.error(f"Error parsing tool arguments: {e}")
                results.append(
                    {
                        "role": "tool",
                        "content": json.dumps({"error": "Invalid tool arguments"}),
                        "tool_call_id": tool_call.id,
                    }
                )

            except Exception as e:
                logger.error(f"Error handling tool call {tool_call.function.name}: {e}")
                results.append(
                    {
                        "role": "tool",
                        "content": json.dumps({"error": str(e)}),
                        "tool_call_id": tool_call.id,
                    }
                )

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

        # INFO: Sanitize Input
        sanitized_message = self.secval.sanitize_input(message)

        messages: list[dict[str, str]] = (
            [{"role": "system", "content": self.system_prompt()}]
            + history
            + [{"role": "user", "content": sanitized_message}]
        )

        # INFO: Check Rate Limit here
        if not self.secval.check_rate_limit():
            logger.warning("Rate limit exceeded. Skipping API call.")
            return "Rate limit exceeded. Please wait before trying again."

        try:
            done = False
            max_retries = 5
            retries = 0

            # TODO: Implement User ID system?

            while not done and retries < max_retries:
                retries += 1
                logger.info(f"OpenAI API call #{retries}")

                start = time.time()

                response = self.openai.chat.completions.create(
                    model=MODEL,
                    messages=messages,  # type: ignore
                    tools=self.tools.tools_list,  # type: ignore
                )

                finish_reason = response.choices[0].finish_reason
                if finish_reason == "tool_calls":
                    message_obj = response.choices[0].message
                    tool_calls = message_obj.tool_calls
                    results = self.handle_tool_call(tool_calls)
                    messages.append(message_obj)  # type: ignore
                    messages.extend(results)
                else:
                    done = True

                monitor_response_time(start)

            if retries >= max_retries:
                logger.warning(
                    "Failed to complete conversation after multiple retries."
                )
                return "Failed to complete conversation. Please try again."

            return (
                response.choices[0].message.content # type: ignore
                or "Response not found. Please try again."
            )

        except Exception as e:
            logger.error(f"Error in chat method: {e}")
            return "An error occurred. Please try again."


if __name__ == "__main__":
    load_dotenv(override=True)
    ConfigValidator().validate_environment()

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
