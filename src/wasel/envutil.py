"""Environment lookups for code that runs outside `Settings` (the LLM layer, prompt registry, tracing, scoring config).

A value is taken from the process environment first, then from the `.env` file that `Settings` reads, so `make run`,
a bare `uvicorn`, `make eval-live` and the scripts see the same `.env` as `make up` and `make serve`. The file is the
one named by `Settings.model_config["env_file"]`; tests set it to None, which disables the fallback.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values


@lru_cache(maxsize=4)
def _dotenv(path: str) -> dict[str, str]:
    p = Path(path)
    return {k: v for k, v in dotenv_values(p).items() if v is not None} if p.is_file() else {}


def env(name: str, default: str | None = None) -> str | None:
    """`name` from the process environment, else from `.env` (relative to the working directory), else `default`.

    An empty value in either place counts as unset for the purpose of falling through to the next source.
    """
    v = os.environ.get(name)
    if v:
        return v
    from wasel.settings import Settings
    f = Settings.model_config.get("env_file")
    if f:
        v = _dotenv(str(f)).get(name)
        if v:
            return v
    return default
