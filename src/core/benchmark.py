import asyncio
import time
from typing import Any, Dict, List, Optional
import dns.asyncresolver


async def test_resolver_once(
    resolver_ip: str, domain: str = "example.com", lifetime: float = 2.0
) -> Dict[str, Any]:
    resolver = dns.asyncresolver.Resolver(configure=False)
    resolver.nameservers = [resolver_ip]
    resolver.lifetime = lifetime

    start = time.perf_counter()
    try:
        await resolver.resolve(domain, "A")
        latency = (time.perf_counter() - start) * 1000
        return {
            "resolver": resolver_ip,
            "latency": round(latency, 2),
            "success": True,
            "error": None,
        }
    except Exception as exc:
        return {
            "resolver": resolver_ip,
            "latency": None,
            "success": False,
            "error": type(exc).__name__,
        }


async def test_resolver(
    resolver_ip: str,
    domain: str = "example.com",
    attempts: int = 3,
    lifetime: float = 2.0,
) -> Dict[str, Any]:
    latencies: List[float] = []
    failures = 0
    last_error: Optional[str] = None

    for _ in range(attempts):
        result = await test_resolver_once(resolver_ip, domain, lifetime)
        if result["success"] and result["latency"] is not None:
            latencies.append(result["latency"])
        else:
            failures += 1
            last_error = result["error"]

    success_count = attempts - failures
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else None

    return {
        "resolver": resolver_ip,
        "avg_latency": avg_latency,
        "min_latency": min(latencies) if latencies else None,
        "max_latency": max(latencies) if latencies else None,
        "attempts": attempts,
        "success": success_count,
        "failures": failures,
        "success_rate": round((success_count / attempts) * 100, 2),
        "last_error": last_error,
    }


async def benchmark_resolvers(
    resolvers: List[str],
    domain: str = "example.com",
    attempts: int = 3,
    lifetime: float = 2.0,
) -> List[Dict[str, Any]]:
    tasks = [
        test_resolver(r, domain=domain, attempts=attempts, lifetime=lifetime)
        for r in resolvers
    ]
    return await asyncio.gather(*tasks)
