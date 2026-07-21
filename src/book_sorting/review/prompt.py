from __future__ import annotations

import sys
from collections.abc import Callable

PromptYesNo = Callable[[str], bool]


def _stdin_prompt_yes_no(message: str) -> bool:
    while True:
        answer = input(f"{message} [y/n]: ").strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please enter y or n.", file=sys.stderr)


_prompt_yes_no: PromptYesNo = _stdin_prompt_yes_no


def prompt_yes_no(message: str) -> bool:
    return _prompt_yes_no(message)


def set_prompt_yes_no(handler: PromptYesNo) -> None:
    global _prompt_yes_no
    _prompt_yes_no = handler


def reset_prompt_yes_no() -> None:
    set_prompt_yes_no(_stdin_prompt_yes_no)
