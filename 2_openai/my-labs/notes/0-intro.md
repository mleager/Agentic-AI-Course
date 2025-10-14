# AsyncIO Intro

AsyncIO provides a lightweight alternative to 

    - threading or multiprocessing


Functions defined with async def are called [coroutines]

    - they're special functions that can be pasued and resumed


Calling a coroutine doesn't execute it immediately

    - it returns a coroutine object


To actually run a coroutine, you must use `await`

    - which schedules it for execution within an event loop


While a couroutine is waiting, the event loop can run other coroutines
