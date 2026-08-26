import argparse
import sys
from mock_logger import DEFAULT_INTERVAL, DEFAULT_MAX_BYTES, run_harness

def main() -> None:
    parser = argparse.ArgumentParser(description="Magic Application Synthetic Log & Rotation Generator")
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=DEFAULT_MAX_BYTES,
        help="Max file size before rotation in bytes",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_INTERVAL,
        help="Delay between log writes in seconds",
    )

    args = parser.parse_args()

    try:
        run_harness(max_bytes=args.max_bytes, interval=args.interval)
    except KeyboardInterrupt:
        print("\n[MAGIC SIMULATOR] Stopped by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()