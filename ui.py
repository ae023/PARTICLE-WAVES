import bpy  # type: ignore


class PARTICLEWAVES_PT_MainPanel(bpy.types.Panel):
    bl_label = "PARTICLE WAVE SETTINGS"
    bl_idname = "PARTICLEWAVES_PT_MAIN"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PARTICLE WAVES"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        settings = context.scene.particlewaves_settings

        # ── QUICK ACTIONS ───────────────────────────────────────────────────────
        box = layout.box()
        box.label(text="ACTIONS")
        row = box.row(align=True)
        row.operator("particlewaves.rebuild", text="GENERATE", icon='FILE_REFRESH')
        row.operator("particlewaves.remove", text="DESTROY", icon='TRASH')
        row.operator("particlewaves.new_variation", text="NEW VARIATION", icon='SORTTIME')

        # ── PARTICLE SETTINGS ──────────────────────────────────────────────────
        box = layout.box()
        box.label(text="PARTICLE SETTINGS")
        col = box.column(align=True)
        col.prop(settings, "PARTICLE_COUNT")
        col.prop(settings, "PARTICLE_RADIUS")
        col.prop(settings, "SPHERE_RADIUS")

        # ── WAVE SETTINGS ──────────────────────────────────────────────────────
        box = layout.box()
        box.label(text="WAVE SETTINGS")
        col = box.column(align=True)
        col.prop(settings, "WAVE_STRENGTH")
        col.prop(settings, "WAVE_SPEED")
        col.prop(settings, "SEED")

        # ── SYSTEM PARAMETERS (STRUCTURED) ─────────────────────────────────────
        box = layout.box()
        box.label(text="SYSTEM PARAMETERS")

        # STRUCTURE & DYNAMICS SPLIT INTO TWO COLUMNS FOR READABILITY
        row = box.row(align=True)
        colL = row.column(align=True)
        colR = row.column(align=True)

        # STRUCTURE
        colL.label(text="STRUCTURE")
        colL.prop(settings, "NUM_MODES")
        colL.prop(settings, "FREQ_BASE")
        colL.prop(settings, "ATTRACT_GAIN")
        colL.prop(settings, "ALONG_GAIN")

        # DYNAMICS
        colR.label(text="DYNAMICS")
        colR.prop(settings, "MOVE_SPEED")
        colR.prop(settings, "DIFFUSION")
        colR.prop(settings, "VEL_SMOOTH")
        colR.prop(settings, "STEP_CLAMP")
        colR.prop(settings, "SOFTNESS")

        # RANDOMISER
        box.operator("particlewaves.randomise_params", text="RANDOMISE SYSTEM PARAMETERS", icon='RNDCURVE')

        # ── ADVANCED ───────────────────────────────────────────────────────────
        box = layout.box()
        box.label(text="ADVANCED")
        col = box.column(align=True)
        col.prop(settings, "AXIS_BIAS")

        # ── PRESETS ────────────────────────────────────────────────────────────
        box = layout.box()
        box.label(text="PRESETS")
        row = box.row(align=True)
        row.prop(settings, "WAVE_PRESET", text="")
        op = row.operator("particlewaves.set_preset", text="Apply", icon='CHECKMARK')
        op.preset = settings.WAVE_PRESET

        # ── PHASE ADVANCE ──────────────────────────────────────────────────────
        layout.separator()
        layout.label(text="PHASE ADVANCE")
        row = layout.row(align=True)
        b10 = row.operator("particlewaves.age_wave", text="Φ +10s", icon='FRAME_NEXT')
        b10.seconds = 10
        b20 = row.operator("particlewaves.age_wave", text="Φ +20s", icon='FRAME_NEXT')
        b20.seconds = 20
        b30 = row.operator("particlewaves.age_wave", text="Φ +30s", icon='FRAME_NEXT')
        b30.seconds = 30