import click
import sys
import time
from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver

from ward.core import run_tests_at_path_and_output_results
from ward.testing import clear_cached_tests


class WatchModeChangeHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()

    def on_moved(self, event):
        super().on_moved(event)

    def on_created(self, event):
        super().on_created(event)

    def on_modified(self, event):
        super().on_modified(event)
        what = "directory" if event.is_directory else "file"
        if what == "file":
            print(f"{what} changed: {event.src_path}")
            run_tests_at_path_and_output_results((event.src_path,))
            clear_cached_tests()


def enter_watch_mode(context: click.Context, param: click.Parameter, value: str):
    if not value or context.resilient_parsing:
        return

    observer = PollingObserver()
    event_handler = WatchModeChangeHandler()
    observer.schedule(event_handler, value, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    sys.exit(0)
