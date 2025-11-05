from agents import Agent
from pydantic import BaseModel, Field
from model_type import OPENAI_MODEL


INSTRUCTIONS = """
You are a Research Assistant.
Your task is to recieve a Research Topic and create 3 clarifying questions.
Your goal of your questions is to provide a better context for the research topic.
The 3 questions you ask will follow this format:
1. Scope: how narrow the research topic should focus
2. Focus: the main focus of the research topic
3. Audience: the target audience for the research topic
"""


class ClarifyingQuestions(BaseModel):
    scope: str = Field(description="How narrow the research topic should focus")
    focus: str = Field(description="The main focus of the research topic")
    audience: str = Field(description="The target audience for the research topic")


class ClarifierAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Clarifier Agent",
            instructions=INSTRUCTIONS,
            model=OPENAI_MODEL,
            output_type=ClarifyingQuestions,
        )
