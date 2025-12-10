# benchmark.py
import time
import dns.resolver

def run_dns_test(resolver_ip, domain="example.com", attempts=1):
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [resolver_ip]
    
    latencies = []
    failures = 0

    for _ in range(attempts):
        start = time.perf_counter()
        try:
            resolver.resolve(domain, "A", lifetime=2)
            latencies.append((time.perf_counter() - start) * 1000)
        except Exception:
            failures += 1

    return {
        "resolver": resolver_ip,
        "avg_latency": round(sum(latencies)/len(latencies), 2) if latencies else None,
        "failures": failures,
        "success": attempts - failures
    }
