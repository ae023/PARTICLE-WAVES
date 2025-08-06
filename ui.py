import bpy # type: ignore

class PARTICLEWAVES_PT_MainPanel(bpy.types.Panel):
    bl_label = "PARTICLE WAVES CONTROLS"
    bl_idname = "PARTICLEWAVES_PT_MAIN"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PARTICLEWAVES"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.particlewaves_settings

        # PARTICLE SETTINGS
        box = layout.box()
        box.label(text="PARTICLES")
        box.prop(settings, "PARTICLE_COUNT", text="COUNT")
        box.prop(settings, "PARTICLE_RADIUS", text="RADIUS")
        box.prop(settings, "SPHERE_RADIUS", text="FIELD")

        # WAVE SETTINGS
        box = layout.box()
        box.label(text="WAVES")
        box.prop(settings, "WAVE_STRENGTH", text="AMPLITUDE")
        box.prop(settings, "WAVE_SPEED", text="PHASE")
        box.prop(settings, "SEED", text="SEED")

        # SYSTEM PARAMETERS
        box = layout.box()
        box.label(text="SYSTEM PARAMETERS")
        box.prop(settings, "NUM_MODES", text="BAND COUNT")
        box.prop(settings, "FREQ_BASE", text="BASE FREQUENCY")
        box.prop(settings, "MOVE_SPEED", text="DRIFT SPEED")
        box.prop(settings, "ATTRACT_GAIN", text="ATTRACT GAIN")
        box.prop(settings, "ALONG_GAIN", text="TANGENTIAL GAIN")
        box.prop(settings, "DIFFUSION", text="DIFFUSION")
        box.prop(settings, "VEL_SMOOTH", text="VELOCITY SMOOTHING")
        box.prop(settings, "STEP_CLAMP", text="STEP LIMIT")
        box.prop(settings, "SOFTNESS", text="SOFTENING")

        # PRESETS
        box = layout.box()
        box.label(text="PRESETS")
        box.prop(settings, "WAVE_PRESET", text="")
        box.operator("particlewaves.set_preset", text="APPLY").preset = settings.WAVE_PRESET

        # ACTIONS
        box = layout.box()
        box.label(text="ACTIONS")
        box.operator("particlewaves.rebuild", text="GENERATE", icon='FILE_REFRESH')
        box.operator("particlewaves.remove", text="DESTROY", icon='TRASH')

        # PHASE ADVANCE
        layout.separator()
        layout.label(text="PHASE ADVANCE", icon='TIME')
        row = layout.row(align=True)
        row.operator("particlewaves.age_wave", text="Φ+10").seconds = 10
        row.operator("particlewaves.age_wave", text="Φ+20").seconds = 20
        row.operator("particlewaves.age_wave", text="Φ+30").seconds = 30