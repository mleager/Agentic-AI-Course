# Asyncio Examples


## Benefits for OpenAI/LLM Frameworks


__Improved Performance:__

- Handle multiple API calls simultaneously

__Better Resource Utilization:__

- Don't waste time waiting for responses

__Scalability:__

- Handle many concurrent operations efficiently

__Responsive Applications:__

- UI doesn't freeze while waiting for LLM responses


__Functions:__

Defines a function as a coroutine

When an async func() is called it doesn't execute immediately 

- it returns a coroutine object

- `async def func_name():`


__To call the function:__

Used within an async function to pause its execution and give control back until the awaited object completes

- allows the event loop to run other tasks while the current one is waiting

- `result = await func_name()`


__Example__

```python
import asyncio

async def fetch_data():
    print("fetching data...")
    await asyncio.sleep(2)
    print("data fetched")
    return "some data"

async def main():
    data = await fetch_data()
    print(f"Received: {data}")

if __name__ == "__main__":
    asyncio.run(main())
```


## Why asyncio is Perfect for OpenAI/LLM Work

When working with OpenAI models, you'll often need to:

- Make multiple API calls

- Wait for model responses

- Handle streaming responses

- Process multiple requests concurrently


__Example with OpenAI:__

```python
import asyncio
import aiohttp

async def call_openai_api(prompt, session):
    """Simulate an OpenAI API call"""
    print(f"Starting API call for: {prompt[:30]}...")
    
    # Simulate API call delay
    await asyncio.sleep(2)
    
    print(f"Completed API call for: {prompt[:30]}...")
    return f"Response to: {prompt}"

async def process_multiple_prompts():
    prompts = [
        "Explain quantum computing",
        "Write a Python function",
        "Summarize this article",
        "Generate a creative story"
    ]
    
    # Without asyncio - would take 8 seconds (2 seconds × 4 calls)
    # With asyncio - takes ~2 seconds (all calls run concurrently)
    
    async with aiohttp.ClientSession() as session:
        tasks = [call_openai_api(prompt, session) for prompt in prompts]
        results = await asyncio.gather(*tasks)
    
    for result in results:
        print(result)

asyncio.run(process_multiple_prompts())
```


## Common AsyncIO Patterns:

__asyncio.gather()__ - Run multiple tasks together

```python
import asyncio

async def task1():
    await asyncio.sleep(1)
    return "Task 1 done"

async def task2():
    await asyncio.sleep(2)
    return "Task 2 done"

async def task2():
    await asyncio.sleep(2)
    return "Task 2 done"

async def main():
    # Both tasks run concurrently
    results = await asyncio.gather(
        task1(), 
        task2(),
        task3()
    )
   
    # ['Task 1 done', 'Task 2 done', 'Task 3 done']
    print(results)

# Finishes in 2sec instead of 6sec
asyncio.run(main())
```


__asyncio.create_task()__ - Schedule a coroutine to run

```python
import asyncio

async def background_task():
    while True:
        print("Background task running...")
        await asyncio.sleep(3)

async def main():
    # Start background task
    task = asyncio.create_task(background_task())
    
    # Do other work
    await asyncio.sleep(10)
    
    # Cancel the background task
    task.cancel()

asyncio.run(main())
```
