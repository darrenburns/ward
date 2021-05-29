from rich.text import Span, Text

from ward import test
from ward._diff import Diff


@test("Diff renders a simple string diff correctly (no symbols, no intraline diff)")
def _():
    # In this case, difflib returns a diff without the intraline differences
    lhs = "hello"
    rhs = "halo"
    diff = Diff(lhs, rhs, 80)

    render_iter = diff.__rich_console__(None, None)

    actual_lhs: Text = next(render_iter)
    actual_rhs: Text = next(render_iter)

    assert actual_lhs == Text(lhs)
    assert actual_lhs.style == "green"

    assert actual_rhs == Text(rhs)
    assert actual_rhs.style == "red"


@test("Diff renders a simple string diff correctly (no symbols, intraline diff)")
def _():
    lhs = "hello"
    rhs = "hallo"
    diff = Diff(lhs, rhs, 80)

    render_iter = diff.__rich_console__(None, None)

    actual_lhs: Text = next(render_iter)
    actual_rhs: Text = next(render_iter)

    expected_lhs = Text(
        lhs,
        spans=[Span(0, 1, "green"), Span(1, 2, "white on green"), Span(2, 5, "green")],
    )
    expected_rhs = Text(
        rhs, spans=[Span(0, 1, "red"), Span(1, 2, "white on red"), Span(2, 5, "red")]
    )

    assert actual_lhs == expected_lhs
    assert actual_rhs == expected_rhs


@test("Diff renders simple string diff correctly (symbols, intraline diff)")
def _():
    lhs = "hello"
    rhs = "hallo"
    diff = Diff(lhs, rhs, 80, show_symbols=True)

    render_iter = diff.__rich_console__(None, None)

    diff_line_1: Text = next(render_iter)
    diff_line_2: Text = next(render_iter)
    diff_line_3: Text = next(render_iter)
    diff_line_4: Text = next(render_iter)

    assert diff_line_1 == Text("+ hello")
    assert diff_line_2 == Text("?  ^")
    assert diff_line_3 == Text("- hallo")
    assert diff_line_4 == Text("?  ^")

    assert diff_line_1.style == "green"
    assert diff_line_2.style == "green"
    assert diff_line_3.style == "red"
    assert diff_line_4.style == "red"


@test(
    "Diff renders string diff correctly, when string wider than terminal (no symbols)"
)
def _():
    lhs = "the quick brown fox jumped over the lazy dog"
    rhs = "the quick brown cat jumped over the lazy dog"
    diff = Diff(lhs, rhs, 12)

    render_iter = diff.__rich_console__(None, None)

    actual_lhs: Text = next(render_iter)
    actual_rhs: Text = next(render_iter)

    assert actual_lhs == Text(
        lhs,
        spans=[
            Span(0, 16, "green"),
            Span(16, 19, "white on green"),
            Span(19, 44, "green"),
        ],
    )
    assert actual_rhs == Text(
        rhs,
        spans=[Span(0, 16, "red"), Span(16, 19, "white on red"), Span(19, 44, "red")],
    )
