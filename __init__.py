bl_info = {
    "name": "PARTICLE WAVES",
    "author": "ERIN",
    "version": (1, 0),
    "blender": (4, 3, 2),
    "location": "View3D > Sidebar > ParticleWaves",
    "description": "SCATTER & ANIMATE PARTICLES ACROSS THE SURFACE OF A SPHERE WITH NOISE DRIVEN RIPPLE EFFECTS.",
    "category": "Object",
}

import bpy # type: ignore

from .props import ParticleWavesSettings
from .operators import PARTICLEWAVES_OT_Rebuild, PARTICLEWAVES_OT_Remove, PARTICLEWAVES_OT_AgeWave, PARTICLEWAVES_OT_SetPreset
from .ui import PARTICLEWAVES_PT_MainPanel

classes = [
    ParticleWavesSettings,
    PARTICLEWAVES_OT_Rebuild,
    PARTICLEWAVES_OT_Remove,
    PARTICLEWAVES_OT_AgeWave,
    PARTICLEWAVES_OT_SetPreset,
    PARTICLEWAVES_PT_MainPanel,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.particlewaves_settings = bpy.props.PointerProperty(type=ParticleWavesSettings)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.particlewaves_settings