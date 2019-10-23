from unittest.mock import Mock, patch, call

from ward import expect, fixture, raises, test
from ward.expect import Expected, ExpectationFailed, math


@test("equals should record history on pass")
def _():
    this, that = "hello", "hello"

    e = expect(this).equals(that)

    hist = [Expected(this=this, op="equals", that=that, op_args=(), op_kwargs={}, success=True)]
    expect(e.history).equals(hist)


@test("equals should record history on fail")
def _():
    this, that = "hello", "goodbye"

    e = expect(this)
    with raises(ExpectationFailed):
        e.equals(that)

    hist = [Expected(this=this, op="equals", that=that, op_args=(), op_kwargs={}, success=False)]
    expect(e.history).equals(hist)


def test_equals_failure_ExpectationFailed_raised():
    with raises(ExpectationFailed):
        expect(1).equals(2)


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
    with raises(ExpectationFailed):
        e.satisfies(predicate)

    hist = [Expected(this=this, op="satisfies", that=predicate, op_args=(), op_kwargs={}, success=False)]

    expect(e.history).equals(hist)


def test_satisfies_failure_ExpectationFailed_raised():
    with raises(ExpectationFailed):
        expect(1).satisfies(lambda x: False)


def test_identical_to_succeeds_when_things_are_identical():
    expect(ZeroDivisionError).identical_to(ZeroDivisionError)


def test_identical_to_fails_when_things_are_not_identical():
    with raises(ExpectationFailed):
        expect(ZeroDivisionError).identical_to(AttributeError)


def test_approx_success_history_recorded():
    this, that, eps = 1.0, 1.01, 0.5

    e = expect(this).approx(that, abs_tol=eps)

    hist = [
        Expected(
            this=this, op="approx", that=that, op_args=(), op_kwargs={"rel_tol": 1e-09, "abs_tol": 0.5}, success=True
        )
    ]
    expect(e.history).equals(hist)


def test_approx_failure_history_recorded():
    this, that, eps = 1.0, 1.01, 0.001

    e = expect(this)
    with raises(ExpectationFailed):
        e.approx(that, eps)

    hist = [
        Expected(
            this=this, op="approx", that=that, op_args=(), op_kwargs={"rel_tol": 0.001, "abs_tol": 0.0}, success=False
        )
    ]

    expect(e.history).equals(hist)


@fixture
def isclose():
    with patch.object(math, "isclose", autospec=True) as m:
        yield m


def test_approx_delegates_to_math_isclose_correctly(isclose):
    this, that = 1.0, 1.1
    abs_tol, rel_tol = 0.1, 0.2

    expect(this).approx(that, abs_tol=abs_tol, rel_tol=rel_tol)

    expect(isclose).called_once_with(this, that, abs_tol=abs_tol, rel_tol=rel_tol)


def test_not_approx_delegeates_to_isclose_correctly(isclose):
    this, that = 1.0, 1.2
    abs_tol = 0.01

    with raises(ExpectationFailed):
        expect(this).not_approx(that, abs_tol=abs_tol)

    expect(isclose).called_once_with(this, that, abs_tol=abs_tol, rel_tol=1e-9)


def test_not_equals_success_history_recorded():
    this, that = 1, 2

    e = expect(this).not_equals(that)

    hist = [Expected(this, op="not_equals", that=that, op_args=(), op_kwargs={}, success=True)]
    expect(e.history).equals(hist)


def test_not_equals_failure_history_recorded():
    this, that = 1, 1

    e = expect(this)
    with raises(ExpectationFailed):
        e.not_equals(that)

    hist = [Expected(this, op="not_equals", that=that, op_args=(), op_kwargs={}, success=False)]
    expect(e.history).equals(hist)


@fixture
def mock():
    return Mock()


def test_mock_called_when_mock_was_called(mock):
    mock()
    e = expect(mock).called()

    hist = [Expected(mock, op="called", that=None, op_args=(), op_kwargs={}, success=True)]
    expect(e.history).equals(hist)


def test_mock_called_when_mock_wasnt_called(mock):
    e = expect(mock)
    with raises(ExpectationFailed):
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
    with raises(ExpectationFailed):
        e.called_once_with(*args, **kwargs)

    hist = [Expected(mock, op="called_once_with", that=None, op_args=args, op_kwargs=kwargs, success=False)]
    expect(e.history).equals(hist)


def test_mock_called_once_with_failure_missing_kwarg(mock):
    args = (1, 2, 3)
    kwargs = {"hello": "world"}
    mock(*args, wrong="thing")

    e = expect(mock)
    with raises(ExpectationFailed):
        e.called_once_with(*args, **kwargs)

    hist = [Expected(mock, op="called_once_with", that=None, op_args=args, op_kwargs=kwargs, success=False)]
    expect(e.history).equals(hist)


def test_mock_called_once_with_fails_when_multiple_correct_calls(mock):
    args = (1, 2, 3)
    kwargs = {"hello": "world"}

    mock(*args, **kwargs)
    mock(*args, **kwargs)

    e = expect(mock)
    with raises(ExpectationFailed):
        e.called_once_with(*args, **kwargs)

    hist = [Expected(mock, op="called_once_with", that=None, op_args=args, op_kwargs=kwargs, success=False)]
    expect(e.history).equals(hist)


def test_mock_called_once_with_fails_when_multiple_calls_but_one_correct(mock):
    args = (1, 2, 3)
    kwargs = {"hello": "world"}

    mock(1)
    mock(*args, **kwargs)
    mock(2)

    e = expect(mock)
    with raises(ExpectationFailed):
        e.called_once_with(*args, **kwargs)

    hist = [Expected(mock, op="called_once_with", that=None, op_args=args, op_kwargs=kwargs, success=False)]
    expect(e.history).equals(hist)


def test_called_with_succeeds_when_expected_call_is_last(mock):
    mock(1)
    mock(2)

    e = expect(mock).called_with(2)
    expect(e.history[0].success).equals(True)


def test_called_with_fails_when_expected_call_is_made_but_not_last(mock):
    mock(2)
    mock(1)
    e = expect(mock)
    with raises(ExpectationFailed):
        e.called_with(2)
    expect(e.history[0].success).equals(False)


def test_has_calls_succeeds_when_all_calls_were_made(mock):
    mock(1, 2)
    mock(key="value")

    e = expect(mock).has_calls([call(1, 2), call(key="value")])
    expect(e.history[0].success).equals(True)


def test_has_calls_fails_when_not_all_calls_were_made(mock):
    mock(1, 2)

    e = expect(mock)
    with raises(ExpectationFailed):
        e.has_calls([call(1, 2), call(key="value")])
    expect(e.history[0].success).equals(False)


def test_has_calls_fails_when_calls_were_made_in_wrong_order(mock):
    mock(1, 2)
    mock(key="value")

    e = expect(mock)
    with raises(ExpectationFailed):
        e.has_calls([call(key="value"), call(1, 2)])


def test_has_calls_succeeds_when_all_calls_were_made_any_order(mock):
    mock(1, 2)
    mock(key="value")

    e = expect(mock).has_calls(
        [call(key="value"), call(1, 2)],
        any_order=True,
    )

    expect(e.history[0].success).equals(True)
