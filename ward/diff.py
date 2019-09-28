import difflib
import pprint

from colorama import Fore, Style


def build_split_diff(lhs, rhs):
    lhs_repr = pprint.pformat(lhs, width=80)
    rhs_repr = pprint.pformat(rhs, width=80)
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
                lhs_out += lhs_substring
            elif op == "equal":
                lhs_out += lhs_substring

            if i != len(lhs_substring_lines) - 1:
                lhs_out += f"{Style.RESET_ALL}\n"

        for j, rhs_substring in enumerate(rhs_substring_lines):
            if op == "replace":
                rhs_out += f"{Fore.RED}{rhs_substring}"
            elif op == "insert":
                rhs_out += f"{Fore.RED}{rhs_substring}"
            elif op == "equal":
                rhs_out += rhs_substring

            if j != len(rhs_substring_lines) - 1:
                rhs_out += f"{Style.RESET_ALL}\n"

    return lhs_out, rhs_out
