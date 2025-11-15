from agents import Agent, Runner, trace, gen_trace_id
from writer import WriterAgent
from tools import plan_searches, perform_searches # generate_clarifiers, update_topic
from model_type import OPENAI_MODEL


UPDATED_TOOLS: list = [plan_searches, perform_searches]

HANDOFFS: list = [WriterAgent()]

UPDATED_INSTRUCTIONS: str = """
You are a research manager, and you'll be given an updated research topic.

You will use these tools and in this order:

1. plan_searches(updated_topic: str)
   - USE THIS SECOND with the user's updated research topic
   - Returns: search_terms

2. perform_searches(search_terms: list)
   - USE THIS THIRD with the search_terms from planning_tool
   - REQUIRES: Output from planning_tool
   - Returns: summaries

3. writer_agent (handoff)
   - USE THIS LAST with the summaries from search_tool
   - REQUIRES: Output from search_tool

WORKFLOW:
Updated Research Topic → planning_tool → search_tool → writer_agent → Final Report

You cannot use 'perform_searches' without the 'plan_searches' results.
You cannot handoff to writer_agent without 'perform_searches' results.
"""


class ManagerAgent(Agent):
    def __init__(self):
        super().__init__(
            name="Manager",
            instructions=UPDATED_INSTRUCTIONS,
            model=OPENAI_MODEL,
            tools=UPDATED_TOOLS,
            handoffs=HANDOFFS,
        )

    async def run_stream(self, query: str):
        trace_id = gen_trace_id()
        with trace("Research", trace_id=trace_id):
            result = await Runner.run(self, query)
            yield result.final_output

    async def run(self, query: str):
        trace_id = gen_trace_id()
        with trace("Research", trace_id=trace_id):
            result = await Runner.run(self, query)
            return result.final_output


# TOOLS: list = [generate_clarifiers, update_topic, plan_searches, perform_searches]
# INSTRUCTIONS: str = """
# You are a research manager with access to these tools:

# 1. generate_clarifiers(topic: str)
#    - USE THIS FIRST with the user's research topic
#    - Returns: clarifying questions

# IMPORTANT: After generating the clarifying questions, stop and wait for the user's answers before calling any other tools.

# 2. update_topic(topic: str, answers_to_clarifying_questions: str)
#    - USE THIS SECOND with the original research topic and the generated clarifying questions
#    - Returns: updated_topic

# 3. plan_searches(updated_topic: str)
#    - USE THIS SECOND with the user's updated research topic
#    - Returns: search_terms

# 4. perform_searches(search_terms: list)
#    - USE THIS THIRD with the search_terms from planning_tool
#    - REQUIRES: Output from planning_tool
#    - Returns: summaries

# 5. writer_agent (handoff)
#    - USE THIS LAST with the summaries from search_tool
#    - REQUIRES: Output from search_tool

# WORKFLOW:
# User Topic → generate_clarifiers → wait for User answer → update_topic → planning_tool → search_tool → writer_agent → Final Report

# You cannot use 'generate_clarifiers' without a user's research topic.
# You cannot use 'update_topic' without the user's answers to the clarifying questions.
# You cannot use 'perform_searches' without the 'plan_searches' results.
# You cannot handoff to writer_agent without 'perform_searches' results.
# """
