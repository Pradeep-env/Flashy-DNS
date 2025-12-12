from backend.benchmark import run_dns_test
from concurrent.futures import ThreadPoolExecutor
import asyncio

executor = ThreadPoolExecutor(max_workers=20)

async def quick_dns(resolver, domain):
    loop = asyncio.get_event_loop()
    # run 3 attempts to smooth the latency
    result = await loop.run_in_executor(executor, run_dns_test, resolver, domain, 3)
    return result
