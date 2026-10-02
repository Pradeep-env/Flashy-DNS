import argparse
import asyncio
import logging
import sys
from typing import List, Optional

from src.core.benchmark import benchmark_resolvers, test_resolver_once
from src.daemon.scheduler import DNSAutoManager

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
    print(
        f"Benchmarking {len(resolvers)} resolvers against '{domain}' ({attempts} queries each)...\n"
    )
    results = await benchmark_resolvers(resolvers, domain=domain, attempts=attempts)

    history = {res["resolver"]: [] for res in results}
    for res in results:
        if res["avg_latency"] is not None:
            history[res["resolver"]] = [res["avg_latency"]] * res["success"]

    print_summary(history, attempts)


async def run_switch_now(resolvers: List[str], domain: str) -> None:
    print(f"{CYAN}⚡ Flashy DNS: Running Immediate Resolver Evaluation...{RESET}")
    manager = DNSAutoManager(candidates=resolvers, domain=domain)
    res = await manager.evaluate_and_switch()

    status = res.get("status")
    reason = res.get("reason", "N/A")
    best = res.get("best", "Unknown")
    msg = res.get("message")

    print("-" * 45)
    if status == "switched":
        print(f"Status       : {GREEN}SWITCHED{RESET}")
        print(f"New Primary  : {GREEN}{best}{RESET}")
        print(f"Reason       : {reason}")
        if msg:
            print(f"Details      : {msg}")
    elif status == "unchanged":
        print(f"Status       : {YELLOW}UNCHANGED{RESET}")
        print(f"Current DNS  : {res.get('current')}")
        print(f"Fastest      : {best}")
        print(f"Reason       : {reason}")
    else:
        print(f"Status       : {RED}ERROR{RESET}")
        print(f"Details      : {msg or reason}")
    print("-" * 45)


async def run_daemon(resolvers: List[str], domain: str, interval: int) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    print(f"{CYAN}⚡ Flashy DNS Auto-Switch Daemon Running ⚡{RESET}")
    print(f"Check Interval : {interval} seconds")
    print(f"Target Domain  : {domain}")
    print(f"Candidates     : {', '.join(resolvers)}")
    print("Press Ctrl+C to terminate.\n")

    manager = DNSAutoManager(
        candidates=resolvers,
        interval_seconds=interval,
        domain=domain,
    )
    manager.start()

    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        manager.stop()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Flashy DNS v2 CLI Benchmark & Switcher"
    )

    parser.add_argument(
        "-r",
        "--resolvers",
        nargs="+",
        default=["1.1.1.1", "8.8.8.8", "9.9.9.9", "208.67.222.222", "94.140.14.14"],
        help="List of DNS resolver IPs",
    )
    parser.add_argument("-d", "--domain", default="example.com", help="Domain to resolve")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--live", action="store_true", help="Display an interactive live benchmark dashboard"
    )
    mode_group.add_argument(
        "--daemon",
        action="store_true",
        help="Run as a continuous foreground auto-switch daemon",
    )
    mode_group.add_argument(
        "--switch-now",
        action="store_true",
        help="Run evaluation once and switch system DNS immediately if faster",
    )

    parser.add_argument(
        "-t",
        "--attempts",
        type=int,
        default=5,
        help="Number of benchmark queries per candidate (static / live modes only)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Check interval in seconds (daemon mode only, default: 300)",
    )

    args = parser.parse_args()

    if args.interval is not None and not args.daemon:
        parser.error("--interval can only be used when running in --daemon mode.")

    interval = args.interval if args.interval is not None else 300

    try:
        if args.daemon:
            asyncio.run(run_daemon(args.resolvers, args.domain, interval))
        elif args.switch_now:
            asyncio.run(run_switch_now(args.resolvers, args.domain))
        elif args.live:
            asyncio.run(run_live(args.resolvers, args.domain, args.attempts))
        else:
            asyncio.run(run_static(args.resolvers, args.domain, args.attempts))
    except KeyboardInterrupt:
        print("\nExited.")
        sys.exit(0)