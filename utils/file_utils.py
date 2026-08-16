"""
File and path management utilities for Chakma Historical OCR.
All path resolutions are relative to project root without hardcoded absolute paths.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Union
import yaml


def get_project_root() -> Path:
    """
    Get the absolute Path to the project root directory.
    Calculated relative to this file location (project_root/utils/file_utils.py).
    """
    return Path(__file__).resolve().parent.parent


def resolve_path(relative_or_absolute: Union[str, Path]) -> Path:
    """
    Resolve a given path relative to the project root if it is not already absolute.
    """
    path = Path(relative_or_absolute)
    if path.is_absolute():
        return path
    return get_project_root() / path


def ensure_dir(dir_path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, creating parents if necessary.
    """
    resolved = resolve_path(dir_path)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load YAML configuration file.
    """
    path = resolve_path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"YAML configuration file not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def save_yaml(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """
    Save dictionary to YAML configuration file.
    """
    path = resolve_path(file_path)
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)


def load_json(file_path: Union[str, Path]) -> Any:
    """
    Load JSON file.
    """
    path = resolve_path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, file_path: Union[str, Path], indent: int = 2) -> None:
    """
    Save object to formatted JSON file.
    """
    path = resolve_path(file_path)
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def read_text_lines(file_path: Union[str, Path], strip: bool = True) -> List[str]:
    """
    Read lines from a text file, filtering out comments starting with '#'.
    """
    path = resolve_path(file_path)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() if strip else line for line in f]
    return [l for l in lines if l and not l.startswith("#")]


def write_text_lines(lines: List[str], file_path: Union[str, Path]) -> None:
    """
    Write a list of strings as lines to a text file.
    """
    path = resolve_path(file_path)
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(f"{line}\n")
