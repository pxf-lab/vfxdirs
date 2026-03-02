"""Built-in VFX app providers."""

from .maya import MayaProvider

MAYA = MayaProvider()

DEFAULT_REGISTRY: dict = {
    MAYA.id: MAYA,
}

__all__ = [
    "MayaProvider",
    "MAYA",
    "DEFAULT_REGISTRY",
]
