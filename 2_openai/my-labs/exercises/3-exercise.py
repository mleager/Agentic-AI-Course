import os
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# from dataclasses import dataclass
# from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import asyncio
from openai import AsyncOpenAI
from agents import Agent, Runner, input_guardrail, output_guardrail, function_tool, GuardrailFunctionOutput, OpenAIChatCompletionsModel, Tool


# Agents: 2  ( Emailer & Manager )
# Emailer Agent:
# - tools: subject_writer agent.as_tool, html_converter agent.as_tool && send_email function tool
# Manager Agent:
# - tools: the 3 Sales Agents
# - handoffs: Emailer Agent

# Guardrails: 3
# Input:
# - validate email address format ?
# Output:
# - validate email content ?

# Additions:
# - Guardrails with more complex rules and function tools
# - Agents using multiple Guardrails

OPENAI_MODEL_NAME = "gpt-4o-mini"
GEMINI_MODEL_NAME = "gemini-2.5-flash"
GROQ_MODEL_NAME = "gpt-oss-20b"


@input_guardrail
def validate_email_address(ctx, agent, email) -> GuardrailFunctionOutput:
    """Validate the email address format is <name>@<domain>."""
    try:
        username, domain = email.split('@')
        if not username or not domain:
            return GuardrailFunctionOutput(
                output_info="Invalid email address format",
                tripwire_triggered=True
            )
    except ValueError:
        return GuardrailFunctionOutput(
            output_info="Invalid email address format",
            tripwire_triggered=True
        )

    return GuardrailFunctionOutput(
        output_info="Email address format is valid",
        tripwire_triggered=False
    )


@output_guardrail
def validate_email_content(ctx, agent, email_content) -> GuardrailFunctionOutput:
    """Validate the email content is not empty or contains sensitive information."""
    if not email_content or any(sensitive_info in email_content for sensitive_info in ['password', 'credit card']):
        return GuardrailFunctionOutput(
            output_info="Email content contains sensitive information",
            tripwire_triggered=True
        )

    return GuardrailFunctionOutput(
        output_info="Email content is valid",
        tripwire_triggered=False
    )


class EmailSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file="/c/Users/mark/Documents/Coding/Agentic-AI-Course/.env", extra="ignore")

    email: str = Field(default="markleager92@gmail.com", alias="GMAIL")
    password: str = Field(default="", alias="APPG")
    max_retries: int = Field(default=3, alias="MAX_RETRIES")


class EmailFunctionTool:
    """A FunctionTool for sending emails from the Emailer Agent."""
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password

    @function_tool
    def send_email(self, subject: str, body: str, is_html: bool = False) -> dict[str, str]:
        context = ssl.create_default_context()

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.email
        msg['To'] = self.email

        if is_html:
            part1 = MIMEText(body, 'plain')
            part2 = MIMEText(body, 'html')
            msg.attach(part1)
            msg.attach(part2)
        else:
            part = MIMEText(body, 'plain')
            msg.attach(part)

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
                server.login(self.email, self.password)
                server.send_message(msg)
            return {'status': 'Email sent successfully', 'error': 'none'}
        except Exception as e:
            return {'status': 'Email failed to send', 'error': f'{str(e)}'}


class EmailerAgent:
    """An Agent for sending emails. 
    Uses 3 Tools: subject_writer, htm_converter, and send_email.
    subject_writer and html_converter as agents as tools.
    send_email as a function tool."""
    def __init__(self, config: EmailSettings):
        self.config = config
        self.model: str = OPENAI_MODEL_NAME
        self.email = EmailFunctionTool(config.email, config.password)

        self.agent_tools: list = self._create_agent_tools()
        self.tools: list = self.agent_tools + [self.email.send_email]
        self.agent: Agent = self._create_email_agent()

    def _create_email_agent(self) -> Agent:
        instructions = """You will receive an email with a subject and content. 
        Use the 'subject_checker' tool to get the subject.
        Then use the 'htm_converter' tool to convert the content into HTML.
        Finally, use the 'send_email' function tool to send the email."""

        return Agent(
            name="Emailer Agent",
            instructions=instructions,
            tools=self.tools,
            input_guardrails=[validate_email_address],
            model=self.model
        )
    
    def _create_agent_tools(self) -> list[Tool]:
        subject_instructions = """You will receive an email with a subject. 
        Your job is to check if a subject that captures the essence of the email content.
        If it does, return the subject
        Otherwise, create a new subject that captures the essence of the email content."""

        subject_writer = Agent(
            name="subject_writer",
            instructions=subject_instructions,
            model=self.model
        )

        html_instructions = """You will receive an email with a content, possibly text or markdown. 
        Your job is to convert the content into HTML format.
        Please use proper HTML formatting keep it organized.
        Please use CSS to make the email look visually appealing."""
        # Use the 'verify_html' guardrail to validate the output is HTML

        html_converter = Agent(
            name="html_converter",
            instructions=html_instructions,
            model=self.model
        )
        
        return [
            subject_writer.as_tool(tool_name=subject_writer.name, tool_description="Write a subject"), 
            html_converter.as_tool(tool_name=html_converter.name, tool_description="Convert content to HTML"),
        ]


class Sales:
    """The starting Agent.
    Uses 3 Agents as Tools: sales_agent1, sales_agent2, sales_agent3.
    Uses 1 Handoff: emailer_agent.
    Have 3 sales agents create an email, then handoff to the emailer agent."""

    def __init__(self, emailer_agent: EmailerAgent):
        self.emailer_agent = emailer_agent.agent
        self.handoffs: list = [self.emailer_agent]

        self.tools: list[Tool] = self._create_sales_agent_tools()
        self.agent: Agent = self._create_sales_manager()

    def _create_sales_agent_tools(self) -> list[Tool]:
        try:
            gemini_client = AsyncOpenAI(api_key=os.getenv('GEMINI_API_KEY', ''), base_url=os.getenv('GEMINI_BASE_URL', 'https://api.openai.com/v1/'))
            gemini_model = OpenAIChatCompletionsModel(model=GEMINI_MODEL_NAME, openai_client=gemini_client)

            groq_client = AsyncOpenAI(api_key=os.getenv('GROQ_API_KEY', ''), base_url=os.getenv('GROQ_BASE_URL', ''))
            groq_model = OpenAIChatCompletionsModel(model=GROQ_MODEL_NAME, openai_client=groq_client)
        except Exception as e:
            print(f"Failed to create sales agents: {str(e)}")
            gemini_model = OPENAI_MODEL_NAME
            groq_model = OPENAI_MODEL_NAME

        instructions = """You are a sales representative. Write a cold sales email to a potential client.
        You are advertising that you're big and strong and looking for love.
        Act like you: """

        sales_agent1 = Agent(
            name="Sales Agent 1",
            instructions=instructions+"are overconfident",
            model=OPENAI_MODEL_NAME,
            output_guardrails=[validate_email_content]
        )

        sales_agent2 = Agent(
            name="Sales Agent 2",
            instructions=instructions+"have a club foot",
            model=gemini_model,
            output_guardrails=[validate_email_content]
        )

        sales_agent3 = Agent(
            name="Sales Agent 3",
            instructions=instructions+"think the Earth is flat",
            model=groq_model,
            output_guardrails=[validate_email_content]
        )
        
        return [
            sales_agent1.as_tool(tool_name=sales_agent1.name, tool_description="Write an email"),
            sales_agent2.as_tool(tool_name=sales_agent2.name, tool_description="Write an email"),
            sales_agent3.as_tool(tool_name=sales_agent3.name, tool_description="Write an email"),
        ]
    
    def _create_sales_manager(self) -> Agent:
        instructions = """You are a sales representative. 
        Your job is to write a 'cold' email introducing yourself.
        Use the tools to generate 3 versions email, and select the best one.
        Then perform the handoff to the Emailer Agent."""

        return Agent(
            name="Sales Manager",
            instructions=instructions,
            tools=self.tools,
            handoffs=self.handoffs,
            model=OPENAI_MODEL_NAME
        )


async def main():
    config = EmailSettings()
    emailer_agent = EmailerAgent(config)
    sales = Sales(emailer_agent)
    manager_agent = sales.agent

    message = "Please write an email to Bertha from Bob. Don't let them know you're crazy."

    # Create a runner
    result = await Runner.run(
        starting_agent=manager_agent,
        input=message 
    )

    print(f"Final response:\n{result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
