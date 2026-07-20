from pathlib import Path

import pytest

from book_sorting.config import ConfigError, get_openai_api_key, load_config


def test_load_config_resolves_paths(tmp_path: Path) -> None:
    source = tmp_path / "input"
    output = tmp_path / "output"
    source.mkdir()
    output.mkdir()

    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        f"source_folder: {source}\noutput_folder: {output}\n",
        encoding="utf-8",
    )

    config = load_config(config_file)
    assert config.source_folder == source.resolve()
    assert config.output_folder == output.resolve()


def test_load_config_relative_to_config_directory(tmp_path: Path) -> None:
    source = tmp_path / "input_test_data"
    output = tmp_path / "output_test_data"
    source.mkdir()
    output.mkdir()

    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "source_folder: ./input_test_data\noutput_folder: ./output_test_data\n",
        encoding="utf-8",
    )

    config = load_config(config_file)
    assert config.source_folder == source.resolve()
    assert config.output_folder == output.resolve()


def test_load_config_missing_source_raises(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        "source_folder: ./missing\noutput_folder: ./out\n",
        encoding="utf-8",
    )
    (tmp_path / "out").mkdir()

    with pytest.raises(ConfigError, match="Source folder does not exist"):
        load_config(config_file)


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
