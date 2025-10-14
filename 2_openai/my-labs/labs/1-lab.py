from dotenv import load_dotenv
from agents import Agent, Runner, trace
import asyncio

load_dotenv(override=True)

OPENAI_MODEL = "gpt-4o-mini"

agent = Agent(
    name="Demo Agent",
    instructions="You are a coding assistant proficient in Go.",
    model=OPENAI_MODEL,
)

print(f"Agent Object:\n{agent}")


async def main():
    with trace("demo agent run"):
        result = await Runner.run(
            starting_agent=agent,
            input="Create a Go file in this directory that has examples of using concurrency.",
        )

    print(f"Agent's Response:\n{result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
