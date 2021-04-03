from click.testing import CliRunner

from ward import each, test
from ward.run import run


@test("Cannot use bar progress style with {output_style} output style")
def _(output_style=each("dots-global", "dots-module")):
    runner = CliRunner()
    result = runner.invoke(
        run, ["test", "--progress-style", "bar", "--test-output-style", output_style]
    )

    assert result.exit_code == 2
