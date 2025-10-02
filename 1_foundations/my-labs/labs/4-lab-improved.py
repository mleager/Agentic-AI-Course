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

# load_dotenv(override=True)


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
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logging("chatbot", LOG_FILE)
monitor = setup_logging("monitor", MONITOR_LOG)


def resume_fallback() -> str:
    fallback = f"""
    DevOps Engineer with experience using common tools and technologies like Terraform, Kubernetes, and Docker.

    Have built custom workflows and developed applications using AI technologies and frameworks.

    Focus on automation and continuous improvement, leveraging AI technologies to drive efficiency and reliability.
    """
    return fallback


def summary_fallback() -> str:
    fallback = f"""
    Self-taught, disciplined, great communicator.

    I've worked on various projects, including infrastructure as code, DevOps, and AI-driven projects.

    My focus has always been on improving the efficiency and reliability of my teams and applications.
    """
    return fallback


@lru_cache(maxsize=1)
def get_cached_content(self, content_type: str, file_path: str) -> str:
    try:
        with open(file_path, 'r') as file:
            content = file.read().strip()
            logger.info(f"Cached {content_type} content from: {file_path}")
            return content
    except Exception as e:
        logger.error(f"Error caching {content_type}: {e}")
        return ""


def get_reference_material(filetype: str, filepath: str, fallback: str, max_attempts=3) -> str:
    # perf = PerformanceOptimizer()
    attempts = 0
    current = filepath

    while attempts < max_attempts:
        if os.path.isfile(current):
            try:
                content = get_cached_content(filepath)
                if content != "":
                    logger.info(f"Successfully loaded {filetype}: {current}")
                    return content
                # with open(current, 'r') as file:
                #     content = file.read()
                #     if content:
                #         logger.info(f"Successfully loaded {filetype}: {current}")
                #         return content
            except Exception as e:
                logger.error(f"Error reading file: {e}")

        logger.warning(f"File not found: {current}. Retrying...")
        attempts += 1

        if attempts < max_attempts:
            current = input(f"Enter {filetype} file location (attempt {attempts}/{max_attempts}): ")
            if not current:
                logger.info("User chose to use fallback resume data.")
                break

    logger.warning(f"Failed to find {filetype} file after {attempts} attempts. Using fallback data.")
    return fallback


# INFO: First Improvement: Santize input and set rate limit
class SecurityValidator:
    def __init__(self):
        self.max_message_length = 2000
        self.rate_limit_window = 60
        self.max_requests_per_window = 10
        self.user_requests: dict[str, list] = {}

    def sanitize_input(self, text) -> str:
        if not isinstance(text, str):
            # raise ValueError("Input must be a string")
            text = str(text)

        sanitized = bleach.clean(text=text, tags=[], attributes={}, strip=True)

        if len(sanitized) > self.max_message_length:
            sanitized = sanitized[:self.max_message_length]
            logger.warning(f"Message length exceeded maximum allowed length. Truncated to {self.max_message_length} characters.")

        return sanitized.strip()

    def validate_email(self, email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def check_rate_limit(self, user_id: str = "default") -> bool:
        """Returns False if rate limit met or exceeded, otherwise returns True."""
        current_time = time.time()

        if user_id not in self.user_requests:
            self.user_requests[user_id] = []

        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if current_time - req_time < self.rate_limit_window
        ]

        request_count = len(self.user_requests[user_id])
        if request_count >= self.max_requests_per_window:
            logger.warning(f"Rate limit exceeded for user {user_id}.")
            return False

        self.user_requests[user_id].append(current_time)
        return True


# INFO: Second Improvement: Validate environment variables
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

        logger.info(f"Environment variables validated.")


# INFO: Third Improvement: Use caching?
# class PerformanceOptimizer:
#     def __init__(self):
#         self.session = None
#
#     async def get_session(self) -> aiohttp.ClientSession:
#         if self.session is None:
#             connector = aiohttp.TCPConnector(
#                 limit=100,
#                 limit_per_host=10,
#                 ttl_dns_cache=300,
#                 use_dns_cache=True,
#             )
#             timout = aiohttp.ClientTimeout(total=10)
#             self.session = aiohttp.ClientSession(connector=connector, timeout=timout)
#
#         return self.session
#
#     async def async_push_notification(self, text: str) -> bool:
#         session = await self.get_session()
#         try:
#             async with session.post(
#                 "https://api.pushover.net/1/messages.json", 
#                 data={
#                     "token": os.getenv("PUSHOVER_TOKEN"),
#                     "user": os.getenv("PUSHOVER_USER"),
#                     "message": text,
#                 }
#             ) as response:
#                 response.raise_for_status()
#                 logger.info("Push notification sent asynchronously.")
#                 return True
#
#         except Exception as e:
#             logger.error(f"Error sending push notification: {e}")
#             return False
#
#     # INFO: Is this needed?
#     @lru_cache(maxsize=1)
#     def get_cached_content(self, content_type: str, file_path: str) -> str:
#         try:
#             with open(file_path, 'r') as file:
#                 content = file.read().strip()
#                 logger.info(f"Cached {content_type} content from: {file_path}")
#                 return content
#         except Exception as e:
#             logger.error(f"Error caching {content_type}: {e}")
#             return ""


# INFO: Added:
# --> PerformanceOptimizer for Async Push
# --> SecurityValidator for Rate Limit and Email
class Pushover:
    def __init__(self):
        # self.perf = PerformanceOptimizer()
        self.secval = SecurityValidator()

    # INFO: Apply async push method

    # def push(self, text) -> bool:
    #     logger.info(f"Sending push notification...")
    #     try:
    #         response = self.perf.async_push_notification(text)
    #         if response:
    #             logger.info("Push notification sent successfully.")
    #             return True
    #         # elif not response:
    #         #     self.seq_push(text)
    #         #     return True
    #         else:
    #             logger.warning("Failed to send push notification.")
    #             return False
    #     except Exception as e:
    #         logger.error(f"Error sending push notification: {e}")
    #         return False

    # INFO: Original Push method (sequential)
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
            # INFO: Implement email validation from SecurityValidator
            email = self.secval.validate_email(email)
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


# INFO: Added:
# --> SecurityValidator for Rate Limit & Sanitize Input
class Chatbot:
    def __init__(self):
        self.name = "Mark"
        self.openai = OpenAI()
        self.tools = Tools()
        self.pushover = Pushover()

        # INFO: Improvements
        self.secval = SecurityValidator()

        self.resume = get_reference_material("Resume", RESUME, resume_fallback())
        self.summary = get_reference_material("Summary", SUMMARY, summary_fallback())

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

        # INFO: Implement Sanitize Input
        sanitized_message = self.secval.sanitize_input(message)

        messages: list[dict[str, str]] = [
            {"role": "system", "content": self.system_prompt()}
        ] + history + [
            {"role": "user", "content": sanitized_message}
        ]

        # INFO: Check Rate Limit here
        if not self.secval.check_rate_limit():
            logger.warning("Rate limit exceeded. Skipping API call.")
            return "Rate limit exceeded. Please wait before trying again."

        try:
            done = False
            max_retries = 5
            retries = 0

            # TODO: Implement User ID system?

            # TODO: Ensure this works as expected
            # INFO: Check if Rate Limit is exceeded (removed)
            # check_rate_limit = self.secval.check_rate_limit()

            # INFO: Add rate limit check to condition (removed)
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
    # INFO: Call validate_environemt()
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

