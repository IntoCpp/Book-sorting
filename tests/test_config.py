"""Tests for configuration loading and OpenAI API key resolution."""

from pathlib import Path

import pytest

from book_sorting.config import ConfigError, get_openai_api_key, load_config, load_output_folder_prod


def _write_config_file(config_file: Path, **overrides: str) -> None:
    values = {
        "source_folder_test": "./input_test_data",
        "output_folder_test": "./output_test_data",
        "source_folder_prod": "./input_prod_data",
        "output_folder_prod": "./output_prod_data",
        "processing_history_test": "processing_history_test.json",
        "processing_history_prod": "processing_history_prod.json",
    }
    values.update(overrides)
    lines = [f"{key}: {value}" for key, value in values.items()]
    config_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_load_config_test_mode_resolves_paths(tmp_path: Path) -> None:
    """Verify test-mode config resolves relative paths to absolute paths.

    Goal: Confirm ``load_config`` with ``test_mode=True`` resolves source,
    output, and history paths relative to the config file location.
    Expected result: ``test_mode`` is ``True`` and all folder paths match
    resolved ``tmp_path`` subdirectories.
    On Failure: Path resolution logic or test-mode key names changed.
    """
    source = tmp_path / "input_test_data"
    output = tmp_path / "output_test_data"
    source.mkdir()
    output.mkdir()

    config_file = tmp_path / "config.yaml"
    _write_config_file(
        config_file,
        source_folder_test="./input_test_data",
        output_folder_test="./output_test_data",
    )

    config = load_config(config_file, test_mode=True)
    assert config.test_mode is True
    assert config.source_folder == source.resolve()
    assert config.output_folder == output.resolve()
    assert config.processing_history_path == (tmp_path / "processing_history_test.json").resolve()


def test_load_config_production_mode_resolves_paths(tmp_path: Path) -> None:
    """Verify production-mode config resolves prod folder paths.

    Goal: Confirm ``load_config`` with ``test_mode=False`` uses production
    source, output, and history keys.
    Expected result: ``test_mode`` is ``False`` and prod paths resolve
    correctly under ``tmp_path``.
    On Failure: Production config keys or path resolution logic changed.
    """
    source = tmp_path / "input_prod_data"
    output = tmp_path / "output_prod_data"
    source.mkdir()
    output.mkdir()

    config_file = tmp_path / "config.yaml"
    _write_config_file(config_file)

    config = load_config(config_file, test_mode=False)
    assert config.test_mode is False
    assert config.source_folder == source.resolve()
    assert config.output_folder == output.resolve()
    assert config.processing_history_path == (tmp_path / "processing_history_prod.json").resolve()


def test_load_config_missing_source_raises(tmp_path: Path) -> None:
    """Verify loading config with a missing source folder raises ConfigError.

    Goal: Confirm ``load_config`` validates that the configured source
    folder exists before returning an ``AppConfig``.
    Expected result: ``ConfigError`` raised with message containing
    ``Source folder does not exist``.
    On Failure: Source-folder validation was removed or error message changed.
    """
    config_file = tmp_path / "config.yaml"
    _write_config_file(
        config_file,
        source_folder_test="./missing",
        output_folder_test="./output_test_data",
    )
    (tmp_path / "output_test_data").mkdir()

    with pytest.raises(ConfigError, match="Source folder does not exist"):
        load_config(config_file, test_mode=True)


def test_load_output_folder_prod(tmp_path: Path) -> None:
    """Verify ``load_output_folder_prod`` returns config and output paths.

    Goal: Confirm the helper loads only the production output folder from a
    minimal config file.
    Expected result: Resolved config path and output folder path returned.
    On Failure: ``load_output_folder_prod`` signature or YAML key changed.
    """
    output = tmp_path / "output_prod_data"
    output.mkdir()
    config_file = tmp_path / "config.yaml"
    config_file.write_text("output_folder_prod: ./output_prod_data\n", encoding="utf-8")

    config_path, output_folder = load_output_folder_prod(config_file)

    assert config_path == config_file.resolve()
    assert output_folder == output.resolve()


def test_get_openai_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify OpenAI API key is read from the environment variable.

    Goal: Confirm ``get_openai_api_key`` returns ``OPENAI_API_KEY`` when set.
    Expected result: Function returns ``"test-key"`` from the environment.
    On Failure: Environment variable name or lookup order changed.
    """
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    assert get_openai_api_key() == "test-key"


def test_get_openai_api_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify missing OpenAI API key returns None when dotenv finds nothing.

    Goal: Confirm ``get_openai_api_key`` returns ``None`` when the env var
    is unset and ``load_dotenv`` provides no value.
    Expected result: Function returns ``None``.
    On Failure: Fallback lookup via dotenv or file still supplies a key.
    """
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(
        "book_sorting.config.load_dotenv",
        lambda *args, **kwargs: None,
    )
    assert get_openai_api_key() is None
