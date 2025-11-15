# WebSearchTool with Structured Outputs

Agents can return custom objects

The Agent uses JSON to populate the object's attributes


__Example__

```python
from pydantic import BaseModel, Field

instructions = """You're a helpful research assistant.
Given a query, come up with a set of web searches that will get the best answers to the query.
Output 3 different web searches.
"""

class WebSearchItem(BaseModel):
    reason: str = Field(
        description="Your reasoning for why this search is important to the query."
    )

    query: str = Field(
        description="The search term to use for the web search."
    )

class WebSearchList(BaseModel):
    searches: list[WebSearchItem] = Field(
        description="A list of web searches to best answer the query."
    )

planner_agent = Agent(
    name="Planner Agent",
    instructions=instructions,
    model="gpt-4o-mini",
    output_type=WebSearchList
)

message: str = "Latest Agentic AI frameworks in 2025"

with trace("Searches"):
    result = await Runner.run(planner_agent, message)

print(result.final_output)
```


__Breakdown__

1. Base `instructions`:
- the system prompt you choose will determine the structure of the output


2. `WebSearchItem` class:
- contains the reason the model chose that search term, and the search term it chose


3. `WebSearchList` class:
- contains a list of all the generated web searches


4. `Planner_Agent`:
- come up with 3 different web searches to answer a question


5. `Run`:
- ask the model to generate multiple search terms that can best answer the question:  
  "Latest Agentic AI frameworks in 2025"


__Basic Chain of Events__

```ini
[System Prompt]
"Create 3 good web search queries to answer a question"

[User]
"Latest Agentic AI frameworks in 2025"

[System]
WebSearchItem(reason: "...", query: "..."),
WebSearchItem(reason: "...", query: "..."),
WebSearchItem(reason: "...", query: "...")
```

```yml
System Prompt: "Create 3 good web search queries to answer a question"

User: "Latest Agentic AI frameworks in 2025"

System:
  - WebSearchItem
      reason: "..."
      query: "...",
  - WebSearchItem
      reason: "..."
      query: "...",
  - WebSearchItem
      reason: "..."
      query: "...",

  - WebSearchItem(reason: "...", query: "...")
```

```json
{
    "system_prompt": "Create 3 good web search queries to answer a question",
    "user": "Latest Agentic AI frameworks in 2025.",
    "system": [
        "WebSearchItem": {
            "reason": "...",
            "query": "...",
        },
        "WebSearchItem": {
            "reason": "...",
            "query": "...",
        },
        "WebSearchItem": {
            "reason": "...",
            "query": "...",
        },
    ]
}
```
