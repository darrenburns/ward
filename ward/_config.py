from pathlib import Path
from typing import Dict, Iterable, Optional, Union

import click
import tomli

from ward._utilities import find_project_root

_ConfigValue = Union[int, str, bool, Iterable[str]]
_ConfigDict = Dict[str, _ConfigValue]

_CONFIG_FILE = "pyproject.toml"


def _breakpoint_supported() -> bool:
    try:
        breakpoint
    except NameError:
        return False
    return True


def read_config_toml(project_root: Path, config_file: str) -> _ConfigDict:
    path = project_root / config_file
    if not path.is_file():
        return {}

    try:
        pyproject_toml = tomli.loads(path.read_text(encoding="utf-8"))
    except (tomli.TOMLDecodeError, OSError) as e:
        raise click.FileError(
            filename=config_file, hint=f"Error reading {config_file}:\n{e}"
        )

    ward_config = pyproject_toml.get("tool", {}).get("ward", {})
    ward_config = {
        k.replace("--", "").replace("-", "_"): v for k, v in ward_config.items()
    }

    return ward_config


def as_list(conf: _ConfigValue):
    if isinstance(conf, list):
        return conf
    else:
        return [conf]


def apply_multi_defaults(
    file_config: _ConfigDict,
    cli_config: _ConfigDict,
) -> _ConfigDict:
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

    # TODO: Can we retrieve the tuple below programmatically?
    multiple_options = ("exclude", "hook_module")
    for param in multiple_options:
        from_cli = cli_config.get(param)
        from_conf_file = file_config.get(param, "")
        if from_conf_file and not from_cli:
            file_config_only[param] = as_list(from_conf_file)

    return file_config_only


def set_defaults_from_config(
    context: click.Context,
    param: click.Parameter,
    value: Union[str, int],
) -> Optional[Path]:
    paths_supplied_via_cli = context.params.get("path")

    search_paths = paths_supplied_via_cli
    if not search_paths:
        search_paths = (".",)

    if not context.default_map:
        context.default_map = {"path": (".",)}

    project_root = find_project_root([Path(path) for path in search_paths])
    if project_root:
        context.params["project_root"] = project_root
    else:
        context.params["project_root"] = None
        context.params["config_path"] = None
        return Path.cwd()

    file_config = read_config_toml(project_root, _CONFIG_FILE)

    if file_config:
        config_path: Optional[Path] = project_root / _CONFIG_FILE
    else:
        config_path = None

    context.params["config_path"] = config_path

    multi_defaults = apply_multi_defaults(file_config, context.params)
    file_config.update(multi_defaults)

    # Paths supplied via the CLI should be treated as relative to pwd
    # However, paths supplied via the pyproject.toml should be relative
    # to the directory that file is contained in.
    path_config_keys = ["path", "exclude"]
    for conf_key, paths in file_config.items():
        if conf_key in path_config_keys:
            assert isinstance(paths, list), 'value of "path" and "exclude" must be list'
            relative_path_strs = []
            for path_str in paths:
                relative_path_strs.append(str((project_root / path_str)))
            file_config[conf_key] = tuple(relative_path_strs)

    context.default_map.update(file_config)

    return config_path
