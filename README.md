# vfxdirs
A Python library for accessing useful paths for common visual effects software on any operating system.

> [!IMPORTANT]
> This library is still in development. Not all paths are properly tested for all providers.

# Usage

## Quick start

```python
import vfxdirs

vd = vfxdirs.VFXDirs(registry=vfxdirs.DEFAULT_REGISTRY)

# resolve a single path
vd.path("houdini", "packages", version="20.5")
# → /home/user/houdini20.5/packages  (Linux)

# get all paths for an app at once
vd.app("maya", version="2025").paths()
# → {DirKey.PREFS: ..., DirKey.SCRIPTS: ..., ...}
```

The built-in registry includes providers for **Maya**, **Houdini**, **Nuke**, and **Blender**.

## Available directory keys

| Key | Meaning |
|---|---|
| `prefs` | User preferences |
| `config` | Configuration files |
| `data` | Application data |
| `cache` | Cached files |
| `logs` | Log files |
| `temp` | Temporary files |
| `scripts` | User scripts |
| `plugins` | Plugins / extensions |
| `packages` | Installed packages |

Not every app supports every key — check the provider's `supported_keys()` if needed.

## Setting versions via config file

Rather than passing `version=` on every call, set it once in the config file.

**Config file location**

| OS | Path |
|---|---|
| Linux | `~/.config/vfxdirs/config.toml` |
| macOS | `~/Library/Application Support/vfxdirs/config.toml` |
| Windows | `%APPDATA%\vfxdirs\config.toml` |

**Example config**

```toml
[apps.maya]
version = "2025"

[apps.houdini]
version = "20.5"
```

Load it automatically with `from_default_config`:

```python
vd = vfxdirs.VFXDirs.from_default_config(registry=vfxdirs.DEFAULT_REGISTRY)

vd.path("maya", "scripts")   # uses version "2025" from config
vd.path("maya", "scripts", version="2024")  # explicit version wins
```

## Overriding individual paths

Any path can be overridden per-app in the config file:

```toml
[apps.maya.paths]
scripts = "/studio/shared/maya/scripts"
plugins = "~/maya/custom-plugins"
```

Environment variables and `~` are expanded:

```toml
[apps.houdini.paths]
packages = "$STUDIO_ROOT/houdini/packages"
```

## One-shot convenience function

```python
from vfxdirs import path

scripts = path("maya", "scripts", version="2025", registry=vfxdirs.DEFAULT_REGISTRY)
```

## Adding a custom provider

Implement the `VFXApp` protocol and pass it in the registry:

```python
from dataclasses import dataclass
from pathlib import Path
from vfxdirs import VFXApp, VFXDirs, DirKey
from vfxdirs.context import Context

@dataclass(frozen=True, slots=True)
class MyAppProvider:
    id: str = "myapp"
    display_name: str = "My App"

    def supported_keys(self):
        return {DirKey.PREFS, DirKey.SCRIPTS}

    def path(self, key, ctx: Context, *, version=None):
        base = ctx.home / ".myapp"
        if key == DirKey.PREFS:
            return base
        if key == DirKey.SCRIPTS:
            return base / "scripts"
        raise KeyError(key)

registry = {**vfxdirs.DEFAULT_REGISTRY, "myapp": MyAppProvider()}
vd = VFXDirs(registry=registry)
```
