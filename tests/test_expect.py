from ward import expect
from ward.expect import Expected, ExpectationFailed


def test_approx_success_history_recorded():
    this, that, eps = 1.0, 1.01, 0.5

    e = expect(this).approx(that, epsilon=eps)

    hist = [
        Expected(
            this=this,
            op="approx",
            that=that,
            op_args=(),
            op_kwargs={"epsilon": eps},
            success=True,
        )
    ]
    expect(e.history).equals(hist)


def test_approx_failure_history_recorded():
    this, that, eps = 1.0, 1.01, 0.001

    # This will raise an ExpectationFailed, which would fail this test unless we catch it.
    e = expect(this)
    try:
        e.approx(that, eps)
    except ExpectationFailed:
        pass

    hist = [
        Expected(
            this=this,
            op="approx",
            that=that,
            op_args=(eps,),
            op_kwargs={},
            success=False,
        )
    ]

    expect(e.history).equals(hist)
