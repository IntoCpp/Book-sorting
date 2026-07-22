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
    output = tmp_path / "output_prod_data"
    output.mkdir()
    config_file = tmp_path / "config.yaml"
    config_file.write_text("output_folder_prod: ./output_prod_data\n", encoding="utf-8")

    config_path, output_folder = load_output_folder_prod(config_file)

    assert config_path == config_file.resolve()
    assert output_folder == output.resolve()


def test_get_openai_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    assert get_openai_api_key() == "test-key"


def test_get_openai_api_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(
        "book_sorting.config.load_dotenv",
        lambda *args, **kwargs: None,
    )
    assert get_openai_api_key() is None
