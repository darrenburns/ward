import difflib
import pprint

from colorama import Fore, Style


def build_auto_diff(lhs, rhs, width=60) -> str:
    """Determines the best type of diff to use based on the output"""

    lhs_repr = pprint.pformat(lhs, width=width)
    rhs_repr = pprint.pformat(rhs, width=width)
    # TODO: Right now, just stick to unified diff while deciding what to do
    # if "\n" in lhs_repr and "\n" in rhs_repr:
    #     diff = build_unified_diff(lhs_repr, rhs_repr)
    # else:
    #     diff = build_split_diff(lhs_repr, rhs_repr)

    return build_unified_diff(lhs_repr, rhs_repr)


def build_split_diff(lhs_repr, rhs_repr) -> str:
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

    # TODO: Clean up the line below
    return f"LHS: {lhs_out}\nRHS: {rhs_out}"


def build_unified_diff(lhs_repr, rhs_repr, margin_left=4) -> str:
    differ = difflib.Differ()
    lines_lhs = lhs_repr.splitlines()
    lines_rhs = rhs_repr.splitlines()
    diff = differ.compare(lines_lhs, lines_rhs)

    output = []
    for line in diff:
        if line.startswith("- "):
            output.append(f"{Fore.GREEN}{line[2:]}")
        elif line.startswith("+ "):
            output.append(f"{Fore.RED}{line[2:]}")
        elif line.startswith("? "):
            # We can use this to find the index of change in
            # the line above if required in the future
            pass
        else:
            output.append(f"{Fore.RESET}{line[2:]}")

    return " " * margin_left + f"\n{' ' * margin_left}".join(output)
