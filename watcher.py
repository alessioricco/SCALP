import sys
import subprocess
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from threading import Timer

class ChangeHandler(PatternMatchingEventHandler):
    patterns = ["*.py", "*.txt"]  # Watch for changes in Python and text files.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.process = None
        self.debounce_period = 1  # Seconds
        self.timer = None

    def restart_app(self):
        if self.process:
            self.process.terminate()  # Gracefully terminate the process
        print("Restarting the application...")
        self.process = subprocess.Popen(["python", "main.py"])  # Start a new process

    def handle_event(self, event):
        if self.timer is not None:
            self.timer.cancel()
        self.timer = Timer(self.debounce_period, self.restart_app)
        self.timer.start()

    def on_any_event(self, event):
        print(f"Change detected in {event.src_path}. Preparing to restart the app.")
        self.handle_event(event)

if __name__ == "__main__":
    path = '.'
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            observer.join(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
