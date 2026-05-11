import subprocess
import time
import sys
import os

def start_process(name, cmd):
    print(f"Starting {name}...")
    return subprocess.Popen([sys.executable, cmd])

def main():
    # 1. Ensure log file exists
    if not os.path.exists("app.log"):
        with open("app.log", "w") as f:
            f.write("# LogScope AI Log File Initialized\n")

    processes = []
    try:
        # Start all components
        processes.append(start_process("Dashboard", "dashboard.py"))
        time.sleep(2) # Give dashboard time to start
        
        processes.append(start_process("Log Collector", "log_collector.py"))
        processes.append(start_process("AI Worker", "worker.py"))
        
        print("\n" + "="*40)
        print("LogScope AI is now running!")
        print("Dashboard: http://localhost:5000")
        print("="*40 + "\n")
        print("Press Ctrl+C to stop everything.")

        while True:
            time.sleep(1)
            # Check if any process died
            for p in processes:
                if p.poll() is not None:
                    print(f"ERROR: A process has died. Exiting.")
                    return

    except KeyboardInterrupt:
        print("\nStopping LogScope AI...")
        for p in processes:
            p.terminate()
        print("All processes stopped.")

if __name__ == "__main__":
    main()
