"""Built-in VFX app providers."""

from .houdini import HoudiniProvider
from .maya import MayaProvider
from .nuke import NukeProvider

HOUDINI = HoudiniProvider()
MAYA = MayaProvider()
NUKE = NukeProvider()

DEFAULT_REGISTRY: dict = {
    HOUDINI.id: HOUDINI,
    MAYA.id: MAYA,
    NUKE.id: NUKE,
}

__all__ = [
    "HoudiniProvider",
    "MayaProvider",
    "NukeProvider",
    "HOUDINI",
    "MAYA",
    "NUKE",
    "DEFAULT_REGISTRY",
]
