# Async in Python

## Basics

Asynchronous IO is an approach used to achieve concurrency by allowing processing to continue  

- while responses from IO operations are still being waited on  


To achieve this, IO function calls are made to be non-blocking, so that they return immediately

- before the actual IO operation is complete or has even begun  


Most, if not all, Frameworks use `async` 


Syntax uses `async/await` keywords:

- async def func()
- await func()


## Purpose of Async

Enables concurrent execution of tasks without blocking the main program thread


Useful for when a program may take a while waiting for:

- an external resource


Beneficial for:

- I/O bound operations
- network requests
- file I/O
- database queries


## Key Components

__Event Loop__

- The heart of `asyncio`

- A single-threaded loop that manages and executes asynchronous tasks


__Coroutines__

- Functions defined with `async def` that can be paused and resumed


__Concurrency vs Parallelism__

Concurrency:

- asyncio runs multiple tasks on a single thread by switching between them during wait times 


Parallelism:

- running tasks simultaneously on multiple CPU cores (not what async does)


## Key characteristics of asynchronous programming with async in Python


__Concurrency, not parallelism:__

- asyncio achieves concurrency on a single thread by efficiently switching between tasks during I/O wait times  

- It does not run multiple tasks in parallel on different CPU cores like multithreading or multiprocessing.


__Event Loop:__

- asyncio relies on an event loop, which manages and schedules the execution of coroutines.


__I/O-bound tasks:__

- Asynchronous programming is most effective for tasks that involve waiting for external operations, as it allows the program to utilize that waiting time for other tasks. 

- It's generally not suitable for CPU-bound tasks, which would still block the single event loop.
