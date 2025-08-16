from __future__ import annotations

import io
from typing import Iterable, Optional

import pandas as pd


PREFERRED_ENCODINGS = (
    "utf-8",
    "utf-8-sig",
    "cp1252",  # common on Windows
    "latin-1",
)


def read_csv_smart(path: str, usecols: Optional[Iterable[str]] = None) -> pd.DataFrame:
    """Read CSV robustly by trying multiple encodings and falling back to replacement.

    Tries utf-8, utf-8-sig, cp1252, latin-1. If all fail, decodes bytes with
    errors='replace' and parses via a StringIO buffer.
    """
    last_err: Exception | None = None
    for enc in PREFERRED_ENCODINGS:
        try:
            return pd.read_csv(path, usecols=usecols, encoding=enc, engine="python")
        except Exception as e:  # try next encoding
            last_err = e
            continue
    # Final fallback: decode with replacement and parse
    try:
        with open(path, "rb") as f:
            data = f.read().decode("utf-8", errors="replace")
        return pd.read_csv(io.StringIO(data), usecols=usecols, engine="python")
    except Exception:
        if last_err:
            raise last_err
        raise

