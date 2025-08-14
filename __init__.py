bl_info = {
    "name": "PARTICLE WAVE FIELD",
    "author": "ERIN",
    "version": (1, 1, 0),
    "blender": (4, 3, 0),
    "location": "View3D > Sidebar > PARTICLE WAVE FIELD",
    "description": "Scatter & animate particles across a sphere using a multi-mode wave field.",
    "category": "Object",
}

import bpy  # type: ignore
from importlib import reload

# SUPPORT HOT RELOAD DURING DEVELOPMENT
if "bpy" in locals():
    try:
        reload(props)       # type: ignore[name-defined]
        reload(operators)   # type: ignore[name-defined]
        reload(ui)          # type: ignore[name-defined]
        reload(core)        # type: ignore[name-defined]
    except Exception:
        pass

from . import props, operators, ui, core  # type: ignore

# COLLECT CLASSES SAFELY
def _gather_classes():
    # RETURN A LIST OF CLASSES TO REGISTER, SKIPPING ANY THAT ARE NOT PRESENT
    candidates = [
        (props, "ParticleWavesSettings"),
        (operators, "PARTICLEWAVES_OT_Rebuild"),
        (operators, "PARTICLEWAVES_OT_Remove"),
        (operators, "PARTICLEWAVES_OT_AgeWave"),
        (operators, "PARTICLEWAVES_OT_SetPreset"),
        (operators, "PARTICLEWAVES_OT_RandomiseParams"),
        # OPTIONAL FUTURE OPERATOR
        (operators, "PARTICLEWAVES_OT_NewVariation"),
        (ui, "PARTICLEWAVES_PT_MainPanel"),
    ]
    classes = []
    for module, name in candidates:
        cls = getattr(module, name, None)
        if cls is not None:
            classes.append(cls)
    return classes


_CLASSES = []  # FILLED DURING REGISTER()


def register():
    global _CLASSES
    _CLASSES = _gather_classes()

    for cls in _CLASSES:
        bpy.utils.register_class(cls)

    # SCENE PROPERTY POINTER
    if not hasattr(bpy.types.Scene, "particlewaves_settings"):
        bpy.types.Scene.particlewaves_settings = bpy.props.PointerProperty(
            type=props.ParticleWavesSettings  # type: ignore
        )


def unregister():
    # ENSURE THE FRAME CHANGE HANDLER IS REMOVED EVEN IF OBJECTS REMAIN
    try:
        core.unregister_wave_animation_handler()
    except Exception:
        pass

    # REMOVE SCENE PROPERTY POINTER
    if hasattr(bpy.types.Scene, "particlewaves_settings"):
        try:
            del bpy.types.Scene.particlewaves_settings
        except Exception:
            pass

    # UNREGISTER CLASSES IN REVERSE ORDER
    for cls in reversed(_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass

# ALLOW RUNNING THIS FILE DIRECTLY FROM BLENDERS TEXT EDITOR FOR QUICK TESTS
if __name__ == "__main__":
    register()