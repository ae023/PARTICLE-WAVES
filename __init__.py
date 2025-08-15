bl_info = {
    "name": "PARTICLE WAVES",
    "author": "ERIN",
    "version": (1, 3, 0),
    "blender": (4, 3, 0),
    "location": "View3D > Sidebar > PARTICLE WAVES",
    "description": "Scatter & animate particles across a sphere using a multi-mode wave field.",
    "category": "Object",
}

import bpy # type: ignore
from importlib import reload
from . import props, operators, ui, core  # import modules (not classes!) to avoid dupes on reload

# Dev-friendly hot reload (safe if modules weren't loaded yet)
for _m in (props, operators, ui, core):
    try:
        reload(_m)
    except Exception:
        pass


def _maybe(mod, name):
    """Return mod.name if it exists, else None."""
    return getattr(mod, name, None)


def _gather_classes():
    """
    Build a single, ordered list of classes to register.
    - PropertyGroup first (so the Scene pointer can reference it)
    - Operators (only those that exist in your current codebase)
    - Panels (main + sub-panels if present)
    """
    cls_list = []

    # 1) Props first
    PWSettings = _maybe(props, "ParticleWavesSettings")
    if PWSettings:
        cls_list.append(PWSettings)

    # 2) Operators (optional/robust lookups)
    for name in (
        "PARTICLEWAVES_OT_Rebuild",
        "PARTICLEWAVES_OT_Remove",
        "PARTICLEWAVES_OT_AgeWave",
        "PARTICLEWAVES_OT_SetPreset",
        "PARTICLEWAVES_OT_RandomiseParams",
        "PARTICLEWAVES_OT_NewVariation",
        "PARTICLEWAVES_OT_ApplyPresetAndRebuild",  # optional, if you added it
        "PARTICLEWAVES_OT_ApplyLook",              # optional, if you added it
        "PARTICLEWAVES_OT_RepairSettings",         # optional, if you added it
    ):
        cls = _maybe(operators, name)
        if cls and cls not in cls_list:
            cls_list.append(cls)

    # 3) Panels (accept either PARTICLEWAVES_* or POINTCLOUD_* naming)
    for name in (
        "PARTICLEWAVES_PT_MainPanel",
        "POINTCLOUD_PT_MainPanel",     # fallback if you used another prefix
        "PARTICLEWAVES_PT_Presets",
        "PARTICLEWAVES_PT_Particle",
        "PARTICLEWAVES_PT_Wave",
        "PARTICLEWAVES_PT_System",
        "PARTICLEWAVES_PT_Advanced",
        "PARTICLEWAVES_PT_PresetsHint",# optional
        "PARTICLEWAVES_PT_PhaseAdvance",# optional 
    ):
        cls = _maybe(ui, name)
        if cls and cls not in cls_list:
            cls_list.append(cls)

    return cls_list


def _safe_register(cls):
    """Register class; if already registered, unregister then re-register."""
    if cls is None:
        return
    try:
        bpy.utils.register_class(cls)
    except ValueError:
        # "already registered" — likely from a previous hot reload
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
        bpy.utils.register_class(cls)


def _safe_unregister(cls):
    if cls is None:
        return
    try:
        bpy.utils.unregister_class(cls)
    except Exception:
        pass


_CLASSES = []


def register():
    global _CLASSES
    _CLASSES = _gather_classes()

    # Register classes
    for cls in _CLASSES:
        _safe_register(cls)

    # Add Scene pointer once
    if not hasattr(bpy.types.Scene, "particlewaves_settings"):
        bpy.types.Scene.particlewaves_settings = bpy.props.PointerProperty(
            type=getattr(props, "ParticleWavesSettings")
        )


def unregister():
    # Remove frame-change handler if active
    try:
        core.unregister_wave_animation_handler()
    except Exception:
        pass

    # Remove Scene pointer if present
    if hasattr(bpy.types.Scene, "particlewaves_settings"):
        try:
            del bpy.types.Scene.particlewaves_settings
        except Exception:
            pass

    # Unregister in reverse order
    for cls in reversed(_CLASSES):
        _safe_unregister(cls)