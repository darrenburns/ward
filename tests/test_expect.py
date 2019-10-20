from contextlib import suppress
from unittest.mock import Mock

from ward import expect, fixture
from ward.expect import Expected, ExpectationFailed


def test_equals_success_history_recorded():
    this, that = "hello", "hello"

    e = expect(this).equals(that)

    hist = [Expected(this=this, op="equals", that=that, op_args=(), op_kwargs={}, success=True)]
    expect(e.history).equals(hist)


def test_equals_failure_history_recorded():
    this, that = "hello", "goodbye"

    e = expect(this)
    with suppress(ExpectationFailed):
        e.equals(that)

    hist = [Expected(this=this, op="equals", that=that, op_args=(), op_kwargs={}, success=False)]
    expect(e.history).equals(hist)


def test_satisfies_success_history_recorded():
    this = "olleh"
    predicate = lambda e: this[::-1] == "hello"
    e = expect(this).satisfies(predicate)

    hist = [Expected(this=this, op="satisfies", that=predicate, op_args=(), op_kwargs={}, success=True)]

    expect(e.history).equals(hist)


def test_satisfies_failure_history_recorded():
    this = "olleh"
    predicate = lambda e: False

    e = expect(this)
    with suppress(ExpectationFailed):
        e.satisfies(predicate)

    hist = [Expected(this=this, op="satisfies", that=predicate, op_args=(), op_kwargs={}, success=False)]

    expect(e.history).equals(hist)


def test_approx_success_history_recorded():
    this, that, eps = 1.0, 1.01, 0.5

    e = expect(this).approx(that, abs_tol=eps)

    hist = [Expected(this=this, op="approx", that=that, op_args=(), op_kwargs={"rel_tol": 1e-09, "abs_tol": 0.5},
                     success=True)]
    expect(e.history).equals(hist)


def test_approx_failure_history_recorded():
    this, that, eps = 1.0, 1.01, 0.001

    # This will raise an ExpectationFailed, which would fail this test unless we catch it.
    e = expect(this)
    with suppress(ExpectationFailed):
        e.approx(that, eps)

    hist = [Expected(this=this, op="approx", that=that, op_args=(), op_kwargs={"rel_tol": 0.001, "abs_tol": 0.0},
                     success=False)]

    expect(e.history).equals(hist)


def test_not_equals_success_history_recorded():
    this, that = 1, 2

    e = expect(this).not_equals(that)

    hist = [Expected(this, op="not_equals", that=that, op_args=(), op_kwargs={}, success=True)]
    expect(e.history).equals(hist)


def test_not_equals_failure_history_recorded():
    this, that = 1, 1

    e = expect(this)
    with suppress(ExpectationFailed):
        e.not_equals(that)

    hist = [Expected(this, op="not_equals", that=that, op_args=(), op_kwargs={}, success=False)]
    expect(e.history).equals(hist)


@fixture
def mock():
    return Mock()


def test_mock_called_success(mock):
    mock()
    e = expect(mock).called()

    hist = [Expected(mock, op="called", that=None, op_args=(), op_kwargs={}, success=True)]
    expect(e.history).equals(hist)


def test_mock_called_failure(mock):
    e = expect(mock)
    with suppress(ExpectationFailed):
        e.called()

    hist = [Expected(mock, op="called", that=None, op_args=(), op_kwargs={}, success=False)]
    expect(e.history).equals(hist)


def test_mock_not_called_success(mock):
    e = expect(mock).not_called()

    hist = [Expected(mock, op="not_called", that=None, op_args=(), op_kwargs={}, success=True)]
    expect(e.history).equals(hist)


def test_mock_called_once_with_success(mock):
    args = (1, 2, 3)
    kwargs = {"hello": "world"}
    mock(*args, **kwargs)

    e = expect(mock).called_once_with(*args, **kwargs)

    hist = [Expected(mock, op="called_once_with", that=None, op_args=args, op_kwargs=kwargs, success=True)]
    expect(e.history).equals(hist)


def test_mock_called_once_with_failure_missing_arg(mock):
    args = (1, 2, 3)
    kwargs = {"hello": "world"}
    mock(1, 2, **kwargs)  # 3 is missing intentionally

    e = expect(mock)
    with suppress(ExpectationFailed):
        e.called_once_with(*args, **kwargs)

    hist = [Expected(mock, op="called_once_with", that=None, op_args=args, op_kwargs=kwargs, success=False)]
    expect(e.history).equals(hist)


def test_mock_called_once_with_failure_missing_kwarg(mock):
    args = (1, 2, 3)
    kwargs = {"hello": "world"}
    mock(*args, wrong="thing")

    e = expect(mock)
    with suppress(ExpectationFailed):
        e.called_once_with(*args, **kwargs)

    hist = [Expected(mock, op="called_once_with", that=None, op_args=args, op_kwargs=kwargs, success=False)]
    expect(e.history).equals(hist)
