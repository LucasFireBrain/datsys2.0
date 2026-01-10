bl_info = {
    "name": "PEEK Macros",
    "author": "Lucas",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > PEEKMacros",
    "description": "PEEK case tools, materials, versioning, booleans",
    "category": "3D View",
}

from . import materialTools
from . import versionControl
from . import caseTools
from . import autoFat
from . import quickBoolean
from . import snapshotCameras
from . import decimateSelected
from . import idBridge

modules = [
    materialTools,
    versionControl,
    caseTools,
    autoFat,
    quickBoolean,
    snapshotCameras,
    decimateSelected,
    idBridge,
]

def register():
    for m in modules:
        if hasattr(m, "register"):
            m.register()

def unregister():
    for m in reversed(modules):
        if hasattr(m, "unregister"):
            m.unregister()
