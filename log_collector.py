import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from supabase import create_client, Client
from dotenv import load_dotenv
from log_parser import LogParser, ParsedLog

load_dotenv()

# Setup Supabase
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
parser = LogParser()

# Configuration: Which file to watch?
LOG_FILE_TO_WATCH = "sample.log"

class LogFileHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_position = 0
        # If file exists, start at the end so we don't read old history
        if os.path.exists(LOG_FILE_TO_WATCH):
            self.last_position = os.path.getsize(LOG_FILE_TO_WATCH)

    def on_modified(self, event):
        if event.src_path.endswith(LOG_FILE_TO_WATCH):
            self.read_new_lines()

    def read_new_lines(self):
        try:
            with open(LOG_FILE_TO_WATCH, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(self.last_position)
                new_lines = f.readlines()
                self.last_position = f.tell()

                for line in new_lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 1. Parse the raw text using our new parser
                    parsed = parser.parse(line)
                    
                    # 2. Determine if it's a basic anomaly (ERROR or CRITICAL)
                    is_anomaly = parsed.level in ['ERROR', 'CRITICAL']
                    
                    # 3. Save to Supabase
                    try:
                        supabase.table("logs").insert({
                            "timestamp": parsed.timestamp.isoformat(),
                            "log_level": parsed.level,
                            "message": parsed.message,
                            "source": parsed.source,
                            "is_anomaly": is_anomaly,
                            "structured_data": parsed.extra_data
                        }).execute()
                        
                        status = "ANOMALY" if is_anomaly else "Normal"
                        print(f"[{status}] [{parsed.level}] [{parsed.source}] {parsed.message[:80]}")
                    except Exception as e:
                        print(f"DB Error: {e}")

        except Exception as e:
            print(f"File read error: {e}")

if __name__ == "__main__":
    # Create the sample log file if it doesn't exist
    if not os.path.exists(LOG_FILE_TO_WATCH):
        with open(LOG_FILE_TO_WATCH, 'w') as f:
            pass # Create empty file

    print(f"Starting real-time watcher for: {LOG_FILE_TO_WATCH}")
    print("Open another terminal and run: echo 'your log here' >> sample.log")
    print("-" * 60)

    event_handler = LogFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(0.5) # Keep the script running
    except KeyboardInterrupt:
        print("\nStopping watcher.")
        observer.stop()
    
    observer.join()
