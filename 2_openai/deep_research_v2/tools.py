from agents import Runner, function_tool
from planner import PlanningAgent, WebSearchItem, WebSearchList
from searcher import SearchAgent
from clarifier import ClarifierAgent, ClarifyingQuestions
from updater import TopicUpdaterAgent
import asyncio


# INFO: Clarifier & Topic Updater Agents aren't used as the 
# Manager Agent's function tools anymore (will remove in the future)
clarifier_agent = ClarifierAgent()
topic_updater_agent = TopicUpdaterAgent()

planning_agent = PlanningAgent()
search_agent = SearchAgent()


###############################################################################
## CLARIFIER

@function_tool
async def generate_clarifiers(research_topic: str) -> ClarifyingQuestions:
    response = await Runner.run(clarifier_agent, research_topic)
    return response.final_output_as(ClarifyingQuestions)


###############################################################################
## TOPIC UPDATER

@function_tool
async def update_topic(topic: str, questions: str) -> str:
    input = f"Topic: {topic}\nClarifying Questions: {questions}"
    result = await Runner.run(topic_updater_agent, input)
    return result.final_output


###############################################################################
## MANAGER

@function_tool
async def plan_searches(query: str) -> WebSearchList:
    """Create 3 search terms based on user's research topic."""
    try:
        result = await Runner.run(planning_agent, query)
        search_plan = result.final_output_as(WebSearchList)
        return search_plan
    except Exception as e:
        return WebSearchList(
            searches=[WebSearchItem(reason=f"Error: {e}", query=query)]
        )


@function_tool
async def perform_searches(search_plan: WebSearchList) -> list[str]:
    """Perform all searches and return their summaries."""
    tasks = [asyncio.create_task(_search(item)) for item in search_plan.searches]
    results = []
    for task in asyncio.as_completed(tasks):
        result = await task
        results.append(result)
    return results


async def _search(item: WebSearchItem) -> str:
    """Use the WebSearchTool to perform each search and generate a summary."""
    input = f"Search term: {item.query}\nReason for searching: {item.reason}"
    try:
        result = await Runner.run(search_agent, input)
        return result.final_output
    except Exception as e:
        return f"Error performing search: {e}"
