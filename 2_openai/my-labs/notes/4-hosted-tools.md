# OpenAI Hosted Tools

Hosted Tools are managed by OpenAI and available as Classes:

- __WebSearchTool__: agents that search the internet
- __FileSearchTool__: retrieves information from OpenAI Vector Stores
- __ComputerTool__: performs local pc tasks like clicking and screenshots (oh hell nah)


__Example of using WebSearchTool__

The WebSearchTool is more expensive, averaging $0.025 per call

```python
from agents import Agent, Runner, WebSearchTool, trace
from agents.model_settings import ModelSettings

INSTRUCTIONS = "You are a research assistant. Given a search term, you search the web for that term and \
produce a concise summary of the results. The summary must be 2-3 paragraphs and less than 300 \
words. Capture the main points. Write succintly, no need to have complete sentences or good \
grammar. This will be consumed by someone synthesizing a report, so it's vital you capture the \
essence and ignore any fluff. Do not include any additional commentary other than the summary itself."

search_agent = Agent(
    name="Search agent",
    instructions=INSTRUCTIONS,
    tools=[WebSearchTool(search_context_size="low")],
    model="gpt-4o-mini",
    model_settings=ModelSettings(tool_choice="required"), # forces the agent to use the tool
)

message = "Latest Agentic AI Frameworks in 2025"

with trace("Search"):
    result = await Runner.run(search_agent, message)

print(result.final_output)
```
