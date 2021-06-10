import random
from dataclasses import dataclass

from rich.markdown import Markdown
from rich.panel import Panel


@dataclass
class Tip:
    title: str
    text: str
    url_link: str = ""

    def __rich__(self):
        return Panel(
            Markdown(self.text),
            title=self.title,
            style="dim",
            expand=False,
        )


# TODO: Update anchors to use static Sphinx refs
TIPS = [
    Tip(
        title="Disabling these tips",
        text="Run Ward with `--no-tips`.",
    ),
    Tip(
        title="Random test order",
        text="Use `--order random` to shuffle tests before running them.",
        url_link="https://ward.readthedocs.io/en/latest/guide/"
        "running_tests.html#randomise-test-execution-order-with-order-random",
    ),
    Tip(
        title="Searching test code",
        text="Use `--search QUERY` to search test function bodies and run the matching tests.",
        url_link="https://ward.readthedocs.io/en/latest/guide/running_tests.html#loosely-search-for-tests-with-search",
    ),
    Tip(
        title="Configuration file",
        text="All Ward command line options can also be supplied in `pyproject.toml`.",
    ),
    Tip(
        title="Markdown descriptions",
        text="You can use basic Markdown syntax in test descriptions and it'll be rendered in the output by default.",
    ),
    Tip(
        title="Tagging tests",
        text="Tag tests with the `tags` argument of the `@test` decorator.",
        url_link="https://ward.readthedocs.io/en/latest/guide/"
        "running_tests.html#selecting-tagged-tests-with-tags",
    ),
    Tip(
        title="Detecting slow tests",
        text="Use `--show-slowest N` and to display the *N* slowest tests after the test session.",
        url_link="https://ward.readthedocs.io/en/latest/guide/"
        "running_tests.html#finding-slow-running-tests-with-show-slowest",
    ),
    Tip(
        title="Failing fast",
        text="Use `--fail-limit N` to stop the test session after *N* test failures.",
    ),
    Tip(
        title="Progress bars",
        text="Use `--progress-style bar` to display a progress bar during the test run.",
    ),
    Tip(
        title="Live updating terminal",
        text="Use `--test-output-style live` for dynamic, live-updating terminal output during the session.",
    ),
    Tip(
        title="Linking tests to issue trackers",
        text="Link your `@skip` and `@xfail` tests to issue trackers using `[link=URL]TEXT[/link]` syntax.",
    ),
]


def get_random_tip():
    random_index = random.randint(0, len(TIPS) - 1)
    return TIPS[random_index]
