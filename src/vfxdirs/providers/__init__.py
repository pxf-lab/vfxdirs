"""Built-in VFX app providers."""

from .blender import BlenderProvider
from .houdini import HoudiniProvider
from .maya import MayaProvider
from .nuke import NukeProvider

BLENDER = BlenderProvider()
HOUDINI = HoudiniProvider()
MAYA = MayaProvider()
NUKE = NukeProvider()

DEFAULT_REGISTRY: dict = {
    BLENDER.id: BLENDER,
    HOUDINI.id: HOUDINI,
    MAYA.id: MAYA,
    NUKE.id: NUKE,
}

__all__ = [
    "BlenderProvider",
    "HoudiniProvider",
    "MayaProvider",
    "NukeProvider",
    "BLENDER",
    "HOUDINI",
    "MAYA",
    "NUKE",
    "DEFAULT_REGISTRY",
]
