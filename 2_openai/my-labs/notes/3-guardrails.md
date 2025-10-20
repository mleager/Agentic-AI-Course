# Guardrails

## Takeaways

__Placement__:          Input guardrails run before agent processing, output guardrails run after
__Function vs Agent__:  Simple checks use functions, complex validation uses dedicated agents
__Structured Outputs__: Use Pydantic models for consistent guardrail responses
__Layered Protection__: Combine multiple guardrails for comprehensive safety
__Context Awareness__:  Guardrails can access user context and history for smarter decisions
__Tripwire Logic__:     tripwire_triggered=True blocks the request/response

## Intro 
Guardrails can't be inserted at all points in the workflow

Guardrails can only be used in 2 places:

- the input at the beginning    (the first agent)
- the output at the end         (the last agent)

These are called:

- Input Guardrails
- Output Guardrails

__Note:__ Guardrails will always need to return the `GuardrailFunctionOutput` type


## Input Guardrails

These run on the intial user input before it reaches the main Agent

Can be used for:

- filter out inappropriate or malicious content
- validate the format or length of the input
- prevent the Agent from being used for unintended purposes


## Output Guardrails

These run on the Agent's final output before it's returned to the user

Can be used for:

- filter out forbidden words or phrases from the Agent's response
- ensure the output adheres to specific safety or content guidelines
- validate the structure or format of the output


## Implementation

Guardrails can be used as:

- function decorators
- Agents themselves

__Functions__

Function that performs a check whether the "tripwire" was set off

Works just like adding a tool

```python
from agents import GuardrailFunctionOutput

# context and agent params are supplied by the Agent
@input_guardrail
def banned_words(context, agent, user_input: str) -> GuardrailFunctionOutput:
    banned_words = ["fuck", "shit", "got daymn"]
    for word in banned_words:
        if word in user_input.lower():
            return GuardrailFunctionOutput(tripwire_triggered=True, output_info={"reason": f"Input contains {word}"})
    return GuardrailFunctionOutput(tripwire_triggered=False)

    agent = Agent(
        name="Agent",
        instructions="You're a helpful assistant",
        input_guardrails=[banned_words]
    )
```


__Guardrail Agent__

More complex guardrails can be implemented as seperate, lighter Agents

```python
class CheckOutputBeforeProcessing(BaseModel):
    is_safe: bool
    contains_sensitive_data: bool
    quality_score: int
    approved: bool

guardrail_agent = Agent(
    name="Output Validator",
    instructions="Check if output is safe, doesn't contain sensitive data, and meets quality standards",
    output_type=CheckOutputBeforeProcessing,
    model="gpt-4o-mini"
)

@output_guardrail
async def agent_based_guardrail(ctx, agent, message, output):
    result = await Runner.run(guardrail_agent, f"Validate: {output}", context=ctx.context)
    validation = result.final_output
    
    should_block = not validation.approved or validation.contains_sensitive_data
    
    return GuardrailFunctionOutput(
        output_info={"validation": validation},
        tripwire_triggered=should_block
    )
```


__Using Multiple Guardrails Together__

```python
protected_name = Agent(
    name="Protected Agent",
    instructions="System Prompt Here"
    input_gaurdrails=[content_filter, business_hours]           # multiple input guardrails
    output_guardrails=[sensitive_data_filter, quality_control]  # multiple output guardrails
)
```
