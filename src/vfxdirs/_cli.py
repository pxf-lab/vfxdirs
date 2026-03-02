from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, NoReturn

from . import DEFAULT_REGISTRY
from .api import VFXDirs
from .config import default_config_path
from .context import Context


def _die(msg: str) -> NoReturn:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def _vfxdirs() -> VFXDirs:
    return VFXDirs.from_default_config(registry=DEFAULT_REGISTRY)


# ── commands ──────────────────────────────────────────────────────────────────


def _cmd_path(args: argparse.Namespace) -> None:
    vd = _vfxdirs()
    try:
        resolved = vd.app(args.app, version=args.version).path(args.key)
    except KeyError as exc:
        _die(exc.args[0])
    if args.raw:
        print(resolved)
    else:
        print(f"{args.app} {args.key}: {resolved}")


def _cmd_paths(args: argparse.Namespace) -> None:
    vd = _vfxdirs()
    try:
        app_dirs = vd.app(args.app, version=args.version)
    except KeyError as exc:
        _die(exc.args[0])
    ver = app_dirs.effective_version
    print(f"{args.app}  {ver}" if ver else args.app)
    resolved = app_dirs.paths()
    if resolved:
        width = max(len(str(k)) for k in resolved)
        for key, p in sorted(resolved.items(), key=lambda kv: str(kv[0])):
            print(f"  {str(key):<{width}}  {p}")


def _cmd_apps(_args: argparse.Namespace) -> None:
    for app_id in _vfxdirs().registered_apps():
        print(app_id)


def _cmd_keys(args: argparse.Namespace) -> None:
    vd = _vfxdirs()
    try:
        app_dirs = vd.app(args.app)
    except KeyError as exc:
        _die(exc.args[0])
    for key in sorted(app_dirs.provider.supported_keys(), key=str):
        print(key)


# ── config helpers ────────────────────────────────────────────────────────────

# Fields that live directly under [apps.<id>] (string scalars)
_APP_SCALARS = {"version", "base"}
# Fields that live under [apps.<id>.install]
_INSTALL_FIELDS = {"root", "executable"}


def _parse_setting(setting: str) -> tuple[str, list[str]] | None:
    """Parse a dotted setting key into (app_id, key_path).

    Valid forms:
      <app>.<scalar>            e.g. maya.version
      <app>.install.<field>     e.g. maya.install.root
      <app>.paths.<key>         e.g. maya.paths.scripts
    """
    parts = setting.split(".")
    if len(parts) < 2:
        return None
    app_id, rest = parts[0], parts[1:]
    if len(rest) == 1 and rest[0] in _APP_SCALARS:
        return app_id, rest
    if len(rest) == 2:
        if rest[0] == "install" and rest[1] in _INSTALL_FIELDS:
            return app_id, rest
        if rest[0] == "paths" and rest[1]:
            return app_id, rest
    return None


def _load_raw(cfg_path: Path) -> dict[str, Any]:
    if cfg_path.exists():
        data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
        data.setdefault("apps", {})
        return data
    return {"apps": {}}


def _write_toml(data: dict[str, Any], cfg_path: Path) -> None:
    """Serialise config data to TOML. Only handles the vfxdirs config schema."""
    lines: list[str] = []
    for app_id in sorted(data.get("apps", {})):
        app: dict[str, Any] = data["apps"][app_id]

        # scalar fields ([apps.<id>])
        scalars = {k: v for k, v in app.items()
                   if k not in ("install", "paths") and v is not None}
        if scalars:
            if lines:
                lines.append("")
            lines.append(f"[apps.{app_id}]")
            for k, v in scalars.items():
                lines.append(f'{k} = "{v}"')

        # install subtable
        install = {k: v for k, v in (app.get("install") or {}).items()
                   if v is not None}
        if install:
            if lines:
                lines.append("")
            lines.append(f"[apps.{app_id}.install]")
            for k, v in install.items():
                lines.append(f'{k} = "{v}"')

        # paths subtable
        paths = {k: v for k, v in (app.get("paths") or {}).items()
                 if v is not None}
        if paths:
            if lines:
                lines.append("")
            lines.append(f"[apps.{app_id}.paths]")
            for k, v in sorted(paths.items()):
                lines.append(f'{k} = "{v}"')

    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── config commands ───────────────────────────────────────────────────────────


def _cmd_config_path(_args: argparse.Namespace) -> None:
    print(default_config_path(Context.from_env()))


def _cmd_config_show(_args: argparse.Namespace) -> None:
    cfg_path = default_config_path(Context.from_env())
    if not cfg_path.exists():
        print(f"no config file at {cfg_path}", file=sys.stderr)
        return
    print(cfg_path.read_text(encoding="utf-8"), end="")


def _cmd_config_set(args: argparse.Namespace) -> None:
    parsed = _parse_setting(args.setting)
    if parsed is None:
        _die(
            f"unknown setting {args.setting!r}. "
            "Use <app>.<field>, <app>.install.<field>, or <app>.paths.<key>"
        )
    app_id, key_path = parsed
    cfg_path = default_config_path(Context.from_env())
    data = _load_raw(cfg_path)
    app_data: dict[str, Any] = data["apps"].setdefault(app_id, {})
    if len(key_path) == 1:
        app_data[key_path[0]] = args.value
    elif key_path[0] == "install":
        app_data.setdefault("install", {})[key_path[1]] = args.value
    else:  # paths
        app_data.setdefault("paths", {})[key_path[1]] = args.value
    _write_toml(data, cfg_path)
    print(f"set {args.setting} = {args.value!r}")


def _cmd_config_edit(_args: argparse.Namespace) -> None:
    ctx = Context.from_env()
    cfg_path = default_config_path(ctx)
    if not cfg_path.exists():
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text("", encoding="utf-8")
    default_editor = "notepad" if ctx.os == "windows" else "nano"
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR") or default_editor
    subprocess.run(shlex.split(editor) + [str(cfg_path)])


# ── parser ────────────────────────────────────────────────────────────────────


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vfxdirs",
        description="Resolve directory paths for common VFX software.",
    )
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("path", help="resolve a single directory path")
    p.add_argument("app", help="app id, e.g. maya")
    p.add_argument("key", help="directory key, e.g. scripts")
    p.add_argument("--version", "-v", metavar="VERSION")
    p.add_argument("--raw", action="store_true", help="print bare path with no label")
    p.set_defaults(func=_cmd_path)

    p = sub.add_parser("paths", help="show all paths for an app")
    p.add_argument("app", help="app id")
    p.add_argument("--version", "-v", metavar="VERSION")
    p.set_defaults(func=_cmd_paths)

    p = sub.add_parser("apps", help="list registered app ids")
    p.set_defaults(func=_cmd_apps)

    p = sub.add_parser("keys", help="list supported directory keys for an app")
    p.add_argument("app", help="app id")
    p.set_defaults(func=_cmd_keys)

    cfg = sub.add_parser("config", help="manage the vfxdirs config file")

    def _config_help(_args: argparse.Namespace) -> None:
        cfg.print_help()

    cfg.set_defaults(func=_config_help)
    cfg_sub = cfg.add_subparsers(dest="config_command")

    p = cfg_sub.add_parser("path", help="print config file location")
    p.set_defaults(func=_cmd_config_path)

    p = cfg_sub.add_parser("show", help="print current config file contents")
    p.set_defaults(func=_cmd_config_show)

    p = cfg_sub.add_parser("set", help="set a config value")
    p.add_argument("setting", help="dotted key, e.g. maya.version or maya.paths.scripts")
    p.add_argument("value", help="value to set")
    p.set_defaults(func=_cmd_config_set)

    p = cfg_sub.add_parser("edit", help="open config file in $EDITOR")
    p.set_defaults(func=_cmd_config_edit)

    return parser


def main() -> None:
    parser = _make_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)
