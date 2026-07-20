from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv
import os


@dataclass(frozen=True)
class AppConfig:
    source_folder: Path
    output_folder: Path
    config_path: Path


class ConfigError(Exception):
    pass


def _resolve_path(base_dir: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def load_config(config_path: Path | None = None) -> AppConfig:
    path = (config_path or Path("config.yaml")).resolve()
    if not path.is_file():
        raise ConfigError(f"Config file not found: {path}")

    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    source = data.get("source_folder")
    output = data.get("output_folder")
    if not source or not output:
        raise ConfigError("config.yaml must define source_folder and output_folder")

    base_dir = path.parent
    source_folder = _resolve_path(base_dir, str(source))
    output_folder = _resolve_path(base_dir, str(output))

    if not source_folder.is_dir():
        raise ConfigError(f"Source folder does not exist: {source_folder}")

    return AppConfig(
        source_folder=source_folder,
        output_folder=output_folder,
        config_path=path,
    )


def load_dotenv_file(env_path: Path | None = None) -> None:
    if env_path is None:
        load_dotenv()
        return
    load_dotenv(env_path)


def get_openai_api_key() -> str | None:
    load_dotenv()
    value = os.getenv("OPENAI_API_KEY")
    if value is None or not value.strip():
        return None
    return value.strip()
