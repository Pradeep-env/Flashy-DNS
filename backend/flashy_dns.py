# flashy_dns.py
import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
from benchmark import run_dns_test

# Color codes
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESET = "\033[0m"

def color_latency(lat):
    if lat is None:
        return RED + "N/A" + RESET
    if lat < 30:
        return GREEN + f"{lat} ms" + RESET
    if lat < 100:
        return YELLOW + f"{lat} ms" + RESET
    return RED + f"{lat} ms" + RESET


def clear_block(lines):
    print(f"\033[{lines}F", end="")
    for _ in range(lines):
        print("\033[2K")
    print(f"\033[{lines}F", end="")


async def run_resolver_async(executor, resolver, domain):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(executor, run_dns_test, resolver, domain, 1)
    return result

async def benchmark_live(resolvers, domain, attempts):
    executor = ThreadPoolExecutor(max_workers=len(resolvers))

    # Shared state
    results_store = {r: None for r in resolvers}
    history = {r: [] for r in resolvers}
    done = False

    lines_needed = 4 + len(resolvers)
    print("\n" * lines_needed)

    async def dns_worker():
        nonlocal done
        for attempt in range(1, attempts + 1):
            tasks = [run_resolver_async(executor, r, domain) for r in resolvers]
            results = await asyncio.gather(*tasks)

            for result in results:
                r = result["resolver"]
                latency = result["avg_latency"]
                failures = result["failures"]

                results_store[r] = (latency, failures, attempt)

                if failures == 0 and latency is not None:
                    history[r].append(latency)

        done = True

    async def ui_worker():
        while not done:
            clear_block(lines_needed)

            # Determine current attempt (infer from any resolver)
            attempts_done = next(
                (v[2] for v in results_store.values() if v is not None),
                0
            )

            print("⚡ Flashy DNS Live Benchmark ⚡")
            print(f"Domain    : {domain}")
            print(f"Attempt   : {attempts_done}/{attempts}\n")

            for r, data in results_store.items():
                if data is None:
                    print(f"{r:<12} waiting...")
                    continue

                latency, failures, _ = data
                status = "OK ✓" if failures == 0 else "FAIL ✗"
                print(f"{r:<12} latency: {color_latency(latency)}   {status}")

            await asyncio.sleep(0.1)  # UI tick interval

    # Run DNS worker and UI worker in parallel
    await asyncio.gather(dns_worker(), ui_worker())

    # Final summary
    print("\nBenchmark complete ✔️\n")
    print("📊 Final Summary")
    print("-----------------------------")

    for r, lat_list in history.items():
        if lat_list:
            avg_total = round(sum(lat_list) / len(lat_list), 2)
            print(f"{r:<12} avg latency: {color_latency(avg_total)}")
        else:
            print(f"{r:<12} no successful queries")



async def benchmark_once(resolvers, domain, attempts):
    executor = ThreadPoolExecutor(max_workers=len(resolvers))

    history = {r: [] for r in resolvers}

    print("Running Flashy DNS Benchmark...\n")
    for attempt in range(1, attempts + 1):
        tasks = [run_resolver_async(executor, r, domain) for r in resolvers]
        results = await asyncio.gather(*tasks)

        for result in results:
            r = result["resolver"]
            lat = result["avg_latency"]
            if lat:
                history[r].append(lat)

    print("📊 Final Summary")
    print("-----------------------------")
    for r, lat_list in history.items():
        if lat_list:
            avg_total = round(sum(lat_list) / len(lat_list), 2)
            print(f"{r:<12} avg latency: {color_latency(avg_total)}")
        else:
            print(f"{r:<12} no successful queries")


def main():
    print()
    print()
    print('''             ........  ...          ...     ...........  ...     ...  ...    ...       .....       ...      ...   ...........
             ........  ...         .. ..    ...........  ...     ...   ...   ...       ...  ..     ....     ...   ...........
             ...       ...        ..   ..   ...          ...     ...    ...  ...       ...   ..    .....    ...   ...
             ........  ...       ..     ..    ...        ...........     ... ...       ...    ..   ...  ..  ...     ...
             ........  ...       .........      ...      ...........      ......       ...    ..   ...   .. ...       ...
             ...       ...       ..     ..        ...    ...     ...        ....       ...   ..    ...    .....         ...
             ...       ........  ..     ..  ...........  ...     ...        ....       ...  ..     ...     ....    ..........
             ...       ........  ..     ..  ...........  ...     ...        ....       .....       ...      ...    ..........

    ''')
    print("----------------------------------------------------------⚡-------------------------------------------------------------------\n")
    parser = argparse.ArgumentParser(description="Flashy DNS CLI Benchmark ⚡")
    parser.add_argument("-r", "--resolvers", nargs="+", required=True)
    parser.add_argument("-d", "--domain", default="example.com")
    parser.add_argument("-t", "--attempts", type=int, default=5)
    parser.add_argument("--live", action="store_true", help="Enable live dashboard mode")

    args = parser.parse_args()

    if args.live:
        asyncio.run(benchmark_live(args.resolvers, args.domain, args.attempts))
    else:
        asyncio.run(benchmark_once(args.resolvers, args.domain, args.attempts))


if __name__ == "__main__":
    main()
