import bpy  # type: ignore
import numpy as np  # type: ignore
from bpy.app.handlers import persistent  # type: ignore


# ──────────────────────────────────────────────────────────────────────────────
# Parameter plumbing
# ──────────────────────────────────────────────────────────────────────────────

def get_params(settings):
    """Read all runtime params from the Scene settings with safe fallbacks."""
    axis_bias = getattr(settings, "AXIS_BIAS", (0.0, 0.0, 0.0))
    return dict(
        N_POINTS=int(settings.PARTICLE_COUNT),
        RADIUS=float(settings.SPHERE_RADIUS),
        DOT_RADIUS=float(settings.PARTICLE_RADIUS),
        DOT_SUBDIVS=1,  # keep it fast; can expose later
        SEED=int(settings.SEED),

        NUM_MODES=int(settings.NUM_MODES),
        FREQ_BASE=float(settings.FREQ_BASE),
        FIELD_SPEED=float(settings.WAVE_SPEED),

        MOVE_SPEED=float(settings.MOVE_SPEED),
        ATTRACT_GAIN=float(settings.ATTRACT_GAIN),
        ALONG_GAIN=float(settings.ALONG_GAIN),
        DIFFUSION=float(settings.DIFFUSION),

        AXIS_BIAS=tuple(map(float, axis_bias)),
        VEL_SMOOTH=float(settings.VEL_SMOOTH),
        STEP_CLAMP=float(settings.STEP_CLAMP),
        SOFTNESS=float(settings.SOFTNESS),

        OBJ_NAME="PARTICLEWAVE",
        DOT_NAME="PARTICLEDOT",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Utilities
# ──────────────────────────────────────────────────────────────────────────────

def remove_obj_and_mesh(name: str):
    """Delete object and its mesh (if any), safely."""
    ob = bpy.data.objects.get(name)
    if ob:
        me = getattr(ob, "data", None)
        bpy.data.objects.remove(ob, do_unlink=True)
        if me:
            try:
                bpy.data.meshes.remove(me, do_unlink=True)
            except Exception:
                pass


def ensure_dot_emission_material(name: str = "PW_Emit_White", strength: float = 1.0):
    """Create or return a simple white Emission material for PARTICLEDOT."""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nt = mat.node_tree
        nt.nodes.clear()
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        emi = nt.nodes.new("ShaderNodeEmission")
        emi.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
        emi.inputs["Strength"].default_value = float(strength)
        nt.links.new(emi.outputs["Emission"], out.inputs["Surface"])
    return mat


def fibonacci_sphere(n: int) -> np.ndarray:
    """Even-ish points on a unit sphere via golden-angle spiral (float32)."""
    i = np.arange(n, dtype=np.float32)
    ga = np.float32(np.pi * (3.0 - np.sqrt(5.0)))
    z = np.float32(1.0) - (2.0 * i + np.float32(1.0)) / np.float32(n)
    r = np.sqrt(np.maximum(np.float32(0.0), np.float32(1.0) - z * z))
    th = ga * i
    x, y = np.cos(th) * r, np.sin(th) * r
    P = np.stack([x, y, z], axis=1).astype(np.float32)
    P /= (np.linalg.norm(P, axis=1, keepdims=True).astype(np.float32) + 1e-9)
    return P


def jitter_blue_noise(dirs: np.ndarray, strength: float, rng: np.random.Generator) -> np.ndarray:
    """
    Tangential jitter to reduce visible structure; keeps points on the sphere.
    'strength' is in units of approximate neighbor spacing.
    """
    n = dirs.shape[0]
    spacing = np.float32(2.0) / np.sqrt(np.float32(n))

    # Build a local tangent basis for each direction
    a = np.tile(np.array([0.0, 0.0, 1.0], dtype=np.float32), (n, 1))
    a[np.abs(dirs[:, 2]) > 0.9] = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    t = np.cross(dirs, a)
    t /= (np.linalg.norm(t, axis=1, keepdims=True).astype(np.float32) + 1e-9)
    b = np.cross(dirs, t)

    phi = rng.uniform(0.0, 2.0 * np.pi, n).astype(np.float32)
    rad = (spacing * np.float32(strength)) * np.sqrt(rng.uniform(0.0, 1.0, n)).astype(np.float32)
    uvec = (t * np.cos(phi)[:, None] + b * np.sin(phi)[:, None]).astype(np.float32)
    d2 = dirs + uvec * rad[:, None]
    d2 /= (np.linalg.norm(d2, axis=1, keepdims=True).astype(np.float32) + 1e-9)
    return d2.astype(np.float32)


def make_points_object(name: str, verts: np.ndarray):
    """Create a mesh object where each vertex is an instance point."""
    me = bpy.data.meshes.new(name + "Mesh")
    me.from_pydata([tuple(map(float, v)) for v in verts], [], [])
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def ensure_dot_instance(name: str, radius: float, subdivs: int):
    """Create an icosphere to instance on points and assign emission material."""
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

    mat = ensure_dot_emission_material()
    me.materials.clear()
    me.materials.append(mat)

    return ob


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return (v / n) if n != 0.0 else v


# ──────────────────────────────────────────────────────────────────────────────
# Global sim state (held in-memory while Blender session lives)
# ──────────────────────────────────────────────────────────────────────────────

P = None          # (N, 3) positions on unit sphere (float32)
V_prev = None     # (N, 3) smoothed velocity (float32)
K = None          # (M, 3) mode directions/frequencies (float32)
W = None          # (M,)   mode weights (float32)
PHI = None        # (M,)   mode static phases (float32)
OMG = None        # (M,)   mode angular speeds (float32)
rng = None        # np.random.Generator
params = None     # dict of runtime parameters
_OBJ_CACHE = None # cache the points object for faster foreach_set


# ──────────────────────────────────────────────────────────────────────────────
# Build / simulate
# ──────────────────────────────────────────────────────────────────────────────

def create_particle_wave(settings):
    """(Re)build the points + instance objects and initialize the field."""
    global P, V_prev, K, W, PHI, OMG, rng, params, _OBJ_CACHE

    params = get_params(settings)

    # Clean previous objects
    remove_obj_and_mesh(params["OBJ_NAME"])
    remove_obj_and_mesh(params["DOT_NAME"])

    rng = np.random.default_rng(int(params["SEED"]))

    # Initial positions
    dirs0 = jitter_blue_noise(
        fibonacci_sphere(int(params["N_POINTS"])), strength=0.85, rng=rng
    )
    P = dirs0.astype(np.float32).copy()
    V_prev = np.zeros_like(P, dtype=np.float32)

    # Scene objects
    points_obj = make_points_object(params["OBJ_NAME"], (P * np.float32(params["RADIUS"])))
    dot_obj = ensure_dot_instance(params["DOT_NAME"], params["DOT_RADIUS"], params["DOT_SUBDIVS"])

    # Instance along vertices
    dot_obj.parent = points_obj
    points_obj.instance_type = 'VERTS'
    points_obj.show_instancer_for_viewport = False
    points_obj.show_instancer_for_render = False

    # Field modes
    M = int(params["NUM_MODES"])
    FREQ_BASE = np.float32(params["FREQ_BASE"])
    AXIS_BIAS = np.array(params["AXIS_BIAS"], dtype=np.float32)

    K = rng.normal(size=(M, 3)).astype(np.float32)
    K /= (np.linalg.norm(K, axis=1, keepdims=True).astype(np.float32) + 1e-9)
    K *= (FREQ_BASE * rng.uniform(0.7, 1.3, (M, 1)).astype(np.float32))

    W = rng.uniform(0.6, 1.0, M).astype(np.float32)
    PHI = rng.uniform(0.0, 2.0 * np.pi, M).astype(np.float32)
    OMG = (rng.uniform(0.6, 1.4, M).astype(np.float32)
           * np.float32(params["FIELD_SPEED"]) * np.float32(2.0 * np.pi))

    # Optional bias toward a preferred axis
    if float(np.linalg.norm(AXIS_BIAS)) > 0.0:
        AXIS_BIAS = unit(AXIS_BIAS.astype(np.float32))
        K = (np.float32(0.85) * K + np.float32(0.15) * AXIS_BIAS).astype(np.float32)
        K /= (np.linalg.norm(K, axis=1, keepdims=True).astype(np.float32) + 1e-9)

    # Meta
    points_obj["particle_count"] = int(params["N_POINTS"])
    _OBJ_CACHE = points_obj

    return points_obj, dot_obj


@persistent
def advect_points(scene):
    """Frame-change handler (or manual call) to advance the particle field."""
    global P, V_prev, K, W, PHI, OMG, rng, params, _OBJ_CACHE

    # Safety: nothing to do until built
    if P is None or V_prev is None or K is None or params is None:
        return

    fps = max(1, int(scene.render.fps))
    dt = np.float32(1.0 / fps)
    t = np.float32(scene.frame_current / fps)

    # Evaluate multi-mode cosine field
    D = P @ K.T                     # (N,M)
    phase = D + PHI + (OMG * t)     # (N,M)
    C = (W * np.cos(phase)).astype(np.float32)  # (N,M)
    grad3 = (C @ K).astype(np.float32)          # (N,3)

    # Tangential gradient & iso-direction (stay on sphere)
    dot_gn = np.sum(grad3 * P, axis=1, keepdims=True).astype(np.float32)
    g_tan = grad3 - dot_gn * P
    g_norm = np.linalg.norm(g_tan, axis=1, keepdims=True).astype(np.float32)
    g_hat = g_tan / (g_norm + 1e-9)

    iso_dir = np.cross(P, g_hat).astype(np.float32)
    iso_dir /= (np.linalg.norm(iso_dir, axis=1, keepdims=True).astype(np.float32) + 1e-9)

    # Optional diffusion (blue noise on the tangent plane)
    if params["DIFFUSION"] > 0.0:
        R = rng.normal(size=P.shape).astype(np.float32)
        R -= (np.sum(R * P, axis=1, keepdims=True).astype(np.float32)) * P
        R /= (np.linalg.norm(R, axis=1, keepdims=True).astype(np.float32) + 1e-9)
    else:
        R = np.zeros_like(P, dtype=np.float32)

    # Soft attraction near ridges (prevents harsh snapping)
    soft = g_norm / (g_norm + np.float32(params["SOFTNESS"]))

    # Target velocity (tangent only), then exponential smoothing
    V_target = (
        np.float32(params["MOVE_SPEED"])
        * (np.float32(params["ATTRACT_GAIN"]) * soft * g_hat
           + np.float32(params["ALONG_GAIN"]) * iso_dir)
        + np.float32(params["DIFFUSION"]) * R
    ).astype(np.float32)

    V_prev[:] = (
        np.float32(params["VEL_SMOOTH"]) * V_prev
        + (np.float32(1.0) - np.float32(params["VEL_SMOOTH"])) * V_target
    )

    # Step with per-frame clamp for stability
    step = (dt * V_prev).astype(np.float32)
    step_len = (np.linalg.norm(step, axis=1, keepdims=True).astype(np.float32) + 1e-9)
    clamp = np.minimum(step_len, np.float32(params["STEP_CLAMP"])) / step_len
    step *= clamp

    # Move and renormalize back to the unit sphere
    P[:] = (P + step).astype(np.float32)
    P[:] /= (np.linalg.norm(P, axis=1, keepdims=True).astype(np.float32) + 1e-9)

    # Push updated positions to the mesh (cached lookup)
    obj = _OBJ_CACHE
    if obj is None or obj.name not in bpy.data.objects:
        obj = bpy.data.objects.get(params["OBJ_NAME"])
        _OBJ_CACHE = obj

    if obj and obj.data and len(obj.data.vertices) == P.shape[0]:
        obj.data.vertices.foreach_set("co", (P * np.float32(params["RADIUS"])).reshape(-1))
        obj.data.update()


def register_wave_animation_handler():
    """Enable frame-change handler once."""
    if advect_points not in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.append(advect_points)


def unregister_wave_animation_handler():
    """Disable frame-change handler if present."""
    if advect_points in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(advect_points)