import os
import ssl
import smtplib
from email.mime.text import MIMEText
import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner, trace, function_tool


# 1. Sales Manager has access to 3 tools and a function (2 sales_agent tools & send_gmail function)
# 2. The Sales Manager calls all 3 agents to create emails, and picks the best one
# 3. After selecting the best agent, the Sales Manager calls the send_gmail function to send the email

# Agents: 1     (Sales Manager)
# Tools: 4      (sales_agent1, sales_agent2, sales_agent3 & send_gmail function tool)


load_dotenv(override=True)

GMAIL = os.getenv("GMAIL", "")
OPENAI_MODEL = "gpt-4o-mini"


@function_tool
def send_gmail(subject: str, body: str):
    """Send an email with a given subject and body."""
    context = ssl.create_default_context()

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = GMAIL
    msg["To"] = GMAIL

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(GMAIL, os.getenv("APPG", ""))
            server.send_message(msg)
    except Exception as e:
        print(f"Error sending email: {e}")


####  --------  Create Email Agents  --------  ####

instructions1 = """You are a sales agent working for ComplAI, a company that provides a SaaS tool 
for ensuring SOC2 compliance and preparing for audits, powered by AI.
You write professional, serious cold emails."""

instructions2 = """You are a humorous, engaging sales agent working for ComplAI, a company that provides
a SaaS tool for ensuring SOC2 compliance and preparing for audits, powered by AI.
You write witty, engaging cold emails that are likely to get a response."""

instructions3 = """You are a busy sales agent working for ComplAI, a company that provides a SaaS tool 
for ensuring SOC2 compliance and preparing for audits, powered by AI.
You write concise, to the point cold emails."""

sales_agent1 = Agent(
    name="Professional Sales Agent",
    instructions=instructions1,
    model="gpt-4o-mini",
)

sales_agent2 = Agent(
    name="Engaging Sales Agent",
    instructions=instructions2,
    model="gpt-4o-mini",
)

sales_agent3 = Agent(
    name="Busy Sales Agent",
    instructions=instructions3,
    model="gpt-4o-mini",
)


####  --------  Convert Email Agents to Tools  -------- ####

description = "Write a cold sales email"

tool1 = sales_agent1.as_tool("sales_agent1", description)
tool2 = sales_agent2.as_tool("sales_agent2", description)
tool3 = sales_agent3.as_tool("sales_agent3", description)

tools = [tool1, tool2, tool3, send_gmail]


####  --------  Create Sales Manager  --------  ####
# Use the Email Agent to generate drafts, and use the send_gmail tool to send the chosen email

manager_instructions = """
You are a Sales Manager at ComplAI. 
Your goal is to find the single best cold sales email using the sales_agent tools.
 
Follow these steps carefully:
1. Generate Drafts: Use all three sales_agent tools to generate three different email drafts. 
   Do not proceed until all three drafts are ready.
 
2. Evaluate and Select: Review the drafts and choose the single best email using your judgment of 
   which one is most effective.
 
3. Use the send_gmail tool to send the best email (and only the best email) to the user.
 
Crucial Rules:
- You must use the sales agent tools to generate the drafts — do not write them yourself.
- You must send ONE email using the send_gmail tool — never more than one.
"""


sales_manager = Agent(
    name="Sales Manager",
    instructions=manager_instructions,
    tools=tools,
    model=OPENAI_MODEL,
)

message = "Send a cold sales email addressed to 'Dear CEO'"


async def main():
    with trace("Sales manager"):
        result = await Runner.run(sales_manager, message)
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
