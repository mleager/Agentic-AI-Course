from agents import Agent, Runner, function_tool
from model_type import OPENAI_MODEL


INSTRUCTIONS = """
You are a senior researcher tasked with writing a cohesive report for a research query.
You will be provided with the original query, and some initial research done by a research assistant.
You should first come up with an outline for the report that describes the structure and 
flow of the report. Then, generate the report and return that as your final output.
The final output should be in markdown format, and it should be lengthy and detailed. 
Aim for at least 2-3 pages of content.
"""


class WriterAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Writer Agent",
            instructions=INSTRUCTIONS,
            model=OPENAI_MODEL,
            handoff_description="Creates a final, cohesive report for a research topic.",
        )

    @function_tool
    async def write_report(self, query: str, search_results: list[str]) -> str:
        input = f"Original query: {query}\nSummarized search results: {search_results}"
        try:
            result = await Runner.run(self, input)
            return result.final_output
        except Exception as e:
            return f"Error writing report: {e}"
