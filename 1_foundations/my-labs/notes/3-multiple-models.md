# Foundations: Lab 3

## Comparing and Calling Multiple Models

You can call multiple Models using the OpenAI() Library

    - Anthropic uses its own Library


You can easily communicate with multiple Models with the SDK

    - compare output of multiple LLMs


Common Examples:

    - having multiple LLMs answer the same question and compare results

    - have LLMs validate the output of another LLM

    - have an LLM choose which LLM to send a particulat input to


In "2_lab2.ipynb" the notebook goes through the following: 

    1. constructing an initial question

    2. then having multiple different models answer the question

    3. finally a model compares all given answers and ranks them


I would consider this either of the following Workflow Patterns:

    - Prompt Chaining

    - Evaluator - Optimizer


Output from the prompts are chained to the Evaluator for comparison

