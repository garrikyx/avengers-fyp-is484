import os
import time
import random
import argparse
from datetime import datetime
from pathlib import Path

LOG_DIR = Path("./logs")
DEFAULT_MAX_BYTES = 5 * 1024 # 5 KB limit for rapid testing
DEFAULT_INTERVAL = 0.2 # Writes every 200ms

SYMBOLS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "FB", "NFLX", "NVDA", "INTC", "AMD"]
REJECT_REASONS = ["PriceExceedsLimit", "UnknownSymbol", "RiskLimitExceeded"]

def get_timestamps():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3], now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def rotate_if_needed(file_path: Path, max_bytes: int):
    if file_path.exists() and file_path.stat().st_size >= max_bytes:
        rotated_path = file_path.with_name(f"{file_path.name}.1")
        if rotated_path.exists():
            os.remove(rotated_path)
        os.rename(file_path, rotated_path)
        print(f"Rotated log file: {file_path} -> {rotated_path}")

def run_harness(max_bytes:int, interval:float):
    LOG_DIR.mkdir(exist_ok=True)
    log_files = {
        "Application": LOG_DIR / "Application.log",
        "Fix": LOG_DIR / "Fix.log",
        "Order": LOG_DIR / "Order.log",
        "Execution": LOG_DIR / "Execution.log",
    }

    print(f"=== Synthetic Log Generator active ===")
    print(f"Target: {LOG_DIR.resolve()} | Max Size: {max_bytes} bytes | Speed: {interval}s\n")
        
    seq = 1000
    while True:
        seq += 1
        category = random.choice(list(log_files.keys()))
        file_path = log_files[category]

        rotate_if_needed(file_path, max_bytes)

        iso_ts, fix_ts = get_timestamps()

        symbol = random.choice(SYMBOLS)

        if category == "Application":
            line = f"{iso_ts} [INFO] [CoreEngine] Heartbeat active. Connected session count: {random.randint(1, 20)}"
        elif category == "Fix":
            line = f"{fix_ts} : 8=FIX.4.2|9=140|35=8|49=MAGIC|56=CLIENT|11=ORD{seq}|55={symbol}|54=1|38=100|44=150.50|10=112|"
        elif category == "Order":
            line = f"{iso_ts} [ORDER_MGMT] NEW_ORDER | ID: ORD{seq} | Symbol: {symbol} | Side: BUY | Qty: 100 | Price: 150.50"
        elif category == "Execution":
            line = f"{iso_ts} [EXEC_ENGINE] FULL_FILL | ExecID: EX{seq} | OrderID: ORD{seq} | Symbol: {symbol} | Qty: 100"

        with open(file_path, "a") as f:
            f.write(f"{line}\n")
            f.flush()

        print(f"[Write] [{category}] -> {file_path.name}")
        time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL)
    args = parser.parse_args()
    
    try:
        run_harness(args.max_bytes, args.interval)
    except KeyboardInterrupt:
        print("\n[LOGGER] Stopped.")
    