from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..context import Context
from ..keys import DirKey, KeyLike, normalize_key


@dataclass(frozen=True, slots=True)
class MayaProvider:
    """App provider for Autodesk Maya."""

    id: str = "maya"
    display_name: str = "Autodesk Maya"

    def supported_keys(self) -> set[DirKey]:
        return {
            DirKey.PREFS,
            DirKey.SCRIPTS,
            DirKey.PLUGINS,
            DirKey.PACKAGES,
            DirKey.DATA,
            DirKey.CACHE,
            DirKey.LOGS,
            DirKey.TEMP,
        }

    def _user_dir(self, ctx: Context, version: str | None) -> Path:
        """Return the Maya user preferences directory (versioned or root)."""
        if ctx.os == "linux":
            base = ctx.home / "maya"
        elif ctx.os == "macos":
            base = ctx.home / "Library" / "Preferences" / "Autodesk" / "maya"
        else:  # windows
            base = ctx.home / "Documents" / "maya"
        return base / version if version else base

    def path(self, key: KeyLike, ctx: Context, *, version: str | None = None) -> Path:
        k = normalize_key(key)
        user_dir = self._user_dir(ctx, version)

        if k == DirKey.PREFS:
            return user_dir / "prefs"
        if k == DirKey.SCRIPTS:
            return user_dir / "scripts"
        if k == DirKey.PLUGINS:
            return user_dir / "plug-ins"
        if k == DirKey.DATA:
            return user_dir
        if k == DirKey.CACHE:
            if ctx.os == "macos":
                cache = ctx.cache_home / "Autodesk" / "Maya"
                return cache / version if version else cache
            return user_dir / "cache"
        if k == DirKey.LOGS:
            if ctx.os == "macos":
                return ctx.home / "Library" / "Logs" / "Autodesk" / "Maya"
            return user_dir / "logs"
        if k == DirKey.TEMP:
            return ctx.temp_dir / "maya"
        if k == DirKey.PACKAGES:
            # modules live under the version-independent root
            return self._user_dir(ctx, None) / "modules"

        raise KeyError(f"Unsupported key {key!r} for {self.display_name}")
