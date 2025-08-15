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

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _settings(context) -> Optional[bpy.types.PropertyGroup]:
    """Safe Scene settings getter."""
    return getattr(context.scene, "particlewaves_settings", None)

def _handler_active() -> bool:
    """Is our frame-change handler currently registered?"""
    return advect_points in bpy.app.handlers.frame_change_pre


# (Optional) View/world helpers for an "Apply Look" operator.
def _ensure_cycles_and_color_management(scene: bpy.types.Scene):
    scene.render.engine = 'CYCLES'
    vs = scene.view_settings
    vs.view_transform = 'Standard'
    vs.look = 'None'
    vs.exposure = 0.0
    vs.gamma = 1.0
    if scene.world is None:
        scene.world = bpy.data.worlds.new("PW_AO_World")

def _ensure_ao_world(scene: bpy.types.Scene):
    world = scene.world
    world.use_nodes = True
    nt = world.node_tree
    nodes, links = nt.nodes, nt.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputWorld")
    bg = nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    bg.inputs["Strength"].default_value = 1.0
    links.new(bg.outputs["Background"], out.inputs["Surface"])

def _set_viewports_to_ao():
    wm = bpy.context.window_manager
    for win in wm.windows:
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                sh = space.shading
                sh.type = 'RENDERED'
                sh.use_scene_lights = True
                sh.use_scene_world = True
                try:
                    sh.render_pass = 'AO'
                except Exception:
                    pass


# ──────────────────────────────────────────────────────────────────────────────
# Core operators used by the UI toolbar
# ──────────────────────────────────────────────────────────────────────────────

class PARTICLEWAVES_OT_Rebuild(bpy.types.Operator):
    """Generate or refresh the particle wave system with current settings."""
    bl_idname = "particlewaves.rebuild"
    bl_label = "Generate"
    bl_description = "Generate (or refresh) the particle wave system"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = _settings(context)
        if not s:
            self.report({'ERROR'}, "Scene is missing Particle Waves settings.")
            return {'CANCELLED'}
        create_particle_wave(s)
        register_wave_animation_handler()
        self.report({'INFO'}, "Particle Waves generated.")
        return {'FINISHED'}


class PARTICLEWAVES_OT_Remove(bpy.types.Operator):
    """Remove the generated objects and stop the animation handler."""
    bl_idname = "particlewaves.remove"
    bl_label = "Destroy"
    bl_description = "Remove generated objects and stop the animation handler"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        unregister_wave_animation_handler()
        remove_obj_and_mesh("PARTICLEWAVE")
        remove_obj_and_mesh("PARTICLEDOT")
        self.report({'INFO'}, "Particle Waves removed.")
        return {'FINISHED'}


class PARTICLEWAVES_OT_AgeWave(bpy.types.Operator):
    """Advance the simulation by a set number of seconds."""
    bl_idname = "particlewaves.age_wave"
    bl_label = "Age Wave"
    bl_description = "Advance the simulation by N seconds"
    bl_options = {'REGISTER', 'UNDO'}

    seconds: bpy.props.IntProperty(  # type: ignore
        name="Seconds", default=10, min=1, max=360
    )

    def execute(self, context):
        scene = context.scene
        fps = max(1, int(scene.render.fps))
        start = int(scene.frame_current)
        end = start + int(self.seconds * fps)

        use_handler = _handler_active()
        for frame in range(start + 1, end + 1):
            scene.frame_set(frame)
            if not use_handler:
                # If the handler isn't running, manually advance
                advect_points(scene)
        scene.frame_set(end)

        self.report({'INFO'}, f"Aged by {self.seconds} seconds.")
        return {'FINISHED'}


class PARTICLEWAVES_OT_NewVariation(bpy.types.Operator):
    """Assign a new random seed and rebuild."""
    bl_idname = "particlewaves.new_variation"
    bl_label = "Regenerate"
    bl_description = "Assign a new random seed and rebuild"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = _settings(context)
        if not s:
            self.report({'ERROR'}, "Scene is missing Particle Waves settings.")
            return {'CANCELLED'}
        s.SEED = random.randint(0, 999_999)
        bpy.ops.particlewaves.rebuild()
        return {'FINISHED'}


# ──────────────────────────────────────────────────────────────────────────────
# Preset workflow
# ──────────────────────────────────────────────────────────────────────────────

class PARTICLEWAVES_OT_SetPreset(bpy.types.Operator):
    """Apply a preset's parameter values to the Scene settings (no rebuild)."""
    bl_idname = "particlewaves.set_preset"
    bl_label = "Set Wave Preset"
    bl_description = "Apply the preset's values to settings (does not rebuild)"
    bl_options = {'REGISTER', 'UNDO'}

    preset: bpy.props.StringProperty()  # type: ignore

    def execute(self, context):
        s = _settings(context)
        if not s:
            self.report({'ERROR'}, "Scene is missing Particle Waves settings.")
            return {'CANCELLED'}

        p = self.preset
        if p == 'DEFAULT':
            s.NUM_MODES = 5;   s.FREQ_BASE = 1.4;  s.MOVE_SPEED = 0.07
            s.ATTRACT_GAIN = 0.70; s.ALONG_GAIN = 0.70; s.DIFFUSION = 0.0010
            s.VEL_SMOOTH = 0.97; s.STEP_CLAMP = 0.0012; s.SOFTNESS = 0.6
            s.AXIS_BIAS = (0.0, 0.0, 0.0)

        elif p == 'RIPPLES':
            s.NUM_MODES = 7;   s.FREQ_BASE = 2.0;  s.MOVE_SPEED = 0.03
            s.ATTRACT_GAIN = 0.85; s.ALONG_GAIN = 0.30; s.DIFFUSION = 0.0002
            s.VEL_SMOOTH = 0.99; s.STEP_CLAMP = 0.0008; s.SOFTNESS = 0.3
            s.AXIS_BIAS = (0.0, 0.0, 0.0)

        elif p == 'CHAOS':
            s.NUM_MODES = 10;  s.FREQ_BASE = 1.6;  s.MOVE_SPEED = 0.14
            s.ATTRACT_GAIN = 0.40; s.ALONG_GAIN = 1.10; s.DIFFUSION = 0.0040
            s.VEL_SMOOTH = 0.94; s.STEP_CLAMP = 0.0020; s.SOFTNESS = 0.9
            s.AXIS_BIAS = (0.0, 0.0, 0.0)

        elif p == 'BANDS':
            s.NUM_MODES = 3;   s.FREQ_BASE = 0.9;  s.MOVE_SPEED = 0.05
            s.ATTRACT_GAIN = 0.85; s.ALONG_GAIN = 0.35; s.DIFFUSION = 0.0003
            s.VEL_SMOOTH = 0.99; s.STEP_CLAMP = 0.0010; s.SOFTNESS = 0.2
            s.AXIS_BIAS = (0.0, 0.0, 0.35)

        elif p == 'SOFT':
            s.NUM_MODES = 5;   s.FREQ_BASE = 1.1;  s.MOVE_SPEED = 0.04
            s.ATTRACT_GAIN = 0.65; s.ALONG_GAIN = 0.60; s.DIFFUSION = 0.0007
            s.VEL_SMOOTH = 0.99; s.STEP_CLAMP = 0.0010; s.SOFTNESS = 1.2
            s.AXIS_BIAS = (0.0, 0.0, 0.0)

        else:
            self.report({'WARNING'}, f"Unknown preset: {p}")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Preset applied: {p} (parameters only).")
        return {'FINISHED'}


class PARTICLEWAVES_OT_ApplyPresetAndRebuild(bpy.types.Operator):
    """Apply the selected preset in the dropdown, then (re)generate."""
    bl_idname = "particlewaves.apply_preset_generate"
    bl_label = "Apply Preset & Generate"
    bl_description = "Apply the selected preset and rebuild in one click"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = _settings(context)
        if not s:
            self.report({'ERROR'}, "Scene is missing Particle Waves settings.")
            return {'CANCELLED'}
        bpy.ops.particlewaves.set_preset(preset=s.WAVE_PRESET)
        bpy.ops.particlewaves.rebuild()
        return {'FINISHED'}


# ──────────────────────────────────────────────────────────────────────────────
# Exploration operator (kept but with sane bounds)
# ──────────────────────────────────────────────────────────────────────────────

class PARTICLEWAVES_OT_RandomiseParams(bpy.types.Operator):
    """Randomly sample a tasteful parameter set for exploration."""
    bl_idname = "particlewaves.randomise_params"
    bl_label = "Randomise System Parameters"
    bl_description = "Randomise within curated ranges to avoid mushy results"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = _settings(context)
        if not s:
            self.report({'ERROR'}, "Scene is missing Particle Waves settings.")
            return {'CANCELLED'}

        s.NUM_MODES   = random.randint(2, 10)
        s.FREQ_BASE   = random.uniform(0.8, 2.2)
        s.MOVE_SPEED  = random.uniform(0.02, 0.15)
        s.ATTRACT_GAIN= random.uniform(0.3, 1.2)
        s.ALONG_GAIN  = random.uniform(0.3, 1.2)
        s.DIFFUSION   = random.uniform(0.0, 0.003)
        s.VEL_SMOOTH  = random.uniform(0.93, 0.99)
        s.STEP_CLAMP  = random.uniform(0.0006, 0.0020)
        s.SOFTNESS    = random.uniform(0.3, 1.2)

        self.report({'INFO'}, "System parameters randomised.")
        return {'FINISHED'}


# ──────────────────────────────────────────────────────────────────────────────
# Optional: Apply Look (Cycles + Standard + AO viewport)
# ──────────────────────────────────────────────────────────────────────────────

class PARTICLEWAVES_OT_ApplyLook(bpy.types.Operator):
    """Cycles + Standard color management, simple AO world, AO viewport pass."""
    bl_idname = "particlewaves.apply_look"
    bl_label = "Apply Preferred Look"
    bl_description = "Set Cycles, Standard view transform, AO world, AO viewport"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        _ensure_cycles_and_color_management(scene)
        _ensure_ao_world(scene)
        _set_viewports_to_ao()
        self.report({'INFO'}, "Applied preferred render/world/viewport settings.")
        return {'FINISHED'}