import sys

from blessings import Terminal

ESCAPE_CODE_MARGIN_BUFFER = 18


def write_over_live_message(str_to_write: str, term: Terminal):
    write_over_line(str_to_write, 2, term)

def write_over_progress_bar(green_pct: float, red_pct: float, term: Terminal):
    bar = term.green("█" * int(green_pct * term.width)) + term.red("█" * int(red_pct * term.width))
    write_over_line(bar, 1, term)


def write_over_line(str_to_write: str, offset_from_bottom: int, term: Terminal):
    with term.location(0, term.height - offset_from_bottom):
        right_margin = max(0, term.width - len(str_to_write) + ESCAPE_CODE_MARGIN_BUFFER) * " "
        print(f"{str_to_write}{right_margin}")
        sys.stdout.flush()
