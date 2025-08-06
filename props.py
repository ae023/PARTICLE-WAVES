import bpy # type: ignore

class ParticleWavesSettings(bpy.types.PropertyGroup):
    PARTICLE_COUNT: bpy.props.IntProperty(
        name="PARTICLE COUNT",
        default=50000,
        min=100,
        max=100000
    ) # type: ignore
    SPHERE_RADIUS: bpy.props.FloatProperty(
        name="SPHERE RADIUS",
        default=1.0,
        min=0.1,
        max=10.0
    ) # type: ignore
    PARTICLE_RADIUS: bpy.props.FloatProperty(
        name="PARTICLE RADIUS",
        default=0.0025,
        min=0.0001,
        max=0.05
    ) # type: ignore
    WAVE_STRENGTH: bpy.props.FloatProperty(
        name="WAVE STRENGTH",
        default=1.0,
        min=0.0,
        max=10.0
    ) # type: ignore
    WAVE_SPEED: bpy.props.FloatProperty(
        name="WAVE SPEED",
        default=0.008,
        min=0.0001,
        max=0.1
    ) # type: ignore
    SEED: bpy.props.IntProperty(
        name="SEED",
        description="Random seed for particle wave",
        default=237,
        min=0,
        max=999999
    ) # type: ignore
    NUM_MODES: bpy.props.IntProperty(
        name="BAND COUNT",
        description="NUMBER OF BANDS/RIDGES (2-8)",
        default=4,
        min=2,
        max=8
    ) # type: ignore
    FREQ_BASE: bpy.props.FloatProperty(
        name="BAND SIZE",
        description="BASE FREQUENCY FOR BAND SIZE (1.0–2.0)",
        default=1.2,
        min=0.5,
        max=3.0
    ) # type: ignore
    MOVE_SPEED: bpy.props.FloatProperty(
        name="DRIFT SPEED",
        description="OVERALL DRIFT SPEED",
        default=0.07,
        min=0.01,
        max=0.2
    ) # type: ignore
    ATTRACT_GAIN: bpy.props.FloatProperty(
        name="ATTRACT GAIN",
        description="ATTRACTION TO RIDGES",
        default=0.6,
        min=0.1,
        max=1.0
    ) # type: ignore
    ALONG_GAIN: bpy.props.FloatProperty(
        name="ALONG GAIN",
        description="GLIDE ALONG RIDGES",
        default=0.7,
        min=0.1,
        max=1.5
    ) # type: ignore
    DIFFUSION: bpy.props.FloatProperty(
        name="DIFFUSION",
        description="RANDOM WALK AMOUNT",
        default=0.001,
        min=0.0,
        max=0.01
    ) # type: ignore
    VEL_SMOOTH: bpy.props.FloatProperty(
        name="VELOCITY SMOOTH",
        description="SMOOTHNESS OF MOTION",
        default=0.97,
        min=0.9,
        max=0.99
    ) # type: ignore
    STEP_CLAMP: bpy.props.FloatProperty(
        name="STEP CLAMP",
        description="MAX TRAVEL PER FRAME",
        default=0.0012,
        min=0.0005,
        max=0.005
    ) # type: ignore
    SOFTNESS: bpy.props.FloatProperty(
        name="SOFTNESS",
        description="SOFT ATTRACTION NEAR RIDGES",
        default=0.6,
        min=0.1,
        max=1.0
    ) # type: ignore
    WAVE_PRESET: bpy.props.EnumProperty(
    name="WAVE PRESET",
    description="CHOOSE A PRESET FOR WAVE PATTERNS",
    items=[
        ('DEFAULT', "DEFAULT", ""),
        ('RIPPLES', "RIPPLES", ""),
        ('CHAOS', "CHAOS", ""),
        ('BANDS', "BANDS", ""),
        ('SOFT', "SOFT", ""),
    ],
    default='DEFAULT'
) # type: ignore