import bpy  # type: ignore
import random  # type: ignore
from typing import Optional

from .core import (
    create_particle_wave,
    register_wave_animation_handler,
    unregister_wave_animation_handler,
    advect_points,
    remove_obj_and_mesh,
)

# HELPERS
def _get_settings(context) -> Optional[bpy.types.PropertyGroup]:
    # RETURN THE ADD-ON SETTINGS OR NONE IF MISSING.
    return getattr(context.scene, "particlewaves_settings", None)

def _handler_active() -> bool:
    return advect_points in bpy.app.handlers.frame_change_pre

# OPERATORS
class PARTICLEWAVES_OT_Rebuild(bpy.types.Operator):
    # CREATE OR REFRESH THE PARTICLE WAVE SYSTEM.
    bl_idname = "particlewaves.rebuild"
    bl_label = "REBUILD PARTICLE WAVE"
    bl_description = "CREATE OR REFRESH THE PARTICLE WAVE SYSTEM"

    def execute(self, context):
        s = _get_settings(context)
        if not s:
            self.report({'ERROR'}, "Particle Waves settings not found on Scene.")
            return {'CANCELLED'}

        create_particle_wave(s)
        register_wave_animation_handler()
        self.report({'INFO'}, "Particle Waves generated.")
        return {'FINISHED'}

class PARTICLEWAVES_OT_Remove(bpy.types.Operator):
    # REMOVE OBJECTS AND STOP THE ANIMATION HANDLER.
    bl_idname = "particlewaves.remove"
    bl_label = "REMOVE PARTICLE WAVE"
    bl_description = "REMOVE THE PARTICLE WAVE SYSTEM"

    def execute(self, context):
        # STOP SIMULATION UPDATES FIRST
        unregister_wave_animation_handler()
        # CLEAN UP OBJECTS
        remove_obj_and_mesh("PARTICLEWAVE")
        remove_obj_and_mesh("PARTICLEDOT")
        self.report({'INFO'}, "Particle Waves removed.")
        return {'FINISHED'}


class PARTICLEWAVES_OT_AgeWave(bpy.types.Operator):
    # ADVANCE THE WAVE ANIMATION BY A SET NUMBER OF SECONDS.
    bl_idname = "particlewaves.age_wave"
    bl_label = "AGE WAVE"
    bl_description = "ADVANCE THE WAVE ANIMATION BY A SET NUMBER OF SECONDS"

    seconds: bpy.props.IntProperty(  # type: ignore
        name="SECONDS",
        default=10,
        min=1,
        max=120,
    )

    def execute(self, context):
        scene = context.scene
        fps = max(1, int(scene.render.fps))
        start = int(scene.frame_current)
        end = start + int(self.seconds * fps)

        # AVOID DOUBLE-STEPPING: IF THE HANDLER IS ACTIVE, FRAME_SET WILL ALREADY ADVECT.
        use_handler = _handler_active()

        for frame in range(start + 1, end + 1):
            scene.frame_set(frame)
            if not use_handler:
                advect_points(scene)

        scene.frame_set(end)
        self.report({'INFO'}, f"Aged simulation by {self.seconds}s.")
        return {'FINISHED'}


class PARTICLEWAVES_OT_RandomiseParams(bpy.types.Operator):
    # RANDOMLY SET SYSTEM PARAMETERS FOR CREATIVE EXPLORATION.
    bl_idname = "particlewaves.randomise_params"
    bl_label = "Randomise System Parameters"
    bl_description = "Randomly set system parameters for creative exploration"

    def execute(self, context):
        s = _get_settings(context)
        if not s:
            self.report({'ERROR'}, "Particle Waves settings not found on Scene.")
            return {'CANCELLED'}

        # FOCUS RANGES TO AVOID UNPRODUCTIVE EXTREMES
        s.NUM_MODES = random.randint(2, 10)
        s.FREQ_BASE = random.uniform(0.8, 2.2)
        s.MOVE_SPEED = random.uniform(0.02, 0.15)
        s.ATTRACT_GAIN = random.uniform(0.3, 1.2)
        s.ALONG_GAIN = random.uniform(0.3, 1.2)
        s.DIFFUSION = random.uniform(0.0, 0.003)
        s.VEL_SMOOTH = random.uniform(0.93, 0.99)
        s.STEP_CLAMP = random.uniform(0.0006, 0.002)
        s.SOFTNESS = random.uniform(0.3, 1.2)

        self.report({'INFO'}, "System parameters randomised.")
        return {'FINISHED'}


class PARTICLEWAVES_OT_SetPreset(bpy.types.Operator):
    # APPLY A NAMED PRESET (DETERMINISTIC VALUES).
    bl_idname = "particlewaves.set_preset"
    bl_label = "Set Wave Preset"

    preset: bpy.props.StringProperty()  # type: ignore

    def execute(self, context):
        s = _get_settings(context)
        if not s:
            self.report({'ERROR'}, "Particle Waves settings not found on Scene.")
            return {'CANCELLED'}

        if self.preset == 'DEFAULT':
            s.NUM_MODES = 5;   s.FREQ_BASE = 1.4;  s.MOVE_SPEED = 0.07
            s.ATTRACT_GAIN = 0.70; s.ALONG_GAIN = 0.70; s.DIFFUSION = 0.0010
            s.VEL_SMOOTH = 0.97; s.STEP_CLAMP = 0.0012; s.SOFTNESS = 0.6
            s.AXIS_BIAS = (0.0, 0.0, 0.0)
        elif self.preset == 'RIPPLES':
            s.NUM_MODES = 7;   s.FREQ_BASE = 2.0;  s.MOVE_SPEED = 0.03
            s.ATTRACT_GAIN = 0.85; s.ALONG_GAIN = 0.30; s.DIFFUSION = 0.0002
            s.VEL_SMOOTH = 0.99; s.STEP_CLAMP = 0.0008; s.SOFTNESS = 0.3
            s.AXIS_BIAS = (0.0, 0.0, 0.0)
        elif self.preset == 'CHAOS':
            s.NUM_MODES = 10;  s.FREQ_BASE = 1.6;  s.MOVE_SPEED = 0.14
            s.ATTRACT_GAIN = 0.40; s.ALONG_GAIN = 1.10; s.DIFFUSION = 0.0040
            s.VEL_SMOOTH = 0.94; s.STEP_CLAMP = 0.0020; s.SOFTNESS = 0.9
            s.AXIS_BIAS = (0.0, 0.0, 0.0)
        elif self.preset == 'BANDS':
            s.NUM_MODES = 3;   s.FREQ_BASE = 0.9;  s.MOVE_SPEED = 0.05
            s.ATTRACT_GAIN = 0.85; s.ALONG_GAIN = 0.35; s.DIFFUSION = 0.0003
            s.VEL_SMOOTH = 0.99; s.STEP_CLAMP = 0.0010; s.SOFTNESS = 0.2
            s.AXIS_BIAS = (0.0, 0.0, 0.35)  # subtle equatorial/polar bias
        elif self.preset == 'SOFT':
            s.NUM_MODES = 5;   s.FREQ_BASE = 1.1;  s.MOVE_SPEED = 0.04
            s.ATTRACT_GAIN = 0.65; s.ALONG_GAIN = 0.60; s.DIFFUSION = 0.0007
            s.VEL_SMOOTH = 0.99; s.STEP_CLAMP = 0.0010; s.SOFTNESS = 1.2
            s.AXIS_BIAS = (0.0, 0.0, 0.0)
        else:
            self.report({'WARNING'}, f"Unknown preset: {self.preset}")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Preset applied: {self.preset}")
        return {'FINISHED'}

class PARTICLEWAVES_OT_NewVariation(bpy.types.Operator):
    # QUICKLY GET A FRESH LOOK: RESEED + REBUILD (KEEPS CURRENT SETTINGS).
    bl_idname = "particlewaves.new_variation"
    bl_label = "New Variation"
    bl_description = "Assign a new random seed and rebuild the system"

    def execute(self, context):
        s = _get_settings(context)
        if not s:
            self.report({'ERROR'}, "Particle Waves settings not found on Scene.")
            return {'CANCELLED'}

        s.SEED = random.randint(0, 999_999)
        bpy.ops.particlewaves.rebuild()
        return {'FINISHED'}