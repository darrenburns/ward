from tests.utilities import make_empty_project, make_project
from ward import fixture, test, using
from ward._utilities import find_project_root, group_by, truncate
from ward.testing import each


@fixture
def s():
    return "hello world"


@test("truncate('{input}', num_chars={num_chars}) returns '{expected}'")
def _(
    input=s, num_chars=each(20, 11, 10, 5), expected=each(s, s, "hello w...", "he...")
):
    result = truncate(input, num_chars)
    assert result == expected


@test("find_project_root returns None if no paths supplied")
def _():
    project_root = find_project_root([])
    assert project_root is None


@fixture
def fake_project_pyproject():
    content = """
    [tool.ward]
    path = ["a/", "x/y"]
    exclude = ["a/b/"]
    order = "hello world"
    """
    yield from make_project("pyproject.toml", content)


@fixture
def fake_project_empty():
    yield from make_empty_project()


@fixture
def fake_project_git():
    yield from make_project(".git")


@using(
    root_file=each("pyproject.toml", ".git"),
    project=each(fake_project_pyproject, fake_project_git),
)
@test("find_project_root finds project root with '{root_file}' file")
def _(root_file, project):
    root = find_project_root([project / "a/b/c", project / "a/d"])
    assert root.resolve() == project.resolve()
    assert (root / root_file).exists()


def is_even(n):
    return n % 2 == 0


def is_vowel(char):
    return char in "aeiou"


def square(x):
    return x**2


@test("group {items!r} by {key.__name__} returns {result}")
def _(
    items=each(range(5), "echolocation", [-2, 3, 4, -3, 2, 3]),
    key=each(is_even, is_vowel, square),
    result=each(
        {True: [0, 2, 4], False: [1, 3]},
        {True: ["e", "o", "o", "a", "i", "o"], False: ["c", "h", "l", "c", "t", "n"]},
        {4: [-2, 2], 9: [3, -3, 3], 16: [4]},
    ),
):
    assert group_by(items, key) == result
