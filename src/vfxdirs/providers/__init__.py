"""Built-in VFX app providers."""

from .houdini import HoudiniProvider
from .maya import MayaProvider

HOUDINI = HoudiniProvider()
MAYA = MayaProvider()

DEFAULT_REGISTRY: dict = {
    HOUDINI.id: HOUDINI,
    MAYA.id: MAYA,
}

__all__ = [
    "HoudiniProvider",
    "MayaProvider",
    "HOUDINI",
    "MAYA",
    "DEFAULT_REGISTRY",
]
