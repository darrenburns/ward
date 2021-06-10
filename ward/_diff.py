import difflib
from typing import Iterator, List

import pprintpp
from rich.console import Console, ConsoleOptions, RenderResult
from rich.text import Text


class Diff:
    """Constructs a Diff object to render diff-highlighted code."""

    def __init__(self, lhs, rhs, width, show_symbols=False) -> None:
        self.width = width
        self.lhs = lhs if isinstance(lhs, str) else pprintpp.pformat(lhs, width=width)
        self.rhs = rhs if isinstance(rhs, str) else pprintpp.pformat(rhs, width=width)
        self.show_symbols = show_symbols

    def raw_unified_diff(self) -> Iterator[str]:
        differ = difflib.Differ()
        lines_lhs = self.lhs.splitlines()
        lines_rhs = self.rhs.splitlines()
        return differ.compare(lines_lhs, lines_rhs)

    def build_symbolic_unified_diff(self) -> RenderResult:
        diff = self.raw_unified_diff()
        output_lines = []
        style = "grey"
        last_style = style
        for line in diff:
            if line.startswith("- "):
                style = "green"
                output_line = f"+ {line[2:]}"
            elif line.startswith("+ "):
                style = "red"
                output_line = f"- {line[2:]}"
            elif line.startswith("? "):
                if last_style == "red":
                    output_line = line[:-1].replace("+", "-")
                elif last_style == "green":
                    output_line = line[:-1].replace("-", "+")
            else:
                output_line = line
                style = "gray"
            output_lines.append(Text(output_line, style=style))
            last_style = style if style != "gray" else last_style
        return output_lines

    def rewrite_line(self, line, line_to_rewrite, prev_marker):
        marker_style_map = {
            "-": {
                " ": "green",
                "-": "white on green",
                "^": "white on green",
            },
            "+": {
                " ": "red",
                "+": "white on red",
                "^": "white on red",
            },
        }
        new_line = Text("")
        current_span = []
        # Differ lines start with a 2 letter code, so skip past that
        prev_char = line[2]
        for idx, char in enumerate(line[2:], start=2):
            if prev_marker in ("+", "-"):
                if char != prev_char:
                    style = marker_style_map.get(prev_marker, {}).get(prev_char, None)
                    if style is not None:
                        new_line.append_text(Text("".join(current_span), style=style))
                    current_span = []
                if idx - 2 < len(line_to_rewrite):
                    current_span.append(line_to_rewrite[idx - 2])
            prev_char = char

        # Lines starting with ? aren't guaranteed to be the same length as the lines before them
        #  so some characters may be left over. Add any leftover characters to the output.
        # subtract 2 for code at start
        remaining_index = idx - 2
        if prev_marker == "+":
            new_line.append_text(Text(line_to_rewrite[remaining_index:], style="red"))
        elif prev_marker == "-":
            new_line.append_text(Text(line_to_rewrite[remaining_index:], style="green"))
        return new_line

    def build_unified_diff(self) -> RenderResult:
        diff = self.raw_unified_diff()
        prev_marker = ""
        output_lines: List[Text] = []
        for line in diff:
            if line.startswith("- "):
                output_lines.append(Text(line[2:], style="green"))
            elif line.startswith("+ "):
                output_lines.append(Text(line[2:], style="red"))
            elif line.startswith("? "):
                line_to_rewrite = output_lines[-1].plain
                output_lines[-1] = self.rewrite_line(line, line_to_rewrite, prev_marker)
            else:
                output_lines.append(Text(line[2:]))
            prev_marker = line[0]
        return output_lines

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        if self.show_symbols:
            result = self.build_symbolic_unified_diff()
        else:
            result = self.build_unified_diff()
        yield from result
