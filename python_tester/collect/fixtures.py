class FixtureRegistry:
    def __init__(self):
        self._fixtures = {}

        def wrapper(func):
            self._fixtures[func.__name__] = func
            return func

        self._wrapper = wrapper

    @property
    def decorator(self):
        return self._wrapper

    def get_all(self):
        return self._fixtures


fixture_registry = FixtureRegistry()
fixture = fixture_registry.decorator
