"""Development CLI for streaming the simulator's two log files."""

import argparse
from pathlib import Path

from telemetry_agent.logs.multi_log_monitor import MultiLogMonitor

LOG_DIR = Path("./logs")
REGISTRY_FILE = Path("offsets.json")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stream the synthetic Magic log files."
    )
    parser.add_argument("--mode", choices=("tail", "interval"), default="tail")
    parser.add_argument("--poll-interval", type=float, default=0.1)
    parser.add_argument("--checkpoint-interval", type=float, default=5.0)
    parser.add_argument("--rotation-drain-timeout", type=float, default=5.0)
    args = parser.parse_args()

    target_files = [LOG_DIR / "Application.log", LOG_DIR / "Fix.log"]
    print("=== Starting Real-Time MultiLogMonitor Streamer ===")
    print(f"Monitoring: {[file.name for file in target_files]}")
    print(f"Persisting offsets to: {REGISTRY_FILE.resolve()}\n")

    monitor = MultiLogMonitor(
        log_paths=target_files,
        registry_path=REGISTRY_FILE,
        read_mode=args.mode,
        checkpoint_interval=args.checkpoint_interval,
        rotation_drain_timeout=args.rotation_drain_timeout,
    )

    try:
        for source_file, line in monitor.stream_lines(
            poll_interval=args.poll_interval
        ):
            print(f"[{source_file}] {line}")
    except KeyboardInterrupt:
        print("\n[STREAMER] Shutting down cleanly and persisting offsets...")
    finally:
        monitor.close()


if __name__ == "__main__":
    main()
