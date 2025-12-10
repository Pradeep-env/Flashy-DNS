import argparse
import time
from benchmark import run_dns_test

def clear_block(lines):
    """Move cursor up N lines and clear them."""
    print(f"\033[{lines}F", end="")   # Move cursor N lines up
    for _ in range(lines):
        print("\033[2K")             # Clear entire line
    print(f"\033[{lines}F", end="")   # Move up again into cleared block


def main():
    parser = argparse.ArgumentParser(description="Flashy DNS CLI Benchmark ⚡")
    parser.add_argument("-r", "--resolver", required=True)
    parser.add_argument("-d", "--domain", default="example.com")
    parser.add_argument("-t", "--attempts", type=int, default=30)
    args = parser.parse_args()

    # Number of lines we will always redraw
    LINES = 7

    print("\n" * LINES)   # Reserve vertical space once

    for i in range(1, args.attempts + 1):
        result = run_dns_test(args.resolver, args.domain, attempts=1)

        clear_block(LINES)

        print("⚡ Flashy DNS Live Benchmark ⚡")
        print(f"Resolver      : {args.resolver}")
        print(f"Domain        : {args.domain}")
        print(f"Attempt       : {i}/{args.attempts}")
        print("")
        print(f"Latency (ms)  : {result['avg_latency']}")
        print(f"Status        : {'OK ✓' if result['failures']==0 else 'FAIL ✗'}")

        time.sleep(0.5)

    print("\nBenchmark complete ✔️")


if __name__ == "__main__":
    main()
