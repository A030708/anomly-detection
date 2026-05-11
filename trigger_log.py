import os
LOG_FILE = "sample.log"
with open(LOG_FILE, "a", encoding="utf-8") as f:
    f.write('{"timestamp": "2024-10-25T10:10:00", "level": "ERROR", "source": "python-test", "message": "Python UTF-8 test log"}\n')
print("Log written.")
