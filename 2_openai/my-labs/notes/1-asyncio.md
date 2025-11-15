# Asyncio

## Common Async Usage

`Create_Task`:

- Creates a "future"
- Results of an async function
- usually used with list comprehension to group tasks together

```python
tasks = [async_func(item) for item in dataset]
```


`Gather`:

- list of the completed tasks
- process all results and return them in order
- uses '*tasks'

```python
tasks = [async_func(item) for item in dataset]

gathering = await asyncio.gather(*tasks)
```


`As_Completed`:

- processes items concurrently and handle results as they complete
- loop through the tasks as they are ready, and not necessarily in order

```python
task_list = []

tasks = [async_func(item) for item in dataset]

for task in asyncio.as_completed(tasks):
  item = await task
  task_list.append(task)
```


## Rate Limiting with Semaphore

Semaphore is a `Rate-Limiter`

- set the number of concurrent tasks at a time
- Semaphore has an internal counter to limit number of tasks

```python
async def worker(name: str, semaphore: asyncio.Semaphore):

  async with semaphore:
    return await do_task(name)


# Using Gather
async def rate_limited_gather(concurrentcy_limit: int = 3):

  semaphore = asyncio.Semaphore(concurrentcy_limit)

  tasks = [worker(name, semaphore) for name in dataset]

  results = await asyncio.gather(*tasks)


# Using As_Completed
async def rate_limited_as_completed(concurrentcy_limit: int = 3):

  task_list = []

  semaphore = asyncio.Semaphore(concurrentcy_limit)

  tasks = [worker(text, semaphore) for text in dataset]

  for task in asyncio.as_completed(tasks):
    result = await task
    task_list.append(result)
```


## Gather vs As_Completed

`Gather`: 

- Execute multiple awaitables (coroutines or tasks) concurrently  
  and waits for all of them to complete

- Returns a list of results in the same order as the input 

- Raised by first Exception by default

- Use when you need all results to be available before continuing,
  and the order of results is important 


`As_Completed`:

- Returns an iterator that yields completed awaitables as they finish,  
  regardless of their input order

- Allows you to process results as soon as each task completed,  
  without waiting for all tasks. 

- The order of results is determined by their order of completion

- Allows for processing individual results and Exceptions as they occur

- Use when you want to process results as they become available,  
  or when some tasks might take much longer than others and you  
  don't want to block on the slowest one


## When to Use Them


__asyncio.gather__:

- You need results in the same order as input
- All tasks must complete successfully
- You want the fastest possible execution
- Memory usage isn't a concern

__asyncio.as_completed__:

- You want to process results as they arrive
- Order doesn't matter
- You're streaming data to clients
- You want to handle large datasets efficiently

__asyncio.Semaphore / rate limiting__:

- Working with API rate limits
- Being respectful to external services
- Managing resource consumption
- Building production applications

