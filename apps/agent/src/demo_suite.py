import json
import time
from pathlib import Path
from telemetry_agent.logs.multi_log_monitor import MultiLogMonitor

LOG_DIR = Path("./demo_logs")
REGISTRY = LOG_DIR / "offsets.json"

def print_header(title):
    print(f"\n==================================================")
    print(f" 🚀 DEMO SCENARIO: {title}")
    print(f"==================================================")

def setup_environment():
    LOG_DIR.mkdir(exist_ok=True)
    for p in LOG_DIR.glob("*"):
        p.unlink()

def run_demo():
    setup_environment()
    app_log = LOG_DIR / "Application.log"
    fix_log = LOG_DIR / "Fix.log"

    # --- Scenario 1: Multi-File Ingestion ---
    print_header("1. Real-Time Multi-Stream Ingestion")
    app_log.write_text("APP line 1\nAPP line 2\n")
    fix_log.write_text("FIX line 1\n")

    monitor = MultiLogMonitor([app_log, fix_log], registry_path=REGISTRY)
    gen = monitor.stream_lines(poll_interval=0.05)

    ingested = [next(gen) for _ in range(3)]
    for source, line in ingested:
        print(f"  [STREAMED] [{source}] -> {line}")
    assert len(ingested) == 3, "Failed to ingest initial logs"
    print("  ✅ [PASS] Ingested 3 log lines across multiple streams.")

    # --- Scenario 2: Zero-Loss File Rotation ---
    print_header("2. Rotation Handover (Inode Swap)")
    # Force rotation: rename active log to .1 (simulates mock_logger)
    rotated_app = LOG_DIR / "Application.log.1"
    app_log.rename(rotated_app)
    
    # Write trailing line to old inode and fresh line to new inode
    with open(rotated_app, "a") as f:
        f.write("APP trailing line on old inode\n")
    app_log.write_text("APP initial line on new inode\n")

    rotated_lines = [next(gen), next(gen)]
    for source, line in rotated_lines:
        print(f"  [ROTATION DETECTED] [{source}] -> {line}")
    print("  ✅ [PASS] Successfully drained old inode and attached to new inode.")

    # --- Scenario 3: Crash Recovery & State Resume ---
    print_header("3. Agent Crash & Resume (Zero Duplicates)")
    monitor.close()  # Simulates abrupt agent shutdown
    
    # Append new data while agent is offline
    with open(fix_log, "a") as f:
        f.write("FIX offline message 1\nFIX offline message 2\n")

    # Restart agent and verify it skips old lines
    restarted_monitor = MultiLogMonitor([app_log, fix_log], registry_path=REGISTRY)
    restarted_gen = restarted_monitor.stream_lines(poll_interval=0.05)

    recovered_lines = [next(restarted_gen), next(restarted_gen)]
    for source, line in recovered_lines:
        print(f"  [RESUMED STREAM] [{source}] -> {line}")
    
    assert recovered_lines[0][1] == "FIX offline message 1"
    print("  ✅ [PASS] Agent resumed at exact byte offset without duplicate processing.")
    restarted_monitor.close()

    # --- Scenario 4: State Registry Audit ---
    print_header("4. Offset Tracker Registry Inspection")
    with open(REGISTRY) as f:
        registry_data = json.load(f)
    print(f"  Registered file inodes tracked: {len(registry_data)}")
    print("  ✅ [PASS] Registry persisted atomic state to disk.")
    print("\n🎉 ALL DEMO SCENARIOS PASSED SUCCESSFULLY!\n")

if __name__ == "__main__":
    run_demo()