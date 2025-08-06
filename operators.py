import bpy # type: ignore
import random # type: ignore
from .core import create_particle_wave, register_wave_animation_handler, unregister_wave_animation_handler, advect_points

class PARTICLEWAVES_OT_Rebuild(bpy.types.Operator):
    bl_idname = "particlewaves.rebuild"
    bl_label = "REBUILD PARTICLE WAVE"
    bl_description = "CREATE OR REFRESH THE PARTICLE WAVE SYSTEM"
    def execute(self, context):
        settings = context.scene.particlewaves_settings
        create_particle_wave(settings)
        register_wave_animation_handler()
        return {'FINISHED'}

class PARTICLEWAVES_OT_Remove(bpy.types.Operator):
    bl_idname = "particlewaves.remove"
    bl_label = "REMOVE PARTICLE WAVE"
    bl_description = "REMOVE THE PARTICLE WAVE SYSTEM"
    def execute(self, context):
        unregister_wave_animation_handler()
        from .core import remove_obj_and_mesh
        remove_obj_and_mesh("PARTICLEWAVE")
        remove_obj_and_mesh("PARTICLEDOT")
        return {'FINISHED'}

class PARTICLEWAVES_OT_AgeWave(bpy.types.Operator):
    bl_idname = "particlewaves.age_wave"
    bl_label = "AGE WAVE"
    bl_description = "ADVANCE THE WAVE ANIMATION BY A SET NUMBER OF SECONDS"

    seconds: bpy.props.IntProperty(
        name="SECONDS",
        default=10,
        min=1,
        max=60
    ) # type: ignore

    def execute(self, context):
        scene = context.scene
        fps = scene.render.fps
        start = scene.frame_current
        end = start + self.seconds * fps
        for frame in range(start + 1, end + 1):
            scene.frame_set(frame)
            advect_points(scene)
        scene.frame_set(end)
        return {'FINISHED'}
    
class PARTICLEWAVES_OT_RandomiseParams(bpy.types.Operator):
    bl_idname = "particlewaves.randomise_params"
    bl_label = "Randomise System Parameters"
    bl_description = "Randomly set system parameters for creative exploration"

    def execute(self, context):
        s = context.scene.particlewaves_settings
        s.NUM_MODES = random.randint(1, 32)
        s.FREQ_BASE = random.uniform(0.1, 10.0)
        s.MOVE_SPEED = random.uniform(0.001, 0.2)
        s.ATTRACT_GAIN = random.uniform(0.0, 2.0)
        s.ALONG_GAIN = random.uniform(0.0, 2.0)
        s.DIFFUSION = random.uniform(0.0, 0.02)
        s.VEL_SMOOTH = random.uniform(0.5, 0.999)
        s.STEP_CLAMP = random.uniform(0.0001, 0.02)
        s.SOFTNESS = random.uniform(0.01, 5.0)
        return {'FINISHED'}

class PARTICLEWAVES_OT_SetPreset(bpy.types.Operator):
    bl_idname = "particlewaves.set_preset"
    bl_label = "Set Wave Preset"
    preset: bpy.props.StringProperty() # type: ignore

    def execute(self, context):
        s = context.scene.particlewaves_settings
        if self.preset == 'DEFAULT':
            s.NUM_MODES = 4; s.FREQ_BASE = 1.2; s.MOVE_SPEED = 0.07
            s.ATTRACT_GAIN = 0.6; s.ALONG_GAIN = 0.7; s.DIFFUSION = 0.001
            s.VEL_SMOOTH = 0.97; s.STEP_CLAMP = 0.0012; s.SOFTNESS = 0.6
        elif self.preset == 'RIPPLES':
            s.NUM_MODES = 6; s.FREQ_BASE = 2.0; s.MOVE_SPEED = 0.03
            s.ATTRACT_GAIN = 0.9; s.ALONG_GAIN = 0.3; s.DIFFUSION = 0.0003
            s.VEL_SMOOTH = 0.98; s.STEP_CLAMP = 0.0008; s.SOFTNESS = 0.3
        elif self.preset == 'CHAOS':
            s.NUM_MODES = 8; s.FREQ_BASE = 1.5; s.MOVE_SPEED = 0.15
            s.ATTRACT_GAIN = 0.3; s.ALONG_GAIN = 1.2; s.DIFFUSION = 0.005
            s.VEL_SMOOTH = 0.93; s.STEP_CLAMP = 0.002; s.SOFTNESS = 0.9
        elif self.preset == 'BANDS':
            s.NUM_MODES = 3; s.FREQ_BASE = 0.8; s.MOVE_SPEED = 0.05
            s.ATTRACT_GAIN = 0.8; s.ALONG_GAIN = 0.4; s.DIFFUSION = 0.0005
            s.VEL_SMOOTH = 0.99; s.STEP_CLAMP = 0.001; s.SOFTNESS = 0.2
        elif self.preset == 'SOFT':
            s.NUM_MODES = 5; s.FREQ_BASE = 1.0; s.MOVE_SPEED = 0.04
            s.ATTRACT_GAIN = 0.7; s.ALONG_GAIN = 0.6; s.DIFFUSION = 0.0007
            s.VEL_SMOOTH = 0.98; s.STEP_CLAMP = 0.001; s.SOFTNESS = 1.0
        return {'FINISHED'}