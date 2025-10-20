import os
import ssl
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from pydantic import BaseModel
import asyncio
from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    trace,
    function_tool,
    input_guardrail,
    output_guardrail,
    GuardrailFunctionOutput,
    OpenAIChatCompletionsModel,
)

load_dotenv(override=True)

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_KEY = os.getenv("GROQ_API_KEY", "")

GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "")

GMAIL = os.getenv("GMAIL_ADDRESS", "")
APPG = os.getenv("APPG", "")

openai_model_name = "gpt-4o-mini"
gemini_model_name = "gemini-2.5-flash"
groq_model_name = "gpt-oss-20b"


####  PreReq - Create Function Tool  ####


@function_tool
async def send_email(subject: str, body: str) -> dict[str, str]:
    context = ssl.create_default_context()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL
    msg["To"] = GMAIL

    msg.attach(MIMEText(body, "plain"))
    msg.attach(MIMEText(body, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(GMAIL, APPG)
            server.send_message(msg)
            return {"message": "Email sent successfully"}
    except Exception as e:
        return {"error": str(e)}


####  PreReq - Create Input Guardrail - used by Sales Manager Agent  ####


class NameCheckOutput(BaseModel):
    is_name_in_message: bool
    name: str


input_guardrail_agent = Agent(
    name="Name Checker",
    instructions="Check if the user is including someone's personal name in what they want you to do.",
    model=openai_model_name,
    output_type=NameCheckOutput,
)


@input_guardrail
async def check_name_in_message(ctx, agent, message) -> GuardrailFunctionOutput:
    result = await Runner.run(
        starting_agent=input_guardrail_agent, input=message, context=ctx.context
    )

    is_name_in_message = result.final_output.is_name_in_message

    return GuardrailFunctionOutput(
        output_info={"found_name": result.final_output},
        tripwire_triggered=is_name_in_message,
    )


####  PreReq - Create Output Guardrail - used by Emailer Agent  ####


class SalesEmailOutput(BaseModel):
    has_subject: bool
    has_body: bool


output_guardrail_agent = Agent(
    name="Sales Email Generator",
    instructions="Generate a cold sales email.",
    model=openai_model_name,
    output_type=SalesEmailOutput,
)


@output_guardrail
async def check_email_content(ctx, agent, output) -> GuardrailFunctionOutput:
    subject = await Runner.run(
        starting_agent=output_guardrail_agent, input=output.subject, context=ctx.context
    )
    body = await Runner.run(
        starting_agent=output_guardrail_agent, input=output.body, context=ctx.context
    )

    if subject.final_output.has_subject and subject.final_output.has_body:
        return GuardrailFunctionOutput(
            output_info={"subject": subject.final_output, "body": body.final_output},
            tripwire_triggered=False,
        )

    return GuardrailFunctionOutput(
        output_info={"subject": subject.final_output, "body": body.final_output},
        tripwire_triggered=True,
    )


####  0. Create the Instructions that the Sales Agents will use (not created yet)  ####


instructions = """You are a sales agent working for ComplAI, a company that 
provides a SaaS tool for ensuring SOC2 compliance, and preparing for audits, 
powered by AI. You write proffessional, cold emails."""

charismatic = (
    instructions + " You maintain a strong, charismatic personality in your emails"
)

busy = instructions + " Your emails need to be as short and direct as possible"


####  1. Create Clients to use other LLM Models  ####


gemini_client = AsyncOpenAI(api_key=GEMINI_KEY, base_url=GEMINI_BASE_URL)

groq_client = AsyncOpenAI(api_key=GROQ_KEY, base_url=GROQ_BASE_URL)


####  2. Create Models from the Clients  ####


gemini_model = OpenAIChatCompletionsModel(
    model=gemini_model_name, openai_client=gemini_client
)

groq_model = OpenAIChatCompletionsModel(
    model=groq_model_name, openai_client=groq_client
)


####  3. Create Agents from the Models  ####


sales_agent1 = Agent(
    name="OpenAI Agent", instructions=instructions, model=openai_model_name
)

sales_agent2 = Agent(name="Gemini Agent", instructions=charismatic, model=gemini_model)

sales_agent3 = Agent(name="Groq Agent", instructions=busy, model=groq_model)


####  4. Create Tools from the Agents  ####


description = "Write a cold sales email"

tool1 = sales_agent1.as_tool(tool_name=sales_agent1.name, tool_description=description)

tool2 = sales_agent2.as_tool(tool_name=sales_agent2.name, tool_description=description)

tool3 = sales_agent3.as_tool(tool_name=sales_agent3.name, tool_description=description)


####  5. Create the HTML Email Tools  ####


subject_instruction = """You can write a subject for a cold sales email.
You're given a message and you need to evaluate the subject if it's given.
If the given subject is good, reply with the subject.
If the given subject is bad, create a new subject.
If no subject exists, create one."""

subject_writer = Agent(
    name="Subject Writer", instructions=subject_instruction, model=openai_model_name
)

subject_tool = subject_writer.as_tool(
    tool_name=subject_writer.name,
    tool_description="Write a subject for a cold sales email",
)


html_instructions = """You can convert a text email body to an HTML email body.
You are given a text email which may have some markdown, and you need to convert it to HTML.
The new HTML email body should include inline CSS to make it visually appealing."""

html_converter = Agent(
    name="HTML Converter", instructions=html_instructions, model=openai_model_name
)

html_tool = html_converter.as_tool(
    tool_name=html_converter.name,
    tool_description="Convert a text email body to an HTML email body",
)


email_tools = [subject_tool, html_tool, send_email]


####  6. Create the Emailer Agent  ####


emailer_instructions = """You are an email formatter and sender.
You receive the body of an email to be sent.
You first use the subject_writer tool to check, revise, or create a new subject.
Then you use the html_converter tool to convert the email body to HTML.
Finally you use the send_email tool to send the email."""


emailer_agent = Agent(
    name="Emailer Agent",
    instructions=emailer_instructions,
    model=openai_model_name,
    tools=email_tools,
    output_guardrails=[check_email_content],
    handoff_description="Convert an email to HTML and send it",
)


####  7. Create the Sales Manager Agent & use the Tools, the Handoff, and the Guardrails  ####


tools = [tool1, tool2, tool3]
handoffs: list = [emailer_agent]


sales_manager_instructions = """You are a Sales Manager working for ComplAI.
You use the tools given to you to generate cold sales emails.
You never generate sales emails yourself; you always use the tools.
You try all the available tools and then compare their results.
Pick the best sales email, then use the handoff to the Emailer Agent to send it."""


sales_manager = Agent(
    name="Sales Manager",
    instructions=sales_manager_instructions,
    model=openai_model_name,
    tools=tools,
    handoffs=handoffs,
    input_guardrails=[check_name_in_message],
)


####  8. Run the Sales Manager Agent  ####


async def main():
    message = (
        "Send out a cold sales email addressed to 'Dear CEO' on behalf of 'Alice'."
    )

    with trace("Automated SDR 2"):
        result = await Runner.run(sales_manager, message)

        print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
