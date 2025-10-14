from dotenv import load_dotenv
from agents import Agent, Runner, trace
import asyncio

load_dotenv(override=True)

OPENAI_MODEL = "gpt-4o-mini"

# Agent 1: Go Code Generator
code_generator = Agent(
    name="Go Code Generator",
    instructions="""You are a Go programming expert. Your job is to create well-structured Go programs.
    When asked to create a Go program, write clean, idiomatic Go code with proper error handling.
    Always include package declaration, imports, and a main function.
    Add comments to explain the code functionality as needed.""",
    model=OPENAI_MODEL,
)

# Agent 2: Go Compiler
compiler_agent = Agent(
    name="Go Compiler",
    instructions="""You are a Go compilation specialist. Your job is to compile Go programs.
    When given a Go file path, use 'go build' command to compile it.
    Check for compilation errors and provide clear feedback.
    If compilation succeeds, mention the output binary name.""",
    model=OPENAI_MODEL,
)

# Agent 3: Go Program Runner
runner_agent = Agent(
    name="Go Program Runner",
    instructions="""You are a Go program execution specialist. Your job is to run compiled Go programs.
    Execute the compiled binary and capture the output.
    Report both successful execution results and any runtime errors.
    Provide clear feedback about the program's behavior.""",
    model=OPENAI_MODEL,
)

async def main():
    program_topic = "a simple HTTP server in Go that responds to GET requests on Port 8080"

    # Generate Go code
    with trace("code generation"):
        code_result = await Runner.run(
            code_generator, 
            f"Create a Go program that implements {program_topic}. Save as main.go in the current directory"
        )
        print(f"Generated Go code:\n{code_result.final_output}\n")

    # Compile the generated Go code
    with trace("compilation"):
        compiler_result = await Runner.run(
            compiler_agent, 
            "Compile the generated Go code in the current directory using the 'go build main.go' command"
        )
        print(f"Compiler Response:\n{compiler_result.final_output}\n")

    # Run the compiled binary
    with trace("program execution"):
        runner_result = await Runner.run(
            runner_agent, 
            """Run the compiled binary using the './main' command. 
            Test it with a simple request to the designated port. 
            Please provide instructions on how to test it manually."""
        )
        print(f"Program execution response:\n{runner_result.final_output}\n")

if __name__ == "__main__":
    asyncio.run(main())
