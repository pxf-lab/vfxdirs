# vfxdirs
A tiny, zero dependency Python library for accessing useful paths for common visual effects software on any operating system.


> [!IMPORTANT]
> This library is still in development. Not all paths are properly tested for all providers.

# Usage

## Quick start

```python
import vfxdirs

vd = vfxdirs.VFXDirs()

vd.get("maya", "scripts", version="2025")
# Linux:   /home/user/maya/2025/scripts
# macOS:   /Users/user/Library/Preferences/Autodesk/maya/2025/scripts
# Windows: C:\Users\user\Documents\maya\2025\scripts
```

The built-in registry currently includes providers for **Maya**, **Houdini**, **Nuke**, and **Blender**.

## Recommended setup: config file

Rather than passing `version=` on every call, set it once via the CLI:

```sh
$ vfxdirs config set maya.version 2025
$ vfxdirs config set houdini.version 20.5
```

Then load it automatically with `from_default_config`:

```python
vd = vfxdirs.VFXDirs.from_default_config()

vd.get("maya", "scripts")                    # uses version from config
vd.get("maya", "scripts", version="2024")    # explicit version wins
```

**Config file location**

| OS | Path |
|---|---|
| Linux | `~/.config/vfxdirs/config.toml` |
| macOS | `~/Library/Application Support/vfxdirs/config.toml` |
| Windows | `%APPDATA%\vfxdirs\config.toml` |

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

Not every app supports every key; check the provider's `supported_keys()` if needed.

## Get all paths for an app at once

```python
vd.app("houdini", version="20.5").paths()
# {DirKey.PREFS: ..., DirKey.SCRIPTS: ..., ...}
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
from vfxdirs import get

scripts = get("maya", "scripts", version="2025")
```

## Adding a custom provider

Implement the `VFXApp` protocol and pass it in the registry:

```python
from dataclasses import dataclass
from pathlib import Path
from vfxdirs import VFXApp, VFXDirs, DirKey, DEFAULT_REGISTRY
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

vd = VFXDirs(registry={**DEFAULT_REGISTRY, "myapp": MyAppProvider()})
```

# CLI

When installed, vfxdirs provides a `vfxdirs` command for resolving paths and managing config from the shell.

## Resolving paths

```
vfxdirs get <app> <key> [--version VERSION]
```

```sh
$ vfxdirs get maya scripts --version 2025
/home/user/maya/2025/scripts

# use in a script
export MAYA_SCRIPT_PATH=$(vfxdirs get maya scripts)
```

Show all paths for an app at once:

```sh
$ vfxdirs paths houdini --version 20.5
houdini  20.5
  cache     /home/user/.cache/houdini
  config    /home/user/houdini20.5
  data      /home/user/houdini20.5
  packages  /home/user/houdini20.5/packages
  plugins   /home/user/houdini20.5/otls
  prefs     /home/user/houdini20.5
  scripts   /home/user/houdini20.5/scripts
  temp      /tmp/houdini
```

## Discovery

```sh
$ vfxdirs apps
blender
houdini
maya
nuke

$ vfxdirs keys maya
cache
data
logs
packages
plugins
prefs
scripts
temp
```

## Managing config

```sh
# where is the config file?
$ vfxdirs config path
/home/user/.config/vfxdirs/config.toml

# set a default version so you don't have to pass --version every time
$ vfxdirs config set maya.version 2025
set maya.version = '2025'

$ vfxdirs config set houdini.version 20.5
set houdini.version = '20.5'

# redirect a specific path
$ vfxdirs config set maya.paths.scripts /studio/shared/maya/scripts
set maya.paths.scripts = '/studio/shared/maya/scripts'

# override the install root or executable
$ vfxdirs config set houdini.install.root /opt/hfs20.5
set houdini.install.root = '/opt/hfs20.5'

# show the current config
$ vfxdirs config show
[apps.houdini]
version = "20.5"

[apps.houdini.install]
root = "/opt/hfs20.5"

[apps.maya]
version = "2025"

[apps.maya.paths]
scripts = "/studio/shared/maya/scripts"

# open the config in $EDITOR
$ vfxdirs config edit
```

Once a version is set in config, all path queries pick it up automatically:

```sh
$ vfxdirs get maya scripts
/home/user/maya/2025/scripts
```

# Architecture

vfxdirs is built around three independent layers that are composed at runtime.

## Layers

**Context** (`context.py`) captures everything that varies by machine: the OS name, home directory, XDG / platform-standard base directories, and environment variables. It is constructed once and passed read-only into every path resolution call. Tests can inject a fake `Context` to exercise all OS branches without changing platform.

**Providers** (`providers/`) hold the app-specific knowledge: where each VFX application stores its prefs, scripts, plugins, etc., on each OS. A provider is any object that satisfies the `VFXApp` protocol — it exposes an `id`, a `display_name`, `supported_keys()`, and a `path(key, ctx, version=)` method. Providers are stateless and frozen; they receive a `Context` on every call rather than storing one.

**Config** (`config.py`) holds user-supplied overrides loaded from a TOML file. It can set a default `version` per app, redirect individual directory keys to custom paths, or point to a custom installation root. Config is merged in layers — the file on disk is the base, and any programmatic `VFXDirsConfig` passed at construction time takes precedence.

## Path resolution order

When `AppDirs.get(key)` is called, the result is determined in this order:

1. **Path override** — if `config.toml` specifies `[apps.<id>.paths.<key>]`, that path is returned immediately.
2. **Provider + effective version** — the provider's `path()` is called with the resolved version:
   - the `version=` argument passed to `VFXDirs.app()` or `VFXDirs.get()`, if given;
   - otherwise the `version` field from `AppConfig` in the config file;
   - otherwise `None` (provider returns a versionless path).

## Key types

`DirKey` is a `StrEnum` of well-known directory kinds shared across all apps. Providers declare which subset they support via `supported_keys()`. Callers may also pass arbitrary string keys — providers that recognise them can handle them; those that don't will raise `KeyError`.
