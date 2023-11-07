import asyncio

async def coroutine1(lock):
    print("Coroutine 1 acquiring lock")
    await lock.acquire()
    try:
        print("Coroutine 1 has acquired the lock")
        await asyncio.sleep(5)
    finally:
        print("Coroutine 1 releasing lock")
        lock.release()

async def coroutine2(lock):
    print("Coroutine 2 acquiring lock")
    await lock.acquire()
    try:
        print("Coroutine 2 has acquired the lock")
        await asyncio.sleep(10)
    finally:
        print("Coroutine 2 releasing lock")
        lock.release()

loop = asyncio.get_event_loop()
lock = asyncio.Lock()

tasks = [coroutine1(lock), coroutine2(lock)]
loop.run_until_complete(asyncio.wait(tasks))