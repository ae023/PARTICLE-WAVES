import bpy                               # type: ignore
import numpy as np                       # type: ignore
from bpy.app.handlers import persistent  # type: ignore



# PARAMATER EXTRACTION (KEEPS API)
def get_params(settings):
    # COLLECT LOW LEVEL SIMULATION PARAMATERS FROM UI SETTINGS (KEEPS BACKWARD COMPATIBILITY).
    # OPTIONAL FUTURE PROP: AXIS_BIAS (VECTORPROPERTY). DEFAULT TO (0,0,0).
    axis_bias = getattr(settings, "AXIS_BIAS", (0.0, 0.0, 0.0))

    return dict(
        N_POINTS=settings.PARTICLE_COUNT,
        RADIUS=settings.SPHERE_RADIUS,
        DOT_RADIUS=settings.PARTICLE_RADIUS,
        DOT_SUBDIVS=1,
        SEED=settings.SEED,
        NUM_MODES=settings.NUM_MODES,
        FREQ_BASE=settings.FREQ_BASE,
        FIELD_SPEED=settings.WAVE_SPEED,
        MOVE_SPEED=settings.MOVE_SPEED,
        ATTRACT_GAIN=settings.ATTRACT_GAIN,
        ALONG_GAIN=settings.ALONG_GAIN,
        DIFFUSION=settings.DIFFUSION,
        AXIS_BIAS=axis_bias,
        VEL_SMOOTH=settings.VEL_SMOOTH,
        STEP_CLAMP=settings.STEP_CLAMP,
        SOFTNESS=settings.SOFTNESS,
        OBJ_NAME="PARTICLEWAVE",
        DOT_NAME="PARTICLEDOT",
    )


# UTILITIES
def remove_obj_and_mesh(name):
    ob = bpy.data.objects.get(name)
    if ob:
        me = getattr(ob, "data", None)
        bpy.data.objects.remove(ob, do_unlink=True)
        if me:
            try:
                bpy.data.meshes.remove(me, do_unlink=True)
            except Exception:
                pass


def fibonacci_sphere(n: int):
    # EVEN POINT DISTRIBUTION ON A SPHERE (UNIT RADIUS).
    i = np.arange(n, dtype=np.float32)
    ga = np.pi * (3.0 - np.sqrt(5.0))
    z = 1.0 - (2.0 * i + 1.0) / np.float32(n)
    r = np.sqrt(np.maximum(0.0, 1.0 - z * z))
    th = ga * i
    x, y = np.cos(th) * r, np.sin(th) * r
    P = np.stack([x, y, z], axis=1)
    # NORMALISE TO BE SAFE (FLOAT32).
    return P / np.linalg.norm(P, axis=1, keepdims=True).astype(np.float32)


def jitter_blue_noise(dirs, strength, rng):
    # LOCAL JITTER IN EACH TANGENT PLANE TO REDUCE RESIDUAL REGULARITY.
    n = dirs.shape[0]
    spacing = np.float32(2.0) / np.sqrt(np.float32(n))
    a = np.tile(np.array([0.0, 0.0, 1.0], dtype=np.float32), (n, 1))
    a[np.abs(dirs[:, 2]) > 0.9] = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    t = np.cross(dirs, a)
    t /= np.linalg.norm(t, axis=1, keepdims=True) + 1e-9
    b = np.cross(dirs, t)
    phi = rng.uniform(0, 2 * np.pi, n).astype(np.float32)
    rad = (spacing * np.float32(strength)) * np.sqrt(rng.uniform(0, 1, n)).astype(np.float32)
    uvec = (t * np.cos(phi)[:, None] + b * np.sin(phi)[:, None]).astype(np.float32)
    d2 = dirs + uvec * rad[:, None]
    d2 /= np.linalg.norm(d2, axis=1, keepdims=True) + 1e-9
    return d2.astype(np.float32)


def make_points_object(name, verts):
    # CREATE A MESH WITH GIVEN VERTS (NO EDGES/FACES).
    me = bpy.data.meshes.new(name + "Mesh")
    me.from_pydata([tuple(v) for v in verts], [], [])
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def ensure_dot_instance(name, radius, subdivs):
    import bmesh  # type: ignore

    me = bpy.data.meshes.new(name + "Mesh")
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=int(subdivs), radius=float(radius))
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n != 0 else v


# GLOBAL SIMULATION STATE
P = None          # POSITIONS ON UNIT SPHERE (N,3) FLOAT32
V_prev = None     # VELOCITY INTEGRATOR (N,3) FLOAT32
K = None          # MODE DIRECTIONS (M,3) FLOAT32 (NORMALISED * FREQ)
W = None          # MODE WEIGHTS (M,) FLOAT32
PHI = None        # BASE PHASES (M,) FLOAT32
OMG = None        # ANGULAR SPEEDS (M,) FLOAT 32
rng = None        # NP.RANDOM.GENERATOR
params = None     # DICTIONARY FROM GET_PARAMS
_OBJ_CACHE = None # CACHED OBJECT REFERENCE


# CONSTRUCTION
def create_particle_wave(settings):
    # BUILD OR REBUILD THE SIMULATION STATE AND BLENDER OBJECTS FROM SETTINGS.
    global P, V_prev, K, W, PHI, OMG, rng, params, _OBJ_CACHE

    params = get_params(settings)

    # CLEAN ANY PREVIOUS OBJECTS
    remove_obj_and_mesh(params["OBJ_NAME"])
    remove_obj_and_mesh(params["DOT_NAME"])

    # RNG
    rng = np.random.default_rng(int(params["SEED"]))

    # SEED POINTS ON UNIT SPHERE WITH JITTER (FLOAT32)
    dirs0 = jitter_blue_noise(fibonacci_sphere(int(params["N_POINTS"])), 0.85, rng)
    P = dirs0.astype(np.float32).copy()
    V_prev = np.zeros_like(P, dtype=np.float32)

    # CREATE INSTANCER & INSTANCE OBJECT
    points_obj = make_points_object(params["OBJ_NAME"], (P * params["RADIUS"]).astype(np.float32))
    dot_obj = ensure_dot_instance(params["DOT_NAME"], params["DOT_RADIUS"], params["DOT_SUBDIVS"])
    dot_obj.parent = points_obj
    points_obj.instance_type = 'VERTS'
    points_obj.show_instancer_for_viewport = False
    points_obj.show_instancer_for_render = False

    # BUILD MULTI-MODE FIELD
    NUM_MODES = int(params["NUM_MODES"])
    FREQ_BASE = np.float32(params["FREQ_BASE"])
    AXIS_BIAS = np.array(params["AXIS_BIAS"], dtype=np.float32)

    K = rng.normal(size=(NUM_MODES, 3)).astype(np.float32)
    K /= (np.linalg.norm(K, axis=1, keepdims=True).astype(np.float32) + 1e-9)
    K *= (FREQ_BASE * rng.uniform(0.7, 1.3, (NUM_MODES, 1)).astype(np.float32))

    W = rng.uniform(0.6, 1.0, NUM_MODES).astype(np.float32)
    PHI = rng.uniform(0.0, 2 * np.pi, NUM_MODES).astype(np.float32)
    OMG = (rng.uniform(0.6, 1.4, NUM_MODES).astype(np.float32)
           * np.float32(params["FIELD_SPEED"]) * np.float32(2 * np.pi))

    if np.linalg.norm(AXIS_BIAS) > 0:
        AXIS_BIAS = unit(AXIS_BIAS.astype(np.float32))
        K = (0.85 * K + 0.15 * AXIS_BIAS).astype(np.float32)
        K /= (np.linalg.norm(K, axis=1, keepdims=True).astype(np.float32) + 1e-9)

    # CACHE OBJECT & METADATA
    points_obj["particle_count"] = int(params["N_POINTS"])
    _OBJ_CACHE = points_obj

    return points_obj, dot_obj


# SIMULATION STEP
@persistent
def advect_points(scene):
    # ADVANCE ONE FRAME OF THE SIMULATION & UPDATE MESH VERTICES.
    global P, V_prev, K, W, PHI, OMG, rng, params, _OBJ_CACHE

    if P is None or V_prev is None or K is None or params is None:
        return

    # TIME
    fps = max(1, int(scene.render.fps))
    dt = np.float32(1.0 / fps)
    t = np.float32(scene.frame_current / fps)

    # FEILD EVALUATION
    # PROJECTIONS TO MODE DIRECTIONS
    D = P @ K.T  # (N, M)
    phase = D + PHI + (OMG * t)  # (N, M) BROADCAST
    C = (W * np.cos(phase)).astype(np.float32)  # (N, M)

    # GRADIENT IN R^3 FROM WEIGHTED COSINES, THEN SPLIT INTO TANGENT/ISO COMPONENTS
    grad3 = (C @ K).astype(np.float32)  # (N, 3)

    # REMOVE RADIAL COMPONENT TO KEEP MOTION ON THE SPHERE (TANGENT PROJECTION)
    dot_gn = np.sum(grad3 * P, axis=1, keepdims=True).astype(np.float32)
    g_tan = grad3 - dot_gn * P
    g_norm = np.linalg.norm(g_tan, axis=1, keepdims=True).astype(np.float32)
    g_hat = g_tan / (g_norm + 1e-9)

    iso_dir = np.cross(P, g_hat).astype(np.float32)
    iso_dir /= (np.linalg.norm(iso_dir, axis=1, keepdims=True).astype(np.float32) + 1e-9)

    # DIFFUSION ORTHOGONAL TO RADIUS
    if params["DIFFUSION"] > 0.0:
        R = rng.normal(size=P.shape).astype(np.float32)
        R -= (np.sum(R * P, axis=1, keepdims=True).astype(np.float32)) * P
        R /= (np.linalg.norm(R, axis=1, keepdims=True).astype(np.float32) + 1e-9)
    else:
        R = np.zeros_like(P, dtype=np.float32)

    # SOFT ATTRACTION NEAR RIDGES (PREVENTS SNAPPING)
    soft = g_norm / (g_norm + np.float32(params["SOFTNESS"]))

    # TARGET VELOCITY: BLEND OF ATTRACTION, SLIDING, & DIFFUSION
    V_target = (
        np.float32(params["MOVE_SPEED"])
        * (np.float32(params["ATTRACT_GAIN"]) * soft * g_hat
           + np.float32(params["ALONG_GAIN"]) * iso_dir)
        + np.float32(params["DIFFUSION"]) * R
    ).astype(np.float32)

    # EXPONENTIAL SMOOTHING TOWARDS TARGET VELOCITY
    V_prev = (np.float32(params["VEL_SMOOTH"]) * V_prev
              + (np.float32(1.0) - np.float32(params["VEL_SMOOTH"])) * V_target)

    # STEP WITH CLAMP FOR STTABILITY
    step = (dt * V_prev).astype(np.float32)
    step_len = (np.linalg.norm(step, axis=1, keepdims=True).astype(np.float32) + 1e-9)
    clamp = np.minimum(step_len, np.float32(params["STEP_CLAMP"])) / step_len
    step *= clamp

    # INTEGRATE & RE-NORMALISE TO UNIT SPHERE
    P = (P + step).astype(np.float32)
    P /= (np.linalg.norm(P, axis=1, keepdims=True).astype(np.float32) + 1e-9)

    # BLENDER MESH UPDATE
    obj = _OBJ_CACHE
    if obj is None or obj.name not in bpy.data.objects:
        obj = bpy.data.objects.get(params["OBJ_NAME"])
        _OBJ_CACHE = obj

    if obj and obj.data and len(obj.data.vertices) == P.shape[0]:
        obj.data.vertices.foreach_set("co", (P * np.float32(params["RADIUS"])).astype(np.float32).reshape(-1))
        obj.data.update()


# FRAME HANDLERS
def register_wave_animation_handler():
    if advect_points not in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.append(advect_points)


def unregister_wave_animation_handler():
    if advect_points in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(advect_points)