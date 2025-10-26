# Random Questions to Check

For `2_openai/deep_research/research_manager.py`:

- The app uses each Agent as a function call, not as tools or handoffs

__Code__:
```python
# This code runs each agent sequentially,
# like individual functions, and they return custom Types/Structs

search_plan = await plan_searches(query)

search_results = await perform_searches(search_plan)

report = await write_report(query, search_results)
```


__Questions__

Why not create a "Research-Agent" that uses the other agents as Tools or Handoffs?

For example, the "writer_agent" is just an agent that takes a query and some search terms,  
and returns a ReportData struct (summary, report, and some more research topics)

```python
Research-Agent = Agent(
  name="Research-Agent",
  instructions=INSTRUCTIONS,
  model=OPENAI_MODEL,
  tools=[planner_agent_tool, search_agent_tool]
  handoffs=[writer_agent]
)
```


__WHY?__

It is because the Agents return Types/Structs instead of text?

- and the Types are used as inputs for the next Agent, rather than a text Handoff

