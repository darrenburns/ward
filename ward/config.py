from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from cucumber_tag_expressions.model import Expression

__all__ = ["Config"]


@dataclass
class Config:
    """Dataclass providing access to the user configuration that has been supplied to Ward"""

    config_path: Optional[Path]
    project_root: Optional[Path]
    path: Tuple[str]
    exclude: Tuple[str]
    search: Optional[str]
    tags: Optional[Expression]
    fail_limit: Optional[int]
    test_output_style: str
    order: str
    capture_output: bool
    show_slowest: int
    show_diff_symbols: bool
    dry_run: bool
    hook_module: Tuple[str]
    progress_style: Tuple[str]
    plugin_config: Dict[str, Dict[str, Any]]
