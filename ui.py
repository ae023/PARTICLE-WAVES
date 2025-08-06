import bpy # type: ignore

class PARTICLEWAVES_PT_MainPanel(bpy.types.Panel):
    bl_label = "PARTICLE WAVE SETTINGS"
    bl_idname = "PARTICLEWAVES_PT_MAIN"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PARTICLE WAVES"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.particlewaves_settings

        # PARTICLE SETTINGS
        box = layout.box()
        box.label(text="PARTICLE SETTINGS")
        box.prop(settings, "PARTICLE_COUNT")
        box.prop(settings, "PARTICLE_RADIUS")
        box.prop(settings, "SPHERE_RADIUS")

        layout.separator()

        # WAVE SETTINGS
        box = layout.box()
        box.label(text="WAVE SETTINGS")
        box.prop(settings, "WAVE_STRENGTH")
        box.prop(settings, "WAVE_SPEED")
        box.prop(settings, "SEED")

        layout.separator()

        # SYSTEM PARAMETERS
        box = layout.box()
        box.label(text="SYSTEM PARAMETERS")
        box.prop(settings, "NUM_MODES")
        box.prop(settings, "FREQ_BASE")
        box.prop(settings, "MOVE_SPEED")
        box.prop(settings, "ATTRACT_GAIN")
        box.prop(settings, "ALONG_GAIN")
        box.prop(settings, "DIFFUSION")
        box.prop(settings, "VEL_SMOOTH")
        box.prop(settings, "STEP_CLAMP")
        box.prop(settings, "SOFTNESS")
        box.operator("particlewaves.randomise_params", text="RANDOMISE SYSTEM PARAMETERS", icon='RNDCURVE')

        layout.separator()

        # PRESETS
        box = layout.box()
        box.label(text="PRESETS")
        box.prop(settings, "WAVE_PRESET", text="")
        box.operator("particlewaves.set_preset", text="APPLY").preset = settings.WAVE_PRESET

        layout.separator()

        # ACTIONS (side by side)
        box = layout.box()
        box.label(text="ACTIONS")
        row = box.row(align=True)
        row.operator("particlewaves.rebuild", text="GENERATE", icon='FILE_REFRESH')
        row.operator("particlewaves.remove", text="DESTROY", icon='TRASH')

        layout.separator()

        # PHASE ADVANCE (unchanged)
        layout.label(text="PHASE ADVANCE")
        row = layout.row(align=True)
        row.operator("particlewaves.age_wave", text="Φ+10").seconds = 10
        row.operator("particlewaves.age_wave", text="Φ+20").seconds = 20
        row.operator("particlewaves.age_wave", text="Φ+30").seconds = 30