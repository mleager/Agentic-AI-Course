import os
import ssl
import smtplib
from email.mime.text import MIMEText
import asyncio
from dotenv import load_dotenv
from agents import Agent, Runner, trace, function_tool


# 1. There are 2 Agents: Sales Manager & Email Agent
# 2. The Sales Manager has access to the 3 sales_agent tools and 1 Handoff to the Email Agent
# 3. The Sales Manager selects the best sales_agent tool and passes the output to the Email Agent
# 4. The Email Agent uses the subject_writer and html_converter tools to generate the email subject and body
# 5. Then the Email Agent sends the HTML Email using the send_html_email function

# Agents: 2             (Sales Manager & Email Agent)
# Sales tools: 3        (sales_agent1, sales_agent2, sales_agent3)
# Sales handoffs: 1     (Email Agent)
# Email tools: 3        (subject_writer, html_converter & send_html_email function tool)


load_dotenv(override=True)

GMAIL = os.getenv('GMAIL', '')
OPENAI_MODEL = 'gpt-4o-mini'


@function_tool
def send_html_email(subject: str, html_body: str) -> dict[str, str]:
    context = ssl.create_default_context()

    msg = MIMEText(html_body, 'html')
    msg['Subject'] = subject
    msg['From'] = GMAIL
    msg['To'] = GMAIL

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
            server.login(GMAIL, os.getenv('APPG', ''))
            err = server.send_message(msg)
            if err:
                return {"status": "error"}
            return {"status": "success"}
    except Exception as e:
        print(f"Error sending email: {e}")
        return {"status": "error"}
    

####  --------  Create Subject Writer and HTML Converter Agents/Tools  --------- ####

subject_instructions = """You can write a subject for a cold sales email.
You are given a message and you need to write a subject for an email that is likely to get a response."""

html_instructions = """You can convert a text email body to an HTML email body.
You are given a text email body which might have some markdown and you need to convert it to an 
HTML email body with simple, clear, compelling layout and design."""


subject_writer = Agent("Subject Writer", subject_instructions, model=OPENAI_MODEL)
subject_tool = subject_writer.as_tool("subject_writer", "Write a subject for an email")


html_converter = Agent("HTML Converter", html_instructions, model=OPENAI_MODEL)
html_tool = html_converter.as_tool("html_converter", "Convert a text email body to HTML")


html_tools = [subject_tool, html_tool, send_html_email]


####  --------  Create Emailer Agent  --------- ####
# Will have access to the subject_tool, html_tool, and send_html_email function

instructions ="""You are an email formatter and sender. You receive the body of an email to be sent.
You first use the subject_writer tool to write a subject for the email, then use the html_converter tool 
to convert the body to HTML.
Make sure to use the ouput from subject_writer and html_converter tools without modifying their outputs.
Finally, you use the send_html_email tool to send the email with the subject and HTML body."""


emailer_agent = Agent(
    name="Email Manager",
    instructions=instructions,
    tools=html_tools,
    model=OPENAI_MODEL,
    handoff_description="Convert an email to HTML and send it")


#### --------  Create Sales Agent  --------- ####

sales_agent_instructions = """You are a sales agent, responsible for writing cold sales emails.
You receive a customer's message, and you need to write a cold sales email that is likely to get a response.
Make sure to use the ouput from the subject_writer and html_converter tools without modifying their outputs. """

direct = sales_agent_instructions + "Be direct and concise"
charismatic = sales_agent_instructions + "Be charismatic and engaging"
busy = sales_agent_instructions + "Be busy and avoid interrupting"


sales_agent1 = Agent(name="Sales Agent",instructions=direct,model=OPENAI_MODEL)
tool1 = sales_agent1.as_tool("sales_agent1", "Write a cold sales email")


sales_agent2 = Agent(name="Sales Agent 2", instructions=charismatic, model=OPENAI_MODEL)
tool2 = sales_agent2.as_tool("sales_agent2", "Write a cold sales email")


sales_agent3 = Agent(name="Sales Agent 3", instructions=busy, model=OPENAI_MODEL)
tool3 = sales_agent3.as_tool("sales_agent3", "Write a cold sales email")



#### --------  Define Tools and Handoff for Sales Manager Agent  --------- ####

tools = [tool1, tool2, tool3]
handoff = [emailer_agent]


#### --------  Create Sales Manager Agent  --------- ####
# Will have acces to sales_agent tools
# Will then have a handoff to the emailer_agent 
# (which has the subject/html tools and send_html_email func)

sales_manager_instructions = """
You are a Sales Manager at ComplAI. Your goal is to find the single best cold sales email using the sales_agent tools.
 
Follow these steps carefully:
1. Generate Drafts: Use all three sales_agent tools to generate three different email drafts. Do not proceed until all three drafts are ready.
 
2. Evaluate and Select: Review the drafts and choose the single best email using your judgment of which one is most effective.
You can use the tools multiple times if you're not satisfied with the results from the first try.
 
3. Handoff for Sending: Pass ONLY the winning email draft to the 'Email Manager' agent. The Email Manager will take care of formatting and sending.
 
Crucial Rules:
- You must use the sales agent tools to generate the drafts — do not write them yourself.
- You must hand off exactly ONE email to the Email Manager — never more than one.
"""

sales_manager = Agent(
    name="Sales Manager",
    instructions=sales_manager_instructions,
    tools=tools,
    handoffs=handoff, # type: ignore
    model="gpt-4o-mini")

message = "Send out a cold sales email addressed to Dear CEO from Alice"


async def main():
    with trace("Automated SDR"):
        result = await Runner.run(sales_manager, message)
        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
