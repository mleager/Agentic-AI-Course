import os
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from agents import Agent, function_tool


@function_tool
def send_email(subject: str, html_body: str) -> dict[str, str]:
    """Send an email with the given subject and HTML body"""
    context = ssl.create_default_context()

    sender = os.getenv("GMAIL", "markleager92@gmail.com")
    appg = os.getenv("APPG", "")

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = sender

        msg.attach(MIMEText(html_body, "html"))
        msg.attach(MIMEText(html_body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender, appg)
            server.send_message(msg)
    except Exception as e:
        return {"status": "error", "error": str(e)}

    return {"status": "success"}


INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line."""


email_agent = Agent(
    name="Email agent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini",
)
