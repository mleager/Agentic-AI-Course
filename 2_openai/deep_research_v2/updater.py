from agents import Agent
from model_type import OPENAI_MODEL


INSTRUCTIONS = """You are a helpful assistant.
Your task is to revise the given research topic using the provided answers 
to clarifying questions to increase its relevance and accuracy.
The given context covers the following:
1. The scope of the research topic.
2. The focus of the research topic.
3. The audience of the research topic.
Return the revised topic.
"""


class TopicUpdaterAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Clarifier Agent",
            instructions=INSTRUCTIONS,
            model=OPENAI_MODEL,
        )
