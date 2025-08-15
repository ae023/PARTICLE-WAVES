import bpy  # type: ignore

def _settings(ctx):
    return getattr(ctx.scene, "particlewaves_settings", None)


# ─────────────────────────────────────────────────────────
# Parent container panel (MODE lives here; not collapsible)
# ─────────────────────────────────────────────────────────
class PARTICLEWAVES_PT_MainPanel(bpy.types.Panel):
    bl_label = "PARTICLE WAVE SETTINGS"
    bl_idname = "PARTICLEWAVES_PT_MAIN"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PARTICLE WAVES"

    def draw(self, context):
        layout = self.layout
        s = _settings(context)

        # MODE (non-collapsible, no box)
        layout.label(text="MODE")
        layout.use_property_split = False
        layout.use_property_decorate = False

        # Row 1 — dropdown (fills width)
        row = layout.row(align=True)
        if s is None:
            row.label(text="Generate first.", icon='INFO')
        else:
            row.prop(s, "WAVE_PRESET", text="")

        # Row 2 — Generate | Regenerate | Destroy
        row = layout.row(align=True)
        gen_op = ("particlewaves.apply_preset_generate"
                  if hasattr(bpy.ops.particlewaves, "apply_preset_generate")
                  else "particlewaves.rebuild")
        row.operator(gen_op,                     text="GENERATE")
        row.operator("particlewaves.new_variation", text="REGENERATE")
        row.operator("particlewaves.remove",        text="DESTROY")

        # Row 3 — phase advance
        row = layout.row(align=True)
        for sec in (10, 20, 30, 40, 50, 60):
            op = row.operator("particlewaves.age_wave", text=f"Φ +{sec}")
            op.seconds = sec


# ─────────────────────────────────────────────────────────
# Sub-panels (collapsible), ordered under Main
# ─────────────────────────────────────────────────────────
class _PW_Sub(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = "PARTICLEWAVES_PT_MAIN"

    @staticmethod
    def _s(layout, context):
        # Match your current look (no split labels)
        layout.use_property_split = False
        layout.use_property_decorate = False
        s = _settings(context)
        if s is None:
            layout.label(text="Generate first.", icon='INFO')
        return s


class PARTICLEWAVES_PT_Particle(_PW_Sub):
    bl_label = "PARTICLE SETTINGS"
    bl_idname = "PARTICLEWAVES_PT_PARTICLE"
    bl_order = 10
    def draw(self, context):
        layout = self.layout
        s = self._s(layout, context);  
        if not s: return
        col = layout.column(align=True)
        col.prop(s, "PARTICLE_COUNT")
        col.prop(s, "PARTICLE_RADIUS")
        col.prop(s, "SPHERE_RADIUS")


class PARTICLEWAVES_PT_Wave(_PW_Sub):
    bl_label = "WAVE SETTINGS"
    bl_idname = "PARTICLEWAVES_PT_WAVE"
    bl_order = 20
    def draw(self, context):
        layout = self.layout
        s = self._s(layout, context);  
        if not s: return
        col = layout.column(align=True)
        col.prop(s, "WAVE_STRENGTH")
        col.prop(s, "WAVE_SPEED")
        col.prop(s, "SEED")


class PARTICLEWAVES_PT_System(_PW_Sub):
    bl_label = "SYSTEM SETTINGS"
    bl_idname = "PARTICLEWAVES_PT_SYSTEM"
    bl_order = 30
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
        layout.operator("particlewaves.randomise_params", text="RANDOMISE")


class PARTICLEWAVES_PT_Advanced(_PW_Sub):
    bl_label = "ADVANCED SETTINGS"
    bl_idname = "PARTICLEWAVES_PT_ADVANCED"
    bl_order = 40
    bl_options = {'DEFAULT_CLOSED'}
    def draw(self, context):
        layout = self.layout
        s = self._s(layout, context);  
        if not s: return
        layout.prop(s, "AXIS_BIAS")