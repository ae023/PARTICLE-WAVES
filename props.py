import bpy  # type: ignore


class ParticleWavesSettings(bpy.types.PropertyGroup):
    # USER-FACING CONTROLS FOR PARTICLE WAVES.

    # PARTICLE & FIELD
    PARTICLE_COUNT: bpy.props.IntProperty(  # type: ignore
        name="COUNT",
        description="Number of particles (instances)",
        default=50000,
        min=100,
        max=100000,
        soft_min=5000,
        soft_max=80000,
    )
    PARTICLE_RADIUS: bpy.props.FloatProperty(  # type: ignore
        name="RADIUS",
        description="Radius of each particle instance (icosphere)",
        default=0.0025,
        min=0.0002,
        max=0.05,
        soft_min=0.0005,
        soft_max=0.01,
    )
    SPHERE_RADIUS: bpy.props.FloatProperty(  # type: ignore
        name="FIELD",
        description="Radius of the spherical domain",
        default=1.0,
        min=0.1,
        max=5.0,
        soft_min=0.25,
        soft_max=2.0,
    )

    # WAVE (GLOBAL)
    WAVE_STRENGTH: bpy.props.FloatProperty(  # type: ignore
        name="AMPLITUDE",
        description="(Reserved) Global wave strength. Present for compatibility; not yet used by core.",
        default=1.0,
        min=0.0,
        max=25.0,
        soft_min=0.0,
        soft_max=5.0,
    )
    WAVE_SPEED: bpy.props.FloatProperty(  # type: ignore
        name="PHASE",
        description="Speed of the underlying field’s phase evolution",
        default=0.01,
        min=0.0001,
        max=2.0,
        soft_min=0.001,
        soft_max=0.2,
    )
    SEED: bpy.props.IntProperty(  # type: ignore
        name="SEED",
        description="Random seed for reproducible variation",
        default=0,
        min=0,
        max=999999,
    )

    # --- Field structure ---
    NUM_MODES: bpy.props.IntProperty(  # type: ignore
        name="BAND COUNT",
        description="Number of wave modes (higher = more complex interference)",
        default=4,
        min=1,
        max=32,
        soft_min=2,
        soft_max=10,
    )
    FREQ_BASE: bpy.props.FloatProperty(  # type: ignore
        name="BAND FREQUENCY",
        description="Base frequency scaling for mode directions (controls band scale)",
        default=1.2,
        min=0.1,
        max=10.0,
        soft_min=0.6,
        soft_max=2.5,
    )

    # MOTION / DYNAMICS
    MOVE_SPEED: bpy.props.FloatProperty(  # type: ignore
        name="DRIFT SPEED",
        description="Overall drift speed of particles across the sphere",
        default=0.05,
        min=0.001,
        max=0.5,
        soft_min=0.02,
        soft_max=0.15,
    )
    ATTRACT_GAIN: bpy.props.FloatProperty(  # type: ignore
        name="ATTRACT GAIN",
        description="Attraction toward ridges (gradient direction)",
        default=0.7,
        min=0.0,
        max=2.0,
        soft_min=0.2,
        soft_max=1.2,
    )
    ALONG_GAIN: bpy.props.FloatProperty(  # type: ignore
        name="TANGENTIAL GAIN",
        description="Sliding along isolines (tangential flow)",
        default=0.7,
        min=0.0,
        max=2.0,
        soft_min=0.2,
        soft_max=1.2,
    )
    DIFFUSION: bpy.props.FloatProperty(  # type: ignore
        name="DIFFUSION",
        description="Random walk amount (adds micro-variation)",
        default=0.002,
        min=0.0,
        max=0.02,
        soft_min=0.0,
        soft_max=0.005,
    )
    VEL_SMOOTH: bpy.props.FloatProperty(  # type: ignore
        name="VELOCITY SMOOTHING",
        description="Exponential smoothing of velocity (higher = smoother, slower response)",
        default=0.97,
        min=0.5,
        max=0.999,
        soft_min=0.9,
        soft_max=0.995,
        precision=3,
    )
    STEP_CLAMP: bpy.props.FloatProperty(  # type: ignore
        name="STEP LIMIT",
        description="Maximum travel per frame (stability clamp)",
        default=0.002,
        min=0.0001,
        max=0.02,
        soft_min=0.0005,
        soft_max=0.005,
        precision=4,
    )
    SOFTNESS: bpy.props.FloatProperty(  # type: ignore
        name="SOFTENING",
        description="Soft attraction near ridges (prevents snapping)",
        default=0.6,
        min=0.01,
        max=5.0,
        soft_min=0.2,
        soft_max=1.5,
    )

    # OPTIONAL AXIS BIAS (ADVANCED)
    AXIS_BIAS: bpy.props.FloatVectorProperty(  # type: ignore
        name="AXIS BIAS",
        description="Preferred axis for banding/flow (use small values; will be normalized in the solver)",
        default=(0.0, 0.0, 0.0),
        size=3,
        min=-1.0,
        max=1.0,
        subtype='DIRECTION',
    )

    # PRESETS ENUM
    WAVE_PRESET: bpy.props.EnumProperty(  # type: ignore
        name="WAVE PRESET",
        description="Choose a preset for wave patterns",
        items=[
            ('DEFAULT', "DEFAULT", ""),
            ('RIPPLES', "RIPPLES", ""),
            ('CHAOS', "CHAOS", ""),
            ('BANDS', "BANDS", ""),
            ('SOFT', "SOFT", ""),
        ],
        default='DEFAULT',
    )