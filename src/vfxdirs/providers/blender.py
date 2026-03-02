from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..context import Context
from ..keys import DirKey, KeyLike, normalize_key


@dataclass(frozen=True, slots=True)
class BlenderProvider:
    """App provider for Blender."""

    id: str = "blender"
    display_name: str = "Blender"

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

    def _version_dir(self, ctx: Context, version: str | None) -> Path:
        """Return the per-version user directory.

        - Linux:   ~/.config/blender/<version>/
        - macOS:   ~/Library/Application Support/Blender/<version>/
        - Windows: %APPDATA%/Blender Foundation/Blender/<version>/
        """
        if ctx.os == "linux":
            base = ctx.config_home / "blender"
        elif ctx.os == "macos":
            base = ctx.config_home / "Blender"
        else:  # windows
            base = ctx.config_home / "Blender Foundation" / "Blender"
        return base / version if version else base

    def path(self, key: KeyLike, ctx: Context, *, version: str | None = None) -> Path:
        k = normalize_key(key)
        version_dir = self._version_dir(ctx, version)

        if k in (DirKey.PREFS, DirKey.CONFIG):
            return version_dir / "config"
        if k == DirKey.SCRIPTS:
            return version_dir / "scripts"
        if k == DirKey.PLUGINS:
            # extensions/ in Blender 4.x, addons/ in older versions; both live here
            return version_dir / "extensions"
        if k == DirKey.DATA:
            return version_dir / "datafiles"
        if k == DirKey.CACHE:
            return ctx.cache_home / "blender"
        if k == DirKey.TEMP:
            return ctx.temp_dir / "blender"

        raise KeyError(f"Unsupported key {key!r} for {self.display_name}")
