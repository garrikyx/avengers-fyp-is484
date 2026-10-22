import argparse
import sys

from simulator.mock_logger import (
    DEFAULT_INTERVAL,
    DEFAULT_KEEP_ROTATED_FILES,
    DEFAULT_MAX_BYTES,
    DEFAULT_REJECT_RATE,
    run_harness,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Magic Application Synthetic Log & Rotation Generator"
    )
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
    parser.add_argument(
        "--reject-rate",
        type=float,
        default=DEFAULT_REJECT_RATE,
        help="Share of FIX orders that Magic rejects (0 to 1)",
    )
    parser.add_argument(
        "--keep-rotated-files",
        type=int,
        default=DEFAULT_KEEP_ROTATED_FILES,
        help="Number of rotated archives to retain per log file",
    )

    args = parser.parse_args()

    try:
        run_harness(
            max_bytes=args.max_bytes,
            interval=args.interval,
            keep_rotated_files=args.keep_rotated_files,
            reject_rate=args.reject_rate,
        )
    except KeyboardInterrupt:
        print("\n[MAGIC SIMULATOR] Stopped by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
