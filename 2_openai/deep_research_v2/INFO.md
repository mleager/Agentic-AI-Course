# DRAFT


## ADD CLARIFICATION

User --> Manager --> User --> Manager --> Writer
- update topic, plan searches, perform searches


How to make Manager ask a question, then receive the answer, and call tools


Gradio State Management:

1. Learn Gradio State

2. Learn Gradio Blocks

3. Can input from Text Blocks be used as input to agents & function tools?


UI Structure:

Option 1: Act like a regular Chatbot

- normal chatbot interface

- 1 text-box, same throughout, no state


Option 2: Create UI "blocks"

- when asking questions, give 3 separate text boxes to receive answer

- initial text-box, then 3 (one for each question), then back to original text-box


Option 3: Act like an Installation Wizard

- enter text, then click "next" to continue (each step will have its own text-box sequentially)

- 1 box per step, click "next" to continue


-------------------------------------------------------------------------------

__Purpose__

A Research-Based Chatbot

Give it a query and it will return a report on the topic


__Actions__

A Manager Agent orchestrates the process

The other Agents will be used as tools or handoffs


__Phases & Other Agents__:

Clarifying Phase:

- Models asks 3 clarifying questions about the topic to get the specifics and scope

Planning Phase:

- Create 3 search terms that will get the best results for the given search topic

Searching Phase:

- Actually search the internet using the queries from the Planning Phase.
  Returns a summary of each search

Writing Phase:

- Use the returned summaries from the Searching Phase to create a full report


__Flow__

Without Clarification:

1. User gives a topic
2. Manager Agent receives the input and calls the other Agents
3. Planning Agent creates multiple search terms
4. Search Agent google's the search terms and creates a summary for each result
5. The Writer Agent combines all the summaries and creates a full report
6. The User gets the report returned to them

User --> Manager --> Planning --> Searching --> Writing --> User


With Clarification:

1. User gives a topic
2. Manager Agent then asks 3 clarifying questions (scope, focus, audience)
3. Manager Agent receives the input and calls the other Agents
3. Planning Agent creates multiple search terms
4. Search Agent google's the search terms and creates a summary for each result
5. The Writer Agent combines all the summaries and creates a full report
6. The User gets the report returned to them

User --> Clarify --> Manager --> Planning --> Searching --> Writing --> User


__Structure__

Manager Agent

Tools:
- Clarifying Agent
- Planning Agent
- Search Agent

Handoffs:
- Writer Agent

If Planning and Search Agents are tools, can they be ordered?

Manager passes input to Planning Tool and gets `searches`
Manager passes `searches` to the Searching Agent and gets `summaries`
Manager handoff `summaries` to Writer Agent
Writer Agent creates the `report` and returns to the User
