from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..context import Context
from ..keys import DirKey, KeyLike, normalize_key


@dataclass(frozen=True, slots=True)
class HoudiniProvider:
    """App provider for SideFX Houdini."""

    id: str = "houdini"
    display_name: str = "SideFX Houdini"

    def supported_keys(self) -> set[DirKey]:
        return {
            DirKey.PREFS,
            DirKey.CONFIG,
            DirKey.SCRIPTS,
            DirKey.PLUGINS,
            DirKey.PACKAGES,
            DirKey.DATA,
            DirKey.CACHE,
            DirKey.TEMP,
        }

    def _user_dir(self, ctx: Context, version: str | None) -> Path:
        """Return the Houdini user preferences directory.

        On Linux and macOS the version is embedded in the directory name
        (e.g. ~/houdini20.5). On Windows it lives under Documents.
        """
        name = f"houdini{version}" if version else "houdini"
        if ctx.os == "windows":
            return ctx.home / "Documents" / name
        return ctx.home / name

    def path(self, key: KeyLike, ctx: Context, *, version: str | None = None) -> Path:
        k = normalize_key(key)
        user_dir = self._user_dir(ctx, version)

        if k in (DirKey.PREFS, DirKey.CONFIG, DirKey.DATA):
            return user_dir
        if k == DirKey.SCRIPTS:
            return user_dir / "scripts"
        if k == DirKey.PLUGINS:
            # otls/ holds user-installed digital assets (the most common "plugin" format)
            return user_dir / "otls"
        if k == DirKey.PACKAGES:
            return user_dir / "packages"
        if k == DirKey.CACHE:
            return ctx.cache_home / "houdini"
        if k == DirKey.TEMP:
            return ctx.temp_dir / "houdini"

        raise KeyError(f"Unsupported key {key!r} for {self.display_name}")
