# flashy_dns.py
import argparse
import time
from benchmark import run_dns_test

def clear_block(lines):
    print(f"\033[{lines}F", end="")
    for _ in range(lines):
        print("\033[2K")
    print(f"\033[{lines}F", end="")


def main():
    parser = argparse.ArgumentParser(description="Flashy DNS CLI Benchmark ⚡")
    parser.add_argument("-r", "--resolvers", nargs="+", required=True,
                        help="List of DNS resolvers")
    parser.add_argument("-d", "--domain", default="example.com")
    parser.add_argument("-t", "--attempts", type=int, default=5)

    args = parser.parse_args()

    num_resolvers = len(args.resolvers)
    lines_needed = 4 + num_resolvers  # dynamic block size

    # Reserve the display area
    print("\n" * lines_needed)

    # Store stats
    history = {r: [] for r in args.resolvers}

    for attempt in range(1, args.attempts + 1):

        clear_block(lines_needed)

        print("⚡ Flashy DNS Live Benchmark ⚡")
        print(f"Domain      : {args.domain}")
        print(f"Attempt     : {attempt}/{args.attempts}\n")

        # Run all resolvers in this loop
        for resolver in args.resolvers:
            result = run_dns_test(resolver, args.domain, attempts=1)

            if result["avg_latency"] is not None:
                history[resolver].append(result["avg_latency"])

            status = "OK ✓" if result["failures"] == 0 else "FAIL ✗"

            latest = result["avg_latency"]
            print(f"{resolver:<12} latency: {latest} ms   {status}")

        time.sleep(0.5)

    print("\nBenchmark complete ✔️\n")

    # SUMMARY
    print("📊 Final Summary")
    print("-----------------------------")
    for resolver, latencies in history.items():
        if latencies:
            avg_total = round(sum(latencies) / len(latencies), 2)
            print(f"{resolver:<12} avg latency: {avg_total} ms")
        else:
            print(f"{resolver:<12} no successful queries")


if __name__ == "__main__":
    main()
