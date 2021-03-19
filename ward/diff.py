import difflib
from typing import Iterator

import pprintpp
from colorama import Style, Fore
from termcolor import colored


def make_diff(lhs, rhs, width=80, show_symbols=False):
    """Transform input into best format for diffing, then return output diff."""
    if isinstance(lhs, str):
        lhs_repr = lhs
    else:
        lhs_repr = pprintpp.pformat(lhs, width=width)

    if isinstance(rhs, str):
        rhs_repr = rhs
    else:
        rhs_repr = pprintpp.pformat(rhs, width=width)

    if show_symbols:
        return build_symbolic_unified_diff(lhs_repr, rhs_repr)
    return build_unified_diff(lhs_repr, rhs_repr)


def bright_red(s: str) -> str:
    return f"{Fore.LIGHTRED_EX}{s}{Style.RESET_ALL}"


def bright_green(s: str) -> str:
    return f"{Fore.LIGHTGREEN_EX}{s}{Style.RESET_ALL}"


def raw_unified_diff(lhs_repr: str, rhs_repr: str) -> Iterator[str]:
    differ = difflib.Differ()
    lines_lhs = lhs_repr.splitlines()
    lines_rhs = rhs_repr.splitlines()
    return differ.compare(lines_lhs, lines_rhs)


def build_symbolic_unified_diff(lhs_repr: str, rhs_repr: str) -> str:
    diff = raw_unified_diff(lhs_repr, rhs_repr)
    output_lines = []
    last_line_colour = "grey"
    for line_idx, line in enumerate(diff):
        if line.startswith("- "):
            last_line_colour = "green"
            output_lines.append(colored(f"+ {line[2:]}", color=last_line_colour))
        elif line.startswith("+ "):
            last_line_colour = "red"
            output_lines.append(colored(f"- {line[2:]}", color=last_line_colour))
        elif line.startswith("? "):
            output_line = line[:-1]
            if last_line_colour == "red":
                output_line = output_line.replace("+", "-")
            elif last_line_colour == "green":
                output_line = output_line.replace("-", "+")
            output_lines.append(colored(output_line, color=last_line_colour))
        else:
            output_lines.append(line)
    return "\n".join(output_lines)


def build_unified_diff(lhs_repr: str, rhs_repr: str) -> str:
    diff = raw_unified_diff(lhs_repr, rhs_repr)
    output_lines = []
    prev_marker = ""
    for line_idx, line in enumerate(diff):
        if line.startswith("- "):
            output_lines.append(colored(line[2:], color="green"))
        elif line.startswith("+ "):
            output_lines.append(colored(line[2:], color="red"))
        elif line.startswith("? "):
            last_output_idx = len(output_lines) - 1
            # Remove the 5 char escape code from the line
            esc_code_length = 5
            line_to_rewrite = output_lines[last_output_idx][esc_code_length:]
            output_lines[
                last_output_idx
            ] = ""  # We'll rewrite the prev line with highlights
            current_span = ""
            index = 2  # Differ lines start with a 2 letter code, so skip past that
            char = line[index]
            prev_char = char
            while index < len(line):
                char = line[index]
                if prev_marker in "+-":
                    if char != prev_char:
                        if prev_char == " " and prev_marker == "+":
                            output_lines[last_output_idx] += colored(
                                current_span, color="red"
                            )
                        elif prev_char == " " and prev_marker == "-":
                            output_lines[last_output_idx] += colored(
                                current_span, color="green"
                            )
                        elif prev_char in "+^" and prev_marker == "+":
                            output_lines[last_output_idx] += bright_red(
                                colored(current_span, on_color="on_red", attrs=["bold"])
                            )
                        elif prev_char in "-^" and prev_marker == "-":
                            output_lines[last_output_idx] += bright_green(
                                colored(
                                    current_span, on_color="on_green", attrs=["bold"]
                                )
                            )
                        current_span = ""
                    # Subtract 2 to account for code at start of line
                    current_span += line_to_rewrite[index - 2]
                prev_char = char
                index += 1

            # Lines starting with ? aren't guaranteed to be the same length as the lines before them
            #  so some characters may be left over. Add any leftover characters to the output

            # subtract 2 for code at start, and 1 to remove the newline char
            remaining_index = index - 3
            if prev_marker == "+":
                output_lines[last_output_idx] += colored(
                    line_to_rewrite[remaining_index:], color="red"
                )
            elif prev_marker == "-":
                output_lines[last_output_idx] += colored(
                    line_to_rewrite[remaining_index:], color="green"
                )

        else:
            output_lines.append(line[2:])
        prev_marker = line[0]

    return "\n".join(output_lines)
