import sys

from blessings import Terminal


def write_test_result(str_to_write: str, term: Terminal):
    write_over_line(str_to_write, 2, term)


def write_over_progress_bar(green_pct: float, red_pct: float, term: Terminal):
    num_green_bars = int(green_pct * term.width)
    num_red_bars = int(red_pct * term.width)

    # Deal with rounding, converting to int could leave us with 1 bar less, so make it green
    if term.width - num_green_bars - num_red_bars == 1:
        num_green_bars += 1

    bar = term.red("█" * num_red_bars) + term.green("█" * num_green_bars)
    write_over_line(bar, 2, term)


def write_over_line(str_to_write: str, offset_from_bottom: int, term: Terminal):
    esc_code_rhs_margin = 28  # chars that are part of escape code, but NOT actually printed.
    with term.location(None, term.height - offset_from_bottom):
        right_margin = max(0, term.width - len(str_to_write) + esc_code_rhs_margin) * " "
        sys.stdout.write(f"{str_to_write}{right_margin}")
        sys.stdout.flush()


def reset_cursor(term: Terminal):
    print(term.normal_cursor(), )
    print(term.move(term.height - 1, 0), )
