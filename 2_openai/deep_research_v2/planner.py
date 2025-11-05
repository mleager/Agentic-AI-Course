from agents import Agent
from pydantic import BaseModel, Field
from model_type import OPENAI_MODEL


NUM_SEARCHES = 1
INSTRUCTIONS = f"""
You are a Research Assistant. You will be given a research topic.
Your task is to create {NUM_SEARCHES} google search queries that will get the best search 
information about the topic.
You will return a list of WebSearchItem types.
"""


class WebSearchItem(BaseModel):
    reason: str = Field(description="Reason for this search result")
    query: str = Field(description="Google search query")


class WebSearchList(BaseModel):
    searches: list[WebSearchItem] = Field(description="List of Google search queries")


class PlanningAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Planning Agent",
            instructions=INSTRUCTIONS,
            model=OPENAI_MODEL,
            output_type=WebSearchList,
        )
