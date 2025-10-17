# Agents, Handoffs, Agents as Tools, and Function Tools

# 1. Agents: Emailer and Teacher
# Teacher creates a small lesson plan for the day
# Emailer sends the lesson plan every day

import re
import os
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from dotenv import load_dotenv
from agents import Agent, Runner, function_tool
import asyncio

load_dotenv(override=True)

OPENAI_MODEL = "gpt-4o-mini"
GMAIL = os.getenv("GMAIL", "markleager92@gmail.com")
APPG = os.getenv("APPG", "")
LESSON_PROMPT = "Please create a lesson plan for DevOps."


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler = logging.FileHandler(f"{name}.log")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


@function_tool
def send_email(subject: str, body: str) -> dict[str, str]:
    """Send an HTML email, but provide plaintext fallback.
    If content_type is 'html', send HTML email.
    Else send plaintext email."""

    context = ssl.create_default_context()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL
    msg["To"] = GMAIL

    is_html = re.search(r"<[a-z][\s\S]*>", body)

    if is_html:
        msg.attach(MIMEText(body, "plain"))
        msg.attach(MIMEText(body, "html"))
    else:
        msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(GMAIL, APPG)
            server.send_message(msg)
            return {"success": "true"}
    except Exception as e:
        print(f"Failed to send email: {e}")
        return {"success": "false"}


class TeacherAgent(Agent):
    def __init__(self, name: str, emailer_agent: Agent):
        self.set_instructions()

        super().__init__(
            name=name,
            instructions=self.lesson_plan,
            handoffs=[emailer_agent],
            model=OPENAI_MODEL,
        )

        self.logger = setup_logger("teacher")
        self.logger.info(f"Initializing Teacher Agent: {self.name}...")

    def set_instructions(self):
        self.lesson_plan = """Create a lesson plan for DevOps (software engineering).
        You can include topics like: Terraform, AWS, Azure, Kubernetes, CI/CD, and more.
        The lesson plans can include homework or challenge questions at the end.
        The lesson plan should be a few paragraphs long, and be easy to follow.
        Then handoff the lesson plan to the Emailer Agent."""


class EmailerAgent(Agent):
    def __init__(self, name: str):
        self.set_instructions()

        super().__init__(
            name=name,
            instructions=self.lesson_plan,
            tools=[send_email],
            model=OPENAI_MODEL,
        )

    def set_instructions(self):
        self.lesson_plan = """You'll be receiving a lesson plan for DevOps.
        Please convert the lesson plan from text or markdown into HTML. The HTML should be visually appealing, 
        easy to follow, and include a table or chart to help visualize the topics.
        Then please use the 'send_email' function tool to send this as an email with the subject 
        'Daily Devops Lesson Plan'."""


async def main():
    emailer = EmailerAgent("Emailer Agent")
    teacher = TeacherAgent(name="DevOps Teacher", emailer_agent=emailer)
    lesson_plan = await Runner.run(teacher, LESSON_PROMPT)

    print(f"Lesson plan: {lesson_plan}")


if __name__ == "__main__":
    asyncio.run(main())
