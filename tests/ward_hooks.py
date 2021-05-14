from ward.hooks import hook


@hook
def before_session(config):
    print('inside before_session')
