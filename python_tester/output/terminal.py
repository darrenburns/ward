import sys

from blessings import Terminal

ESC_CODE_RHS_BUFFER = 18


def write_test_result(str_to_write: str, term: Terminal):
    write_over_line(str_to_write, 3, term)


def write_over_progress_bar(green_pct: float, red_pct: float, term: Terminal):
    num_green_bars = int(green_pct * term.width)
    num_red_bars = int(red_pct * term.width)

    # Deal with rounding, converting to int could leave us with 1 bar less, so make it green
    if term.width - num_green_bars - num_red_bars == 1:
        num_green_bars += 1

    bar = term.green("█" * num_green_bars) + term.red("█" * num_red_bars)
    write_over_line(bar, 2, term)


def write_over_line(str_to_write: str, offset_from_bottom: int, term: Terminal):
    with term.location(None, term.height - offset_from_bottom):
        right_margin = max(0, term.width - len(str_to_write) + ESC_CODE_RHS_BUFFER) * " "
        sys.stdout.write(f"{str_to_write}{right_margin}")
        sys.stdout.flush()


def reset_cursor(term: Terminal):
    print(term.normal_cursor(), )
    print(term.move(term.height - 1, 0), )
