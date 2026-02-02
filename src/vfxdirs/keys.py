from __future__ import annotations

from enum import StrEnum
from typing import TypeAlias


class DirKey(StrEnum):
    """Common per-application directory "kinds".

    This is intentionally small and shared across many DCCs. Individual apps may
    support only a subset. Callers may also pass custom string keys to API's.
    """

    PREFS = "prefs"
    CONFIG = "config"
    DATA = "data"
    CACHE = "cache"
    LOGS = "logs"
    TEMP = "temp"
    SCRIPTS = "scripts"
    PLUGINS = "plugins"
    PACKAGES = "packages"


KeyLike: TypeAlias = DirKey | str


def normalize_key(key: KeyLike) -> KeyLike:
    """Normalize a key to a `DirKey` when possible.

    - `DirKey` inputs are returned as-is.
    - String inputs are trimmed and case-normalized.
    - If the normalized string matches a `DirKey` value, the corresponding
      `DirKey` is returned; otherwise the normalized string is returned.
    """

    if isinstance(key, DirKey):
        return key
    if not isinstance(key, str):
        raise TypeError(
            f"key must be a DirKey or str, got {type(key).__name__}")

    raw = key.strip()
    if not raw:
        raise ValueError("key cannot be empty")

    raw_lower = raw.lower()
    try:
        return DirKey(raw_lower)
    except ValueError:
        return raw_lower
