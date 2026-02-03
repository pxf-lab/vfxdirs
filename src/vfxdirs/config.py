from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from .context import Context
from .keys import DirKey, KeyLike, normalize_key


class VFXDirsConfigError(ValueError):
    """Raised when config TOML cannot be parsed/validated."""


_ENV_VAR_PATTERN = re.compile(r"\$(\w+)|\$\{([^}]+)\}")


def default_config_path(ctx: Context) -> Path:
    """Return the OS-appropriate default config file path."""

    return ctx.config_home / "vfxdirs" / "config.toml"


def _expand_env_vars(value: str, env: Mapping[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        var = match.group(1) or match.group(2)
        if not var:
            return match.group(0)
        return env.get(var, match.group(0))

    return _ENV_VAR_PATTERN.sub(repl, value)


def _expand_user(value: str, home: Path) -> str:
    # pass home to make tests easier
    if value == "~":
        return str(home)
    if value.startswith("~/") or value.startswith("~\\"):
        return str(home) + value[1:]
    return value


def _parse_path(
    raw: Any,
    *,
    env: Mapping[str, str],
    home: Path,
    base_dir: Path,
    where: str,
) -> Path:
    if not isinstance(raw, str):
        raise VFXDirsConfigError(
            f"{where} must be a string path but got {type(raw).__name__}")

    raw_str = raw.strip()
    if not raw_str:
        raise VFXDirsConfigError(f"{where} cannot be an empty path")

    expanded = _expand_user(raw_str, home)
    expanded = _expand_env_vars(expanded, env)
    p = Path(expanded)
    if not p.is_absolute():
        p = base_dir / p
    return p


@dataclass(frozen=True, slots=True)
class InstallOverride:
    root: Path | None = None
    executable: Path | None = None

    def merged(self, higher: "InstallOverride") -> "InstallOverride":
        return InstallOverride(
            root=higher.root if higher.root is not None else self.root,
            executable=higher.executable
            if higher.executable is not None
            else self.executable,
        )


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Per-app overrides."""

    base: Path | None = None
    install: InstallOverride = field(default_factory=InstallOverride)
    paths: Mapping[KeyLike, Path] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized: dict[KeyLike, Path] = {}
        for k, v in dict(self.paths).items():
            normalized[normalize_key(k)] = v
        object.__setattr__(self, "paths", MappingProxyType(normalized))

    def path_override(self, key: KeyLike) -> Path | None:
        return self.paths.get(normalize_key(key))

    def merged(self, higher: "AppConfig") -> "AppConfig":
        merged_paths = dict(self.paths)
        merged_paths.update(higher.paths)
        return AppConfig(
            base=higher.base if higher.base is not None else self.base,
            install=self.install.merged(higher.install),
            paths=merged_paths,
        )


def _parse_install_table(
    app_id: str,
    table: Any,
    *,
    env: Mapping[str, str],
    home: Path,
    base_dir: Path,
) -> InstallOverride:
    if table is None:
        return InstallOverride()
    if not isinstance(table, Mapping):
        raise VFXDirsConfigError(
            f"`apps.{app_id}.install` must be a TOML table or object"
        )

    install_root = None
    if "root" in table and table["root"] is not None:
        install_root = _parse_path(
            table["root"],
            env=env,
            home=home,
            base_dir=base_dir,
            where=f"apps.{app_id}.install.root",
        )

    install_exe = None
    if "executable" in table and table["executable"] is not None:
        install_exe = _parse_path(
            table["executable"],
            env=env,
            home=home,
            base_dir=base_dir,
            where=f"apps.{app_id}.install.executable",
        )

    return InstallOverride(root=install_root, executable=install_exe)


def _parse_paths_table(
    app_id: str,
    table: Any,
    *,
    env: Mapping[str, str],
    home: Path,
    base_dir: Path,
) -> dict[KeyLike, Path]:
    if table is None:
        return {}
    if not isinstance(table, Mapping):
        raise VFXDirsConfigError(
            f"`apps.{app_id}.paths` must be a TOML table or object"
        )

    paths: dict[KeyLike, Path] = {}
    for raw_key, raw_value in table.items():
        key: KeyLike = normalize_key(str(raw_key))
        paths[key] = _parse_path(
            raw_value,
            env=env,
            home=home,
            base_dir=base_dir,
            where=f"apps.{app_id}.paths.{raw_key}",
        )
    return paths


def _parse_app_config(
    app_id: str,
    table: Any,
    *,
    env: Mapping[str, str],
    ctx: Context,
    base_dir: Path,
) -> AppConfig:
    if not isinstance(table, Mapping):
        raise VFXDirsConfigError(
            f"`apps.{app_id}` must be a TOML table or object")

    base: Path | None = None
    if "base" in table and table["base"] is not None:
        base = _parse_path(
            table["base"],
            env=env,
            home=ctx.home,
            base_dir=base_dir,
            where=f"apps.{app_id}.base",
        )

    install = _parse_install_table(
        app_id,
        table.get("install"),
        env=env,
        home=ctx.home,
        base_dir=base_dir,
    )

    paths = _parse_paths_table(
        app_id,
        table.get("paths"),
        env=env,
        home=ctx.home,
        base_dir=base_dir,
    )

    return AppConfig(base=base, install=install, paths=paths)


@dataclass(frozen=True, slots=True)
class VFXDirsConfig:
    """Top-level configuration with per-app override tables."""

    apps: Mapping[str, AppConfig] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized: dict[str, AppConfig] = {}
        for app_id, cfg in dict(self.apps).items():
            norm_id = _normalize_app_id(app_id)
            normalized[norm_id] = cfg
        object.__setattr__(self, "apps", MappingProxyType(normalized))

    def app(self, app_id: str) -> AppConfig | None:
        return self.apps.get(_normalize_app_id(app_id))

    def path_override(self, app_id: str, key: KeyLike) -> Path | None:
        app_cfg = self.app(app_id)
        if app_cfg is None:
            return None
        return app_cfg.path_override(key)

    def merged(self, higher: "VFXDirsConfig | None") -> "VFXDirsConfig":
        """Return a new config where `higher` takes precedence over `self`."""

        if higher is None:
            return self

        merged_apps: dict[str, AppConfig] = dict(self.apps)
        for app_id, higher_app in higher.apps.items():
            lower_app = merged_apps.get(app_id)
            merged_apps[app_id] = (
                higher_app if lower_app is None else lower_app.merged(
                    higher_app)
            )
        return VFXDirsConfig(apps=merged_apps)

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        *,
        env: Mapping[str, str] | None = None,
        context: Context | None = None,
    ) -> "VFXDirsConfig":
        config_path = Path(path)
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
        return cls.from_mapping(
            data,
            base_dir=config_path.parent,
            env=env,
            context=context,
        )

    @classmethod
    def load(
        cls,
        path: str | Path,
        *,
        env: Mapping[str, str] | None = None,
        context: Context | None = None,
    ) -> "VFXDirsConfig | None":
        config_path = Path(path)
        if not config_path.exists():
            return None
        return cls.from_file(config_path, env=env, context=context)

    @classmethod
    def load_default(
        cls,
        ctx: Context,
        *,
        env: Mapping[str, str] | None = None,
    ) -> "VFXDirsConfig | None":
        return cls.load(default_config_path(ctx), env=env, context=ctx)

    @classmethod
    def from_mapping(
        cls,
        data: Mapping[str, Any],
        *,
        base_dir: Path,
        env: Mapping[str, str] | None = None,
        context: Context | None = None,
    ) -> "VFXDirsConfig":
        if not isinstance(data, Mapping):
            raise VFXDirsConfigError(
                "Config root must be a TOML table or object")

        ctx = context or Context.from_env(env)
        env_map = ctx.env if env is None else env

        raw_apps = data.get("apps", {})
        if raw_apps is None:
            raw_apps = {}
        if not isinstance(raw_apps, Mapping):
            raise VFXDirsConfigError(
                "`apps` must be a TOML table or object")

        apps: dict[str, AppConfig] = {}
        for raw_id, raw_tbl in raw_apps.items():
            app_id = _normalize_app_id(str(raw_id))
            apps[app_id] = _parse_app_config(
                app_id,
                raw_tbl,
                env=env_map,
                ctx=ctx,
                base_dir=base_dir,
            )

        return cls(apps=apps)


def _normalize_app_id(app_id: str) -> str:
    raw = app_id.strip().lower()
    if not raw:
        raise VFXDirsConfigError("app_id cannot be empty")
    return raw


def supported_app_keys(config: VFXDirsConfig, app_id: str) -> set[DirKey]:
    """Return the set of known `DirKey` overrides in config for `app_id`."""

    app_cfg = config.app(app_id)
    if app_cfg is None:
        return set()
    return {k for k in app_cfg.paths.keys() if isinstance(k, DirKey)}
