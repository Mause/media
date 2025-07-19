from datetime import date
from typing import Any

from pydantic import ValidatorFunctionWrapHandler

from ...providers.serpapi import HumanDate


class Handler(ValidatorFunctionWrapHandler):
    def __call__(self, a: Any, b: str | int | None = None) -> Any:
        return a


def test_human_date() -> None:
    hd = HumanDate()
    value = "March 31, 1999 (USA)"
    assert hd.tz_constraint_validator(value, Handler()) == date(1999, 3, 31)
