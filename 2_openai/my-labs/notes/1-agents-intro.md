# Agents Intro

## Basic Terminology

`Agents`:

- Represents the AI Model (LLM)


`Handoffs`:

- Represents the interaction between Agents


`Guardrails`:

- Represents the checks/controls you put around the Agent to stay in scope of the task


`Sessions`:

- Automatically maintains conversation history across Agent Runs


## 3 Steps to run an Agent

Create  -->  Track  -->  Run

1. Create an instance of Agent

2. Use `with trace()` to track the Agent

3. Call `await runner.run()` to run the Agent


## Why Use the Agents SDK

The SDK has two driving design principles:

1. Enough features to be worth using, but few enough primitives to make it quick to learn.
2. Works great out of the box, but you can customize exactly what happens.


### Main features of the SDK:


__Agent loop:__

- Built-in agent loop that handles calling tools, sending results to the LLM, and looping until the LLM is done


__Python-first:__

- Use built-in language features to orchestrate and chain agents, rather than needing to learn new abstractions


__Handoffs:__

- A powerful feature to coordinate and delegate between multiple agents


__Guardrails:__

- Run input validations and checks in parallel to your agents, breaking early if the checks fail


__Sessions:__

- Automatic conversation history management across agent runs, eliminating manual state handling


__Function tools:__

- Turn any Python function into a tool, with automatic schema generation and Pydantic-powered validation


__Tracing:__

- Built-in tracing that lets you visualize, debug and monitor your workflows,  
  as well as use the OpenAI suite of evaluation, fine-tuning and distillation tools.
