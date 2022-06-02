import shutil
import tempfile
from collections import defaultdict
from pathlib import Path

from ward import fixture, test
from ward._testing import is_test_module_name
from ward.fixtures import Fixture
from ward.testing import Test

NUMBER_OF_TESTS = 5
FORCE_TEST_PATH = Path("path/of/test").absolute()


def testable_test(func):
    """
    Decorate a function with this to treat it as a test that doesn't
    interfere with the "normal" tests, i.e. it collects into a separate
    location, uses a static path, module name etc. Useful for writing
    Ward internal tests.
    """
    func.__module__ = "test_x"
    assert is_test_module_name(func.__module__)
    return test(
        "testable test description",
        _force_path=FORCE_TEST_PATH,
        _collect_into=defaultdict(list),
    )(func)


testable_test.path = FORCE_TEST_PATH  # type: ignore[attr-defined]


@fixture
def dummy_fixture():
    """
    This is a dummy fixture for use inside tests.
    """
    return "dummy"


@fixture
def fixture_b():
    def b():
        return 2

    return b


@fixture
def fixture_a(b=fixture_b):
    def a(b=b):
        return b * 2

    return a


@fixture
def fixtures(a=fixture_a, b=fixture_b):
    return {"fixture_a": Fixture(fn=a), "fixture_b": Fixture(fn=b)}


@fixture
def module():
    return "test_module"


@fixture
def example_test(module=module, fixtures=fixtures):
    @fixture
    def f():
        return 123

    @testable_test
    def t(fix_a=f):
        return fix_a

    return Test(fn=t, module_name=module)


def make_project(root_file: str, file_content: str = ""):
    tempdir = Path(tempfile.gettempdir())
    paths = [
        tempdir / "project/a/b/c",
        tempdir / "project/a/d",
        tempdir / "project/a",
        tempdir / "project/x/y/z",
    ]
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)

    root_file_path = tempdir / f"project/{root_file}"
    with open(root_file_path, "w+", encoding="utf-8") as f:
        f.write(file_content)
        f.flush()
        yield (tempdir / "project").resolve()
    shutil.rmtree(tempdir / "project")


def make_empty_project():
    tempdir = Path(tempfile.gettempdir())
    paths = [
        tempdir / "project/a/b/c",
        tempdir / "project/a/d",
        tempdir / "project/a",
        tempdir / "project/x/y/z",
    ]
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)

    yield (tempdir / "project").resolve()

    shutil.rmtree(tempdir / "project")
