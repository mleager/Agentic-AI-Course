# Foundations: Lab 2

## What is Agentic AI

AI Agents are programs where LLM outputs control the workflow


Features of AI Agents:

    - multiple LLM calls (chaining)

    - ability to use Tools

    - multiple LLMs interacting together

    - an LLM that coordinates other actions

    - autonomy


## Agentic Systems

2 categories of Agentic Systems as defined by Anthropic

    - Workflows

    - Agents


Workflows:

    Systems where LLM & Tools are orchestrated through pre-defined code paths


Agents:

    Systems where LLMs dynamically managed their own processes and tool usage,  
    maintaining control over how they accomplish tasks


## Workflow Design Patterns

Prompt Chaining

    - decomposed into fixed sub-tasks

    - frame multiple LLMs calls together for concise output

    - can be used for cleaning, formatting, checking output, etc.

```bash
- IN --> LLM1 --> Code/Tooling --> LLM2 --> LLM3 --> OUT
```


Routing

    - direct an input into specialized LLMs

    - like a load balancer for LLMs

    - the Routing LLM decides which LLM to route the input to

```bash
                      |--> LLM1 --|
- IN --> LLM Router --|--> LLM2 --|--> OUT
                      |--> LLM3 --|
```


Parallelization

    - break down tasks into sub-tasks and run the multiple sub-tasks concurrently

    - python code breaks down the tasks to the parallel LLMs

    - python code aggregator combines the sub-tasks back into a single output

```bash
                       |--> LLM1 --|
- IN --> Coordinator --|--> LLM2 --|--> Aggregator --> OUT
           (Code)      |--> LLM3 --|      (Code)
```


Orchestrator - Worker

    - complex tasks are broken down dynamically and re-combined

    - similiar to Parallelization but with LLMs instead of code

    - the orchestrator decides how to break down complex tasks

```bash
                        |--> LLM1 --|
- IN --> Orchestrator --|--> LLM2 --|--> Synthesizer --> OUT
            (LLM)       |--> LLM3 --|       (LLM)

```


Evaluator - Optimizer

    - LLM output is validated by another

    - An LLM generates an output that's checked and validated by another LLM

    - If successful, the validated output is accepted and returned

    - If not, the output is sent back to the LLM with feedback for improvement

    - feedback loop until the LLM Generator output is validated

```bash
- IN --> LLM Generator --> LLM Evaluator --> OUT
```


## Agent Design Patterns

Compared to Workflow Patterns, Agent Design Patterns are more

    - fluid and dynamic


Agent Design Patterns are:

    - open-ended

    - use feedback loops, usually with multiple iterations

    - no fixed path

    - can make their own decisions and modifications as needed


```bash
- IN --> LLM Call --> Action --> Environment
             ^                      |
             |------- Feedback -----|
```


## Risks of Agent Frameworks

Just as Agent Design Patterns can be very helpful, they have drawbacks


While Agent Patterns have greater flexibility

    - it also introduces a level of unpredictability


Requires greater monitoring and visibility into Agent actions

    - use guardrails


Cons:

    - unpredictable paths

    - unpredictable output

    - unpredictable costs

