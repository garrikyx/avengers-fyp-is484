import sys
from pathlib import Path
from telemetry_agent.logs.multi_log_monitor import MultiLogMonitor

LOG_DIR = Path("./logs")
REGISTRY_FILE = Path("offsets.json")

def main():
    # Define targets to match mock_logger.py output files
    target_files = [
        LOG_DIR / "Application.log",
        LOG_DIR / "Fix.log",
    ]

    print("=== Starting Real-Time MultiLogMonitor Streamer ===")
    print(f"Monitoring: {[f.name for f in target_files]}")
    print(f"Persisting offsets to: {REGISTRY_FILE.resolve()}\n")

    monitor = MultiLogMonitor(log_paths=target_files, registry_path=REGISTRY_FILE)

    try:
        # Stream lines continuously from all files in round-robin order
        for source_file, line in monitor.stream_lines(poll_interval=0.1):
            print(f"[{source_file}] {line}")

    except KeyboardInterrupt:
        print("\n[STREAMER] Shutting down cleanly and persisting offsets...")
        monitor.close()
        sys.exit(0)

if __name__ == "__main__":
    main()