from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from .context import Context
from .keys import DirKey, KeyLike, normalize_key


@runtime_checkable
class VFXApp(Protocol):
    """Protocol implemented by app providers"""

    id: str
    display_name: str

    def supported_keys(self) -> set[DirKey]:
        """Return the set of `DirKey`s this app provider can resolve."""

    def path(self, key: KeyLike, ctx: Context, *, version: str | None = None) -> Path:
        """Resolve a directory path for the given key and context."""


@dataclass(frozen=True, slots=True)
class AppDirs:
    """Key-based directory access to a single app."""

    provider: VFXApp
    ctx: Context
    version: str | None = None

    @property
    def app_id(self) -> str:
        return self.provider.id

    def path(self, key: KeyLike) -> Path:
        return self.provider.path(normalize_key(key), self.ctx, version=self.version)

    def paths(self) -> dict[DirKey, Path]:
        return {k: self.path(k) for k in self.provider.supported_keys()}
