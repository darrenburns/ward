import difflib
import pprint

from colorama import Fore, Style


def build_split_diff(lhs, rhs, width=80):
    lhs_repr = pprint.pformat(lhs, width=width)
    rhs_repr = pprint.pformat(rhs, width=width)
    lhs_out, rhs_out = "", ""

    matcher = difflib.SequenceMatcher(None, lhs_repr, rhs_repr)
    for op, i1, i2, j1, j2 in matcher.get_opcodes():

        lhs_substring_lines = lhs_repr[i1:i2].splitlines()
        rhs_substring_lines = rhs_repr[j1:j2].splitlines()

        for i, lhs_substring in enumerate(lhs_substring_lines):
            if op == "replace":
                lhs_out += f"{Fore.GREEN}{lhs_substring}"
            elif op == "delete":
                lhs_out += f"{Fore.GREEN}{lhs_substring}"
            elif op == "insert":
                lhs_out += f"{Fore.RESET}{lhs_substring}"
            elif op == "equal":
                lhs_out += f"{Fore.RESET}{lhs_substring}"

            if i != len(lhs_substring_lines) - 1:
                lhs_out += f"{Style.RESET_ALL}\n"

        for j, rhs_substring in enumerate(rhs_substring_lines):
            if op == "replace":
                rhs_out += f"{Fore.RED}{rhs_substring}"
            elif op == "insert":
                rhs_out += f"{Fore.RED}{rhs_substring}"
            elif op == "equal":
                rhs_out += f"{Fore.RESET}{rhs_substring}"

            if j != len(rhs_substring_lines) - 1:
                rhs_out += f"{Style.RESET_ALL}\n"

    return lhs_out, rhs_out


def build_unified_diff(lhs, rhs, width=80, margin_left=4):
    differ = difflib.Differ()
    lines_lhs = pprint.pformat(lhs, width=width).splitlines()
    lines_rhs = pprint.pformat(rhs, width=width).splitlines()
    diff = differ.compare(lines_lhs, lines_rhs)

    output = []
    for line in diff:
        # Differ instructs us how to transform left into right, but we want
        # our colours to indicate how to transform right into left
        if line.startswith("- "):
            output.append(f"{Fore.GREEN}{line[2:]}")
        elif line.startswith("+ "):
            output.append(f"{Fore.RED}{line[2:]}")
        elif line.startswith("? "):
            # We can use this to find the index of change in the
            # line above if required in the future
            pass
        else:
            output.append(f"{Fore.RESET}{line[2:]}")

    return " " * margin_left + f"\n{' ' * margin_left}".join(output)
