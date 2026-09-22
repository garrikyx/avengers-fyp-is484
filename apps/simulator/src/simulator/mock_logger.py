import os
import time
import random
import argparse
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("./logs")
DEFAULT_MAX_BYTES = 5 * 1024 # 5 KB limit for rapid testing
DEFAULT_INTERVAL = 0.2 # Writes every 200ms
DEFAULT_KEEP_ROTATED_FILES = 5

SYMBOLS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "FB", "NFLX", "NVDA", "INTC", "AMD"]

def get_timestamps() -> tuple[str, str]:
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def rotate_if_needed(
    file_path: Path,
    max_bytes: int,
    keep_rotated_files: int = DEFAULT_KEEP_ROTATED_FILES,
) -> bool:
    """Rotate with numbered retained archives, like ``logrotate``.

    ``Application.log.1`` is the newest archive and
    ``Application.log.<keep_rotated_files>`` is the oldest.  Keeping several
    generations gives a stopped log collector time to restart and backfill the
    files it missed.
    """
    if keep_rotated_files < 1:
        raise ValueError("keep_rotated_files must be at least 1")

    if file_path.exists() and file_path.stat().st_size >= max_bytes:
        oldest_path = file_path.with_name(f"{file_path.name}.{keep_rotated_files}")
        if oldest_path.exists():
            oldest_path.unlink()

        # Rename in descending order so no retained generation is overwritten.
        for index in range(keep_rotated_files - 1, 0, -1):
            source = file_path.with_name(f"{file_path.name}.{index}")
            destination = file_path.with_name(f"{file_path.name}.{index + 1}")
            if source.exists():
                source.replace(destination)

        rotated_path = file_path.with_name(f"{file_path.name}.1")
        file_path.replace(rotated_path)
        print(
            f"Rotated log file: {file_path} -> {rotated_path} "
            f"(retaining {keep_rotated_files} archives)"
        )
        return True
    return False

def run_harness(
    max_bytes: int,
    interval: float,
    keep_rotated_files: int = DEFAULT_KEEP_ROTATED_FILES,
) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    log_files = {
        "Application": LOG_DIR / "Application.log",
        "Fix": LOG_DIR / "Fix.log",
    }

    print(f"=== Synthetic Log Generator active ===")
    print(f"Target: {LOG_DIR.resolve()} | Max Size: {max_bytes} bytes | Speed: {interval}s\n")
        
    seq = 1000
    while True:
        seq += 1
        category = random.choice(list(log_files.keys()))
        file_path = log_files[category]

        rotate_if_needed(file_path, max_bytes, keep_rotated_files)

        iso_ts, fix_ts = get_timestamps()

        symbol = random.choice(SYMBOLS)

        if category == "Application":
            line = f"{iso_ts} [INFO] [CoreEngine] Heartbeat active. Connected session count: {random.randint(1, 20)}"
        elif category == "Fix":
            line = f"{fix_ts} : 8=FIX.4.2|9=140|35=8|49=MAGIC|56=CLIENT|11=ORD{seq}|55={symbol}|54=1|38=100|44=150.50|10=112|"

        with open(file_path, "a") as f:
            f.write(f"{line}\n")
            f.flush()

        print(f"[Write] [{category}] -> {file_path.name}")
        time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL)
    parser.add_argument(
        "--keep-rotated-files",
        type=int,
        default=DEFAULT_KEEP_ROTATED_FILES,
        help="Number of rotated archives to retain per log file",
    )
    args = parser.parse_args()

    try:
        run_harness(
            args.max_bytes,
            args.interval,
            keep_rotated_files=args.keep_rotated_files,
        )
    except KeyboardInterrupt:
        print("\n[LOGGER] Stopped.")
