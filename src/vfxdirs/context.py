from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping, TypeAlias

OSName: TypeAlias = Literal["windows", "macos", "linux"]


def _home_from_env(os_name: OSName, env: Mapping[str, str]) -> Path:
    # pref env values so tests can inject a fake env
    if os_name == "windows":
        value = env.get("USERPROFILE")
    else:
        value = env.get("HOME")
    return Path(value) if value else Path.home()


@dataclass(frozen=True, slots=True)
class Context:
    """Environment facts used during path resolution."""

    os: OSName
    env: Mapping[str, str]
    home: Path
    cwd: Path
    temp_dir: Path
    config_home: Path
    data_home: Path
    cache_home: Path
    install_roots: tuple[Path, ...]

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        *,  # force all following args to be keyword-only
        os_name: OSName | None = None,
        home: Path | None = None,
        cwd: Path | None = None,
    ) -> "Context":
        env_map: Mapping[str, str]
        if env is None:
            # TODO: is this stable enough for all callers?
            env_map = os.environ
        else:
            env_map = env


)
