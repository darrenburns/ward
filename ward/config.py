from pathlib import Path
from typing import Dict, Union, Iterable

import click
import toml

from ward.util import find_project_root

ConfigValue = Union[int, str, bool, Iterable[str]]
Config = Dict[str, ConfigValue]

CONFIG_FILE = "pyproject.toml"


def read_config_toml(project_root: Path, config_file: str) -> Config:
    path = project_root / config_file
    if not path.is_file():
        return {}

    try:
        pyproject_toml = toml.load(str(path))
        config = pyproject_toml.get("tool", {}).get("ward", {})
    except (toml.TomlDecodeError, OSError) as e:
        raise click.FileError(
            filename=config_file, hint=f"Error reading {config_file}:\n{e}"
        )

    if not config:
        return {}

    config = {k.replace("--", "").replace("-", "_"): v for k, v in config.items()}
    return config


def as_list(conf: Config):
    if isinstance(conf, list):
        return conf
    else:
        return [conf]


def apply_multi_defaults(file_config: Config, cli_config: Config,) -> Config:
    """
    Returns all options where multiple=True that
    appeared in the config file, but weren't passed
    via the command line.
    """

    cli_paths = cli_config.get("path")
    conf_file_paths = file_config.get("path", ".")
    file_config_only = {}
    if conf_file_paths and not cli_paths:
        file_config_only["path"] = as_list(conf_file_paths)

    # TODO: Can we retrieve the list below programmatically?
    multiple_options = ("exclude",)
    for param in multiple_options:
        from_cli = cli_config.get(param)
        from_conf_file = file_config.get(param, "")
        if from_conf_file and not from_cli:
            file_config_only[param] = as_list(from_conf_file)

    return file_config_only


def set_defaults_from_config(
    context: click.Context, param: click.Parameter, value: Union[str, int],
) -> Path:
    supplied_paths = context.params.get("path")

    search_paths = supplied_paths
    if not search_paths:
        search_paths = (".",)

    project_root = find_project_root([Path(path) for path in search_paths])
    file_config = read_config_toml(project_root, CONFIG_FILE)
    if file_config:
        config_path = project_root / "pyproject.toml"
    else:
        config_path = None
    context.params["config_path"] = config_path
    file_config = apply_multi_defaults(file_config, context.params)

    if context.default_map is None:
        context.default_map = {}

    context.default_map.update(file_config)
    return project_root
