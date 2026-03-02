from __future__ import annotations

import argparse
import sys
from typing import NoReturn

from . import DEFAULT_REGISTRY
from .api import VFXDirs


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

    return parser


def main() -> None:
    parser = _make_parser()
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return
    args.func(args)
