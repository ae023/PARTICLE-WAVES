import bpy  # type: ignore

def _settings(ctx):
    return getattr(ctx.scene, "particlewaves_settings", None)


class PARTICLEWAVES_PT_MainPanel(bpy.types.Panel):
    bl_label = "PARTICLE WAVE SETTINGS"
    bl_idname = "PARTICLEWAVES_PT_MAIN"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PARTICLE WAVES"

    def draw(self, context):
        layout = self.layout
        s = _settings(context)

        # COMPACT HEADER (NO SPLIT LABELS)
        layout.use_property_split = False
        layout.use_property_decorate = False

        header = layout.box()

        # LINE 1 — PRESET TITLE
        header.label(text="PRESET")

        # LINE 2 — DROPDOWN | GEN | REGEN | DESTROY (ICON-ONLY)
        row = header.row(align=True)
        if s is None:
            row.label(text="Settings missing. Re-enable add-on.", icon='ERROR')
        else:
            row.prop(s, "WAVE_PRESET", text="")

        # CHOOSE BEST GEN ACTION AVAILABLE
        gen_op_id = ("particlewaves.apply_preset_generate"
                     if hasattr(bpy.ops.particlewaves, "apply_preset_generate")
                     else "particlewaves.rebuild")

        row.operator(gen_op_id,                     text="", icon='FILE_REFRESH')  # GEN
        row.operator("particlewaves.new_variation", text="", icon='RNDCURVE')      # REGEN
        row.operator("particlewaves.remove",        text="", icon='TRASH')         # DESTROY

        # Line 3 — Phase advance
        row = header.row(align=True)
        for sec in (10, 20, 30):
            op = row.operator("particlewaves.age_wave", text=f"Φ +{sec}s", icon='FRAME_NEXT')
            op.seconds = sec


# ---------- SUB-PANELS (SINGLE COLUMN, COLLAPSIBLE) ----------
class _PW_Sub(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "PARTICLEWAVES_PT_MAIN"

    @staticmethod
    def _s(layout, context):
        layout.use_property_split = True
        layout.use_property_decorate = False
        s = _settings(context)
        if s is None:
            layout.label(text="Generate first.", icon='INFO')
        return s


class PARTICLEWAVES_PT_Particle(_PW_Sub):
    bl_label = "Particle"
    bl_idname = "PARTICLEWAVES_PT_PARTICLE"
    def draw(self, context):
        layout = self.layout
        s = self._s(layout, context);  
        if not s: return
        col = layout.column(align=True)
        col.prop(s, "PARTICLE_COUNT")
        col.prop(s, "PARTICLE_RADIUS")
        col.prop(s, "SPHERE_RADIUS")


class PARTICLEWAVES_PT_Wave(_PW_Sub):
    bl_label = "Wave"
    bl_idname = "PARTICLEWAVES_PT_WAVE"
    def draw(self, context):
        layout = self.layout
        s = self._s(layout, context);  
        if not s: return
        col = layout.column(align=True)
        col.prop(s, "WAVE_STRENGTH")
        col.prop(s, "WAVE_SPEED")
        col.prop(s, "SEED")


class PARTICLEWAVES_PT_System(_PW_Sub):
    bl_label = "System"
    bl_idname = "PARTICLEWAVES_PT_SYSTEM"
    def draw(self, context):
        layout = self.layout
        s = self._s(layout, context);  
        if not s: return
        col = layout.column(align=True)
        col.prop(s, "NUM_MODES")
        col.prop(s, "FREQ_BASE")
        col.prop(s, "MOVE_SPEED")
        col.prop(s, "ATTRACT_GAIN")
        col.prop(s, "ALONG_GAIN")
        col.prop(s, "DIFFUSION")
        col.prop(s, "VEL_SMOOTH")
        col.prop(s, "STEP_CLAMP")
        col.prop(s, "SOFTNESS")
        layout.operator("particlewaves.randomise_params", text="Randomise System Parameters", icon='RNDCURVE')


class PARTICLEWAVES_PT_Advanced(_PW_Sub):
    bl_label = "Advanced"
    bl_idname = "PARTICLEWAVES_PT_ADVANCED"
    bl_options = {'DEFAULT_CLOSED'}  # COLLAPSED BY DEFAULT
    def draw(self, context):
        layout = self.layout
        s = self._s(layout, context);  
        if not s: return
        layout.prop(s, "AXIS_BIAS")