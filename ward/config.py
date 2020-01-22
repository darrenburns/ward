from pathlib import Path
from typing import Dict, Union

import click
import toml


def read_config_toml(
    project_root: Path, config_file: str
) -> Dict[str, Union[str, int]]:
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
