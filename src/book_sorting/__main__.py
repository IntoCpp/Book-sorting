from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from book_sorting.config import ConfigError, get_openai_api_key, load_config, load_dotenv_file
from book_sorting.models.state import WorkflowState
from book_sorting.workflow.runner import WorkflowRunner


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )


def main(argv: list[str] | None = None) -> None:
    _configure_logging()
    parser = argparse.ArgumentParser(description="Book Sorting Tool")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config.yaml"),
        help="Path to project config.yaml",
    )
    args = parser.parse_args(argv)

    load_dotenv_file()
    api_key = get_openai_api_key()
    if api_key is None:
        logging.warning("OPENAI_API_KEY is not set; AI stages are stubbed in Step 1")

    try:
        config = load_config(args.config)
    except ConfigError as exc:
        logging.error("%s", exc)
        sys.exit(1)

    logging.info("Loaded config from %s", config.config_path)
    logging.info("Source folder: %s", config.source_folder)
    logging.info("Output folder: %s", config.output_folder)

    runner = WorkflowRunner()
    state = WorkflowState(config=config)
    final_state = runner.run(state)

    if final_state.report:
        print(final_state.report.message)


if __name__ == "__main__":
    main()
