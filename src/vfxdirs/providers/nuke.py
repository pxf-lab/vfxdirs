from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..context import Context
from ..keys import DirKey, KeyLike, normalize_key


@dataclass(frozen=True, slots=True)
class NukeProvider:
    """App provider for Foundry Nuke."""

    id: str = "nuke"
    display_name: str = "Foundry Nuke"

    def supported_keys(self) -> set[DirKey]:
        return {
            DirKey.PREFS,
            DirKey.CONFIG,
            DirKey.SCRIPTS,
            DirKey.PLUGINS,
            DirKey.DATA,
            DirKey.CACHE,
            DirKey.TEMP,
        }

    def _user_dir(self, ctx: Context) -> Path:
        """Return ~/.nuke, which is the single user directory for all Nuke data."""
        return ctx.home / ".nuke"

    def path(self, key: KeyLike, ctx: Context, *, version: str | None = None) -> Path:
        k = normalize_key(key)
        user_dir = self._user_dir(ctx)

        if k in (DirKey.PREFS, DirKey.CONFIG, DirKey.SCRIPTS, DirKey.DATA):
            return user_dir
        if k == DirKey.PLUGINS:
            return user_dir / "plugins"
        if k in (DirKey.CACHE, DirKey.TEMP):
            return ctx.temp_dir / "nuke"

        raise KeyError(f"Unsupported key {key!r} for {self.display_name}")
