from agents import Agent, WebSearchTool, ModelSettings
from model_type import OPENAI_MODEL


INSTRUCTIONS = """
You are a research assistant. Given a search term, you search the web for that term and
produce a concise summary of the results. The summary must be 2-3 paragraphs and less than 300
words. Capture the main points. Write succintly, no need to have complete sentences or good
grammar. This will be consumed by someone synthesizing a report, so its vital you capture the
essence and ignore any fluff. Do not include any additional commentary other than the summary itself.
---
You are a Research Assistant. You will be given search queries.
Use the WebSearchTool to perform each search, and return a summary of the results.
"""


class SearchAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Search Agent",
            instructions=INSTRUCTIONS,
            model=OPENAI_MODEL,
            tools=[WebSearchTool(search_context_size="low")],
            model_settings=ModelSettings(tool_choice="required"),
        )
