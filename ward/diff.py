import difflib
import pprint

from colorama import Style
from termcolor import colored


def build_auto_diff(lhs, rhs, width=60) -> str:
    """Determines the best type of diff to use based on the output"""
    if isinstance(lhs, str):
        lhs_repr = lhs
    else:
        lhs_repr = pprint.pformat(lhs, width=width)

    if isinstance(rhs, str):
        rhs_repr = rhs
    else:
        rhs_repr = pprint.pformat(rhs, width=width)

    return build_unified_diff(lhs_repr, rhs_repr)


def build_split_diff(lhs_repr, rhs_repr) -> str:
    lhs_out, rhs_out = "", ""

    matcher = difflib.SequenceMatcher(None, lhs_repr, rhs_repr)
    for op, i1, i2, j1, j2 in matcher.get_opcodes():

        lhs_substring_lines = lhs_repr[i1:i2].splitlines()
        rhs_substring_lines = rhs_repr[j1:j2].splitlines()

        for i, lhs_substring in enumerate(lhs_substring_lines):
            if op == "replace":
                lhs_out += colored(lhs_substring, color="green")
            elif op == "delete":
                lhs_out += colored(lhs_substring, color="green")
            elif op == "insert":
                lhs_out += lhs_substring
            elif op == "equal":
                lhs_out += lhs_substring

            if i != len(lhs_substring_lines) - 1:
                lhs_out += f"\n"

        for j, rhs_substring in enumerate(rhs_substring_lines):
            if op == "replace":
                rhs_out += colored(rhs_substring, color="red")
            elif op == "insert":
                rhs_out += colored(rhs_substring, color="red")
            elif op == "equal":
                rhs_out += rhs_substring

            if j != len(rhs_substring_lines) - 1:
                rhs_out += f"\n"

    # TODO: Clean up the line below
    return f"LHS: {lhs_out}\nRHS: {rhs_out}"


def bright(s: str) -> str:
    return f"{Style.BRIGHT}{s}{Style.RESET_ALL}"


def build_unified_diff(lhs_repr, rhs_repr, margin_left=4) -> str:
    differ = difflib.Differ()
    lines_lhs = lhs_repr.splitlines()
    lines_rhs = rhs_repr.splitlines()
    diff = differ.compare(lines_lhs, lines_rhs)

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
            output_lines[last_output_idx] = ""  # We'll rewrite the prev line with highlights
            current_span = ""
            index = 2  # Differ lines start with a 2 letter code, so skip past that
            char = line[index]
            prev_char = char
            while index < len(line):
                char = line[index]
                if prev_marker in "+-":
                    if char != prev_char:
                        if prev_char == " " and prev_marker == "+":
                            output_lines[last_output_idx] += colored(current_span, color="red")
                        elif prev_char == " " and prev_marker == "-":
                            output_lines[last_output_idx] += colored(current_span, color="green")
                        elif prev_char in "+^" and prev_marker == "+":
                            output_lines[last_output_idx] += bright(
                                colored(current_span, color="red", on_color="on_red"))
                        elif prev_char in "-^" and prev_marker == "-":
                            output_lines[last_output_idx] += bright(
                                colored(current_span, color="green", on_color="on_green"))
                        current_span = ""
                    current_span += line_to_rewrite[index - 2]  # Subtract 2 to account for code at start of line
                prev_char = char
                index += 1

            # Lines starting with ? aren't guaranteed to be the same length as the lines before them
            #  so some characters may be left over. Add any leftover characters to the output
            remaining_index = index - 3  # subtract 2 for code at start, and 1 to remove the newline char
            if prev_marker == "+":
                output_lines[last_output_idx] += colored(line_to_rewrite[remaining_index:], color="red")
            elif prev_marker == "-":
                output_lines[last_output_idx] += colored(line_to_rewrite[remaining_index:], color="green")


        else:
            output_lines.append(line[2:])
        prev_marker = line[0]

    return " " * margin_left + f"\n{' ' * margin_left}".join(output_lines)
