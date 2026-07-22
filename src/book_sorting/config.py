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
    processing_history_path: Path
    config_path: Path
    test_mode: bool = False


class ConfigError(Exception):
    pass


def _resolve_path(base_dir: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def _required_config_value(data: dict, *, test_mode: bool, test_key: str, prod_key: str) -> str:
    key = test_key if test_mode else prod_key
    value = data.get(key)
    if not value:
        raise ConfigError(f"config.yaml must define {key}")
    return str(value)


def load_output_folder_prod(config_path: Path | None = None) -> tuple[Path, Path]:
    """Return the config file path and resolved production output folder."""
    path = (config_path or Path("config.yaml")).resolve()
    if not path.is_file():
        raise ConfigError(f"Config file not found: {path}")

    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    output = data.get("output_folder_prod")
    if not output:
        raise ConfigError("config.yaml must define output_folder_prod")

    output_folder = _resolve_path(path.parent, str(output))
    if not output_folder.is_dir():
        raise ConfigError(f"Output folder does not exist: {output_folder}")

    return path, output_folder


def load_config(config_path: Path | None = None, *, test_mode: bool = False) -> AppConfig:
    path = (config_path or Path("config.yaml")).resolve()
    if not path.is_file():
        raise ConfigError(f"Config file not found: {path}")

    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    source = _required_config_value(
        data,
        test_mode=test_mode,
        test_key="source_folder_test",
        prod_key="source_folder_prod",
    )
    output = _required_config_value(
        data,
        test_mode=test_mode,
        test_key="output_folder_test",
        prod_key="output_folder_prod",
    )
    history_name = _required_config_value(
        data,
        test_mode=test_mode,
        test_key="processing_history_test",
        prod_key="processing_history_prod",
    )

    base_dir = path.parent
    source_folder = _resolve_path(base_dir, source)
    output_folder = _resolve_path(base_dir, output)
    processing_history_path = _resolve_path(base_dir, history_name)

    if not source_folder.is_dir():
        raise ConfigError(f"Source folder does not exist: {source_folder}")

    return AppConfig(
        source_folder=source_folder,
        output_folder=output_folder,
        processing_history_path=processing_history_path,
        config_path=path,
        test_mode=test_mode,
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
