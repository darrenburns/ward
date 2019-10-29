from unittest.mock import Mock, patch, call

from ward import expect, fixture, raises, test
from ward.expect import Expected, ExpectationFailed, math


@test("equals should record history when args are equal")
def _():
    this, that = "hello", "hello"

    e = expect(this).equals(that)

    hist = [
        Expected(
            this=this, op="equals", that=that, op_args=(), op_kwargs={}, success=True
        )
    ]
    expect(e.history).equals(hist)


@test("equals should record history when args aren't equal")
def _():
    this, that = "hello", "goodbye"

    e = expect(this)
    with raises(ExpectationFailed):
        e.equals(that)

    hist = [
        Expected(
            this=this, op="equals", that=that, op_args=(), op_kwargs={}, success=False
        )
    ]
    expect(e.history).equals(hist)


@test("equals should raise an ExpectationFailed when args aren't equal")
def _():
    with raises(ExpectationFailed):
        expect(1).equals(2)


@test("satisfies should record history when arg satisfies predicate")
def _():
    this = "olleh"
    predicate = lambda e: this[::-1] == "hello"
    e = expect(this).satisfies(predicate)

    hist = [
        Expected(
            this=this,
            op="satisfies",
            that=predicate,
            op_args=(),
            op_kwargs={},
            success=True,
        )
    ]

    expect(e.history).equals(hist)


@test("satisfies should record history when arg doesn't satisfy predicate")
def _():
    this = "olleh"
    predicate = lambda e: False

    e = expect(this)
    with raises(ExpectationFailed):
        e.satisfies(predicate)

    hist = [
        Expected(
            this=this,
            op="satisfies",
            that=predicate,
            op_args=(),
            op_kwargs={},
            success=False,
        )
    ]

    expect(e.history).equals(hist)


@test("satisfies should raise an ExpectationFailed when arg doesn't satisfy predicate")
def _():
    with raises(ExpectationFailed):
        expect(1).satisfies(lambda x: False)


@test("identical_to passes when args are identical")
def _():
    expect(ZeroDivisionError).identical_to(ZeroDivisionError)


@test("identical_to fails when args are not identical")
def _():
    with raises(ExpectationFailed):
        expect(ZeroDivisionError).identical_to(AttributeError)


@test("approx records history when args are within abs_tol of each other")
def _():
    this, that, eps = 1.0, 1.01, 0.5

    e = expect(this).approx(that, abs_tol=eps)

    hist = [
        Expected(
            this=this,
            op="approx",
            that=that,
            op_args=(),
            op_kwargs={"rel_tol": 1e-09, "abs_tol": 0.5},
            success=True,
        )
    ]
    expect(e.history).equals(hist)


@test("approx records history and raises when args aren't within abs_tol")
def _():
    this, that, eps = 1.0, 1.01, 0.001

    e = expect(this)
    with raises(ExpectationFailed):
        e.approx(that, eps)

    hist = [
        Expected(
            this=this,
            op="approx",
            that=that,
            op_args=(),
            op_kwargs={"rel_tol": 0.001, "abs_tol": 0.0},
            success=False,
        )
    ]

    expect(e.history).equals(hist)


@fixture
def isclose():
    with patch.object(math, "isclose", autospec=True) as m:
        yield m


@test("approx calls `math.isclose` with the expected args")
def _(isclose=isclose):
    this, that = 1.0, 1.1
    abs_tol, rel_tol = 0.1, 0.2

    expect(this).approx(that, abs_tol=abs_tol, rel_tol=rel_tol)

    expect(isclose).called_once_with(this, that, abs_tol=abs_tol, rel_tol=rel_tol)


@test("not_approx calls `math.isclose` with the expected args")
def _(isclose=isclose):
    this, that = 1.0, 1.2
    abs_tol = 0.01

    with raises(ExpectationFailed):
        expect(this).not_approx(that, abs_tol=abs_tol)

    expect(isclose).called_once_with(this, that, abs_tol=abs_tol, rel_tol=1e-9)


@test("not_equals records history args items aren't equal")
def _():
    this, that = 1, 2

    e = expect(this).not_equals(that)

    hist = [
        Expected(
            this, op="not_equals", that=that, op_args=(), op_kwargs={}, success=True
        )
    ]
    expect(e.history).equals(hist)


@test("not_equals records history and raises ExpectationFailed when args are equal")
def _():
    this, that = 1, 1

    e = expect(this)
    with raises(ExpectationFailed):
        e.not_equals(that)

    hist = [
        Expected(
            this, op="not_equals", that=that, op_args=(), op_kwargs={}, success=False
        )
    ]
    expect(e.history).equals(hist)


@fixture
def mock():
    return Mock()


@test("expect.called records history when the mock was called")
def _(mock=mock):
    mock()
    e = expect(mock).called()

    hist = [
        Expected(mock, op="called", that=None, op_args=(), op_kwargs={}, success=True)
    ]
    expect(e.history).equals(hist)


@test(
    "expect.called records history and raises ExpectationFailed when mock was not called"
)
def _(mock=mock):
    e = expect(mock)
    with raises(ExpectationFailed):
        e.called()

    hist = [
        Expected(mock, op="called", that=None, op_args=(), op_kwargs={}, success=False)
    ]
    expect(e.history).equals(hist)


@test("expect.not_called records history, even when the mock wasn't called")
def _(m=mock):
    e = expect(m).not_called()

    hist = [
        Expected(m, op="not_called", that=None, op_args=(), op_kwargs={}, success=True)
    ]
    expect(e.history).equals(hist)


@test(
    "called_once_with records history when the mock was called as expected exactly once"
)
def _(m=mock):
    args = (1, 2, 3)
    kwargs = {"hello": "world"}
    m(*args, **kwargs)

    e = expect(m).called_once_with(*args, **kwargs)

    hist = [
        Expected(
            m,
            op="called_once_with",
            that=None,
            op_args=args,
            op_kwargs=kwargs,
            success=True,
        )
    ]
    expect(e.history).equals(hist)


@test("called_once_with records history and raises when positional arg missing")
def _(m=mock):
    args = (1, 2, 3)
    kwargs = {"hello": "world"}
    m(1, 2, **kwargs)  # 3 is missing intentionally

    e = expect(m)
    with raises(ExpectationFailed):
        e.called_once_with(*args, **kwargs)

    hist = [
        Expected(
            m,
            op="called_once_with",
            that=None,
            op_args=args,
            op_kwargs=kwargs,
            success=False,
        )
    ]
    expect(e.history).equals(hist)


@test("called_once_with records history and raises when kwarg missing")
def _(m: Mock = mock):
    args = (1, 2, 3)
    kwargs = {"hello": "world"}
    m(*args, wrong="thing")

    e = expect(m)
    with raises(ExpectationFailed):
        e.called_once_with(*args, **kwargs)

    hist = [
        Expected(
            m,
            op="called_once_with",
            that=None,
            op_args=args,
            op_kwargs=kwargs,
            success=False,
        )
    ]
    expect(e.history).equals(hist)


@test(
    "called_once_with records history and raises when the expected call is made more than once"
)
def _(mock=mock):
    args = (1, 2, 3)
    kwargs = {"hello": "world"}

    mock(*args, **kwargs)
    mock(*args, **kwargs)

    e = expect(mock)
    with raises(ExpectationFailed):
        e.called_once_with(*args, **kwargs)

    hist = [
        Expected(
            mock,
            op="called_once_with",
            that=None,
            op_args=args,
            op_kwargs=kwargs,
            success=False,
        )
    ]
    expect(e.history).equals(hist)


@test("called_once_with records history and raises when multiple calls made")
def _(mock=mock):
    args = (1, 2, 3)
    kwargs = {"hello": "world"}

    mock(1)
    mock(*args, **kwargs)
    mock(2)

    e = expect(mock)
    with raises(ExpectationFailed):
        e.called_once_with(*args, **kwargs)

    hist = [
        Expected(
            mock,
            op="called_once_with",
            that=None,
            op_args=args,
            op_kwargs=kwargs,
            success=False,
        )
    ]
    expect(e.history).equals(hist)


@test("called_with records history when the expected call is the most recent one")
def _(mock=mock):
    mock(1)
    mock(2)

    e = expect(mock).called_with(2)
    expect(e.history[0].success).equals(True)


@test(
    "called_with records history and raises when expected call was made before other calls"
)
def _(mock=mock):
    mock(2)
    mock(1)
    e = expect(mock)
    with raises(ExpectationFailed):
        e.called_with(2)
    expect(e.history[0].success).equals(False)


@test("has_calls records history when all expected calls were made")
def _(mock=mock):
    mock(1, 2)
    mock(key="value")

    e = expect(mock).has_calls([call(1, 2), call(key="value")])
    expect(e.history[0].success).equals(True)


@test("has_calls records history and raises when not all expected calls were made")
def _(mock=mock):
    print(mock.call_args_list)
    mock(1, 2)

    e = expect(mock)
    with raises(ExpectationFailed):
        e.has_calls([call(1, 2), call(key="value")])
    expect(e.history[0].success).equals(False)


@test("has_calls raises when the expected calls were made in the wrong order")
def _(mock=mock):
    print(mock.call_args_list)
    mock(1, 2)
    mock(key="value")

    e = expect(mock)
    with raises(ExpectationFailed):
        e.has_calls([call(key="value"), call(1, 2)])


@test(
    "has_calls(any_order=True) records history when the calls were made in the wrong order"
)
def _(mock=mock):
    mock(1, 2)
    mock(key="value")

    e = expect(mock).has_calls([call(key="value"), call(1, 2)], any_order=True)

    expect(e.history[0].success).equals(True)
