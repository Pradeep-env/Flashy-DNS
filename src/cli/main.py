import argparse
import asyncio
import sys
from typing import List, Optional

from src.core.benchmark import benchmark_resolvers, test_resolver_once

GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RED = "\033[31m"
RESET = "\033[0m"


def format_latency(lat: Optional[float]) -> str:
    if lat is None:
        return f"{RED}FAIL{RESET}"
    if lat < 30:
        return f"{GREEN}{lat:6.2f} ms{RESET}"
    if lat < 100:
        return f"{YELLOW}{lat:6.2f} ms{RESET}"
    return f"{RED}{lat:6.2f} ms{RESET}"


def clear_block(lines: int) -> None:
    print(f"\033[{lines}F", end="")
    for _ in range(lines):
        print("\033[2K")
    print(f"\033[{lines}F", end="")


async def run_live(resolvers: List[str], domain: str, attempts: int) -> None:
    history = {r: [] for r in resolvers}
    results_store = {r: None for r in resolvers}
    lines_needed = 4 + len(resolvers)
    done = False

    print("\n" * lines_needed)

    async def worker():
        nonlocal done
        for attempt in range(1, attempts + 1):
            tasks = [test_resolver_once(r, domain=domain) for r in resolvers]
            results = await asyncio.gather(*tasks)

            for res in results:
                r = res["resolver"]
                results_store[r] = (res["latency"], res["success"], attempt)
                if res["success"] and res["latency"] is not None:
                    history[r].append(res["latency"])

            await asyncio.sleep(0.05)
        done = True

    async def ui():
        while not done:
            clear_block(lines_needed)
            cur_attempt = next(
                (v[2] for v in results_store.values() if v is not None), 0
            )

            print(f"{CYAN}Flashy DNS Live Benchmark{RESET}")
            print(f"Target Domain : {domain}")
            print(f"Progress      : Attempt {cur_attempt}/{attempts}\n")

            for r in resolvers:
                data = results_store[r]
                if data is None:
                    print(f"{r:<16} waiting...")
                    continue
                lat, success, _ = data
                status = f"{GREEN}OK ✓{RESET}" if success else f"{RED}ERR ✗{RESET}"
                print(f"{r:<16} latency: {format_latency(lat)}   [{status}]")

            await asyncio.sleep(0.1)

    await asyncio.gather(worker(), ui())
    print_summary(history, attempts)


def print_summary(history: dict, total_attempts: int) -> None:
    print(f"\n{CYAN}Final Summary{RESET}")
    print("-" * 42)
    print(f"{'Resolver':<16} {'Avg Latency':<16} {'Reliability':<10}")
    print("-" * 42)

    sorted_results = []
    for r, lats in history.items():
        avg = round(sum(lats) / len(lats), 2) if lats else None
        rate = round((len(lats) / total_attempts) * 100, 1)
        sorted_results.append((r, avg, rate))

    sorted_results.sort(key=lambda x: (x[1] is None, x[1]))

    for r, avg, rate in sorted_results:
        rate_str = f"{rate}%"
        print(f"{r:<16} {format_latency(avg):<25} {rate_str:<10}")
    print("-" * 42)


async def run_static(resolvers: List[str], domain: str, attempts: int) -> None:
    print(f"Benchmarking {len(resolvers)} resolvers against '{domain}' ({attempts} queries each)...\n")
    results = await benchmark_resolvers(resolvers, domain=domain, attempts=attempts)

    history = {res["resolver"]: [] for res in results}
    for res in results:
        if res["avg_latency"] is not None:
            history[res["resolver"]] = [res["avg_latency"]] * res["success"]

    print_summary(history, attempts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Flashy DNS v2 CLI Benchmark")
    parser.add_argument(
        "-r",
        "--resolvers",
        nargs="+",
        default=["1.1.1.1", "8.8.8.8", "9.9.9.9", "208.67.222.222"],
        help="List of DNS resolver IPs",
    )
    parser.add_argument("-d", "--domain", default="example.com", help="Domain to resolve")
    parser.add_argument(
        "-t", "--attempts", type=int, default=5, help="Number of benchmark queries"
    )
    parser.add_argument(
        "--live", action="store_true", help="Display an interactive live dashboard"
    )

    args = parser.parse_args()

    try:
        if args.live:
            asyncio.run(run_live(args.resolvers, args.domain, args.attempts))
        else:
            asyncio.run(run_static(args.resolvers, args.domain, args.attempts))
    except KeyboardInterrupt:
        print("\nBenchmark cancelled by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
