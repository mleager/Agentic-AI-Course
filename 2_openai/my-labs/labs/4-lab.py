from pydantic import BaseModel, Field
from agents import Runner, Agent, WebSearchTool
from agents.model_settings import ModelSettings
import asyncio


# Steps:
# ------------------------------------------------------------------------------------
# 1. Planner: Create a Planning Agent to generate 3 search terms based on a given query.
# 2. Search:  Use the Search Agent's WebSearchTool to search for the generated search terms.
# 3. Report:  Use the Report Agent to create a report from the Search Agent's summary.
# ------------------------------------------------------------------------------------


# NOTE: 1.
# Create 3 Search Terms to answer the given question.
# - Doesn't answer the questions, it just creates good search terms
#   that will best answer the given question.


class WebSearchItem(BaseModel):
    reason: str = Field(description="Reason for choosing the search term")

    query: str = Field(description="The search term itself")


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="List of search terms")


# Break down a broad user query into specific, effective search terms

planning_instruction = """Given a google query, create 3 search terms 
that can be used to create the best answer to the given query."""


# Create the google search terms that will get the best results

planning_agent = Agent(
    name="PlanningAgent",
    instructions=planning_instruction,
    model="gpt-4o-mini",
    output_type=WebSearchPlan,
)


# NOTE: 2.
# Actually perform the internet search and summarize the results.
# - Will use all of the generated search terms from the planning_agent
#   to create 3 reports for each search term.


search_instructions = """Given a search term, search the web for that term and 
produce a concise summary of the results. The summary must be 2-3 paragraphs 
and no more than 300 words. Capture the main points. Write succinctly, no need 
to have complete sentences or good grammar. This summar ywill be used by someone 
creating a fuill report, so it's vital to capture the essence, and ingnore any fluff.
Do not include any additional commentary other than the summary itself."""


# Use the WebSearchTool to perform the internet search

search_agent = Agent(
    name="SearchAgent",
    instructions=search_instructions,
    model="gpt-4o-mini",
    tools=[WebSearchTool(search_context_size="low")],
    model_settings=ModelSettings(tool_choice="required"),
)


# INFO: 3.
# Create the report agent to create a report for each search term


class ReportData(BaseModel):
    short_summary: str = Field(description="Short summary of the search results")

    markdown_report: str = Field(description="Markdown report for the search results")

    followup_questions: str = Field(description="Suggested topics to research further")


report_instructions = """You are a senior researcher tasked with writing a cohesive 
report for a research query. You will be provided with the original query, and some 
initial research done by a research assistant. You should first come up with an outline 
for the report that describes the strucuture and flow of the report. 
Then, generate the report abd return that as your final output. 
The final output should be in markdown format, and it should be lengthy and detailed. 
Aim for either 5-10 pages of content, or at least 1000 words."""


# Create the report

reporter_agent = Agent(
    name="ReporterAgent",
    instructions=report_instructions,
    model="gpt-4o-mini",
    output_type=ReportData,
)


# INFO: Functions to run the agents, perform the searches, and summarize the results


async def plan_searches(query: str) -> WebSearchPlan:
    """Use the planner_agent to plan which searches
    will be most effective to run for the query"""
    print("Planning searches...")
    result = await Runner.run(planning_agent, f"Query: {query}")
    return result.final_output


async def perform_searches(search_plan: WebSearchPlan) -> list[str]:
    """Call search() for each item in the search plan"""
    tasks = [asyncio.create_task(search(item)) for item in search_plan.searches]
    results = await asyncio.gather(*tasks)
    return results


async def search(item: WebSearchItem) -> str:
    """Use the search_agent to perform a search for the given query"""
    input = f"Search: {item.query}\nReason for searching: {item.reason}"
    result = await Runner.run(search_agent, input)
    return result.final_output


async def write_report(query: str, search_results: list[str]) -> ReportData:
    """Use the reporter_agent to create a report for the given query"""
    input = f"Query: {query}\nSummarized search results: {search_results}"
    result = await Runner.run(reporter_agent, input)
    return result.final_output


async def main():
    # 1. Intitial query
    query = "Latest Agentic AI frameworks in 2025"

    # 2. Use the planning agent to generate search terms
    search_plan = await plan_searches(query)

    # 3. Use the search and report agents to generate a report
    search_results = await perform_searches(search_plan)

    # 4. Use the reporter agent to create a markdown report
    report = await write_report(query, search_results)
    
    print(report.markdown_report)


    # --------------------------------------------------------------------------------------- 
    # 1. Give the initial search term to the planning agent
    # 2. The PlanningAgent returns a WebSearchPlan object (list of WebSearchItem objects)
    # 3. The SearchAgent performs searches for each item in the WebSearchPlan
    # 4. The SearchAgent returns a list of search results (strings, not any custom objects)
    # 5. The ReportAgent takes the original query, and the list of search results from SearchAgent
    # 6. The ReportAgent returns a ReportData object containing:
    #    - the short summary, the full markdown report, and any further questions to research
    # --------------------------------------------------------------------------------------- 


if __name__ == "__main__":
    asyncio.run(main())
