import bpy # type: ignore
import numpy as np # type: ignore
from bpy.app.handlers import persistent # type: ignore

def get_params(settings):
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
        AXIS_BIAS=(0.0, 0.0, 0.0),
        VEL_SMOOTH=settings.VEL_SMOOTH,
        STEP_CLAMP=settings.STEP_CLAMP,
        SOFTNESS=settings.SOFTNESS,
        OBJ_NAME="PARTICLEWAVE",
        DOT_NAME="PARTICLEDOT"
    )

def remove_obj_and_mesh(name):
    ob = bpy.data.objects.get(name)
    if ob:
        me = getattr(ob, "data", None)
        bpy.data.objects.remove(ob, do_unlink=True)
        if me:
            try: bpy.data.meshes.remove(me, do_unlink=True)
            except: pass

def fibonacci_sphere(n):
    i = np.arange(n, dtype=np.float64)
    ga = np.pi * (3.0 - np.sqrt(5.0))
    z  = 1.0 - (2.0*i + 1.0) / n
    r  = np.sqrt(np.maximum(0.0, 1.0 - z*z))
    th = ga * i
    x, y = np.cos(th)*r, np.sin(th)*r
    P = np.stack([x, y, z], axis=1)
    return P / np.linalg.norm(P, axis=1, keepdims=True)

def jitter_blue_noise(dirs, strength, rng):
    n = dirs.shape[0]
    spacing = 2.0 / np.sqrt(n)
    a = np.tile(np.array([0.0,0.0,1.0]), (n,1))
    a[np.abs(dirs[:,2])>0.9] = np.array([1.0,0.0,0.0])
    t = np.cross(dirs, a); t /= np.linalg.norm(t, axis=1, keepdims=True)
    b = np.cross(dirs, t)
    phi = rng.uniform(0, 2*np.pi, n)
    rad = (spacing * strength) * np.sqrt(rng.uniform(0,1,n))
    uvec = (t*np.cos(phi)[:,None] + b*np.sin(phi)[:,None])
    d2 = dirs + uvec*rad[:,None]
    d2 /= np.linalg.norm(d2, axis=1, keepdims=True)
    return d2

def make_points_object(name, verts):
    me = bpy.data.meshes.new(name + "Mesh")
    me.from_pydata([tuple(v) for v in verts], [], [])
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob

def ensure_dot_instance(name, radius, subdivs):
    import bmesh # type: ignore
    me = bpy.data.meshes.new(name + "Mesh")
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdivs, radius=radius)
    bm.to_mesh(me); bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob

def unit(v):
    n = np.linalg.norm(v)
    return v/n if n != 0 else v

# GLOBALS FOR ANIMATION STATE
P = None
V_prev = None
K = None
W = None
PHI = None
OMG = None
rng = None
params = None

def create_particle_wave(settings):
    global P, V_prev, K, W, PHI, OMG, rng, params
    params = get_params(settings)
    remove_obj_and_mesh(params["OBJ_NAME"])
    remove_obj_and_mesh(params["DOT_NAME"])
    rng = np.random.default_rng(params["SEED"])
    dirs0 = jitter_blue_noise(fibonacci_sphere(params["N_POINTS"]), 0.85, rng)
    P = dirs0.copy()
    V_prev = np.zeros_like(P)
    points_obj = make_points_object(params["OBJ_NAME"], P * params["RADIUS"])
    dot_obj = ensure_dot_instance(params["DOT_NAME"], params["DOT_RADIUS"], params["DOT_SUBDIVS"])
    dot_obj.parent = points_obj
    points_obj.instance_type = 'VERTS'
    points_obj.show_instancer_for_viewport = False
    points_obj.show_instancer_for_render = False
    NUM_MODES = params["NUM_MODES"]
    FREQ_BASE = params["FREQ_BASE"]
    AXIS_BIAS = np.array(params["AXIS_BIAS"], dtype=np.float64)
    K = rng.normal(size=(NUM_MODES,3))
    K = K / np.linalg.norm(K, axis=1, keepdims=True)
    K = K * (FREQ_BASE * rng.uniform(0.7, 1.3, (NUM_MODES,1)))
    W = rng.uniform(0.6, 1.0, NUM_MODES)
    PHI = rng.uniform(0, 2*np.pi, NUM_MODES)
    OMG = rng.uniform(0.6, 1.4, NUM_MODES) * params["FIELD_SPEED"] * 2*np.pi
    if np.linalg.norm(AXIS_BIAS) > 0:
        AXIS_BIAS = unit(AXIS_BIAS)
        K = (0.85*K + 0.15*AXIS_BIAS)
        K = K / np.linalg.norm(K, axis=1, keepdims=True)
    points_obj["particle_count"] = params["N_POINTS"]
    return points_obj, dot_obj

@persistent
def advect_points(scene):
    global P, V_prev, K, W, PHI, OMG, rng, params
    if P is None or V_prev is None or K is None:
        return
    fps = scene.render.fps
    dt  = 1.0 / fps
    t   = scene.frame_current / fps
    D     = P @ K.T
    phase = D + PHI + (OMG * t)
    C     = (W * np.cos(phase)).astype(np.float64)
    grad3 = C @ K
    dot_gn = np.sum(grad3 * P, axis=1, keepdims=True)
    g_tan  = grad3 - dot_gn * P
    g_norm = np.linalg.norm(g_tan, axis=1, keepdims=True)
    g_hat  = g_tan / (g_norm + 1e-9)
    iso_dir = np.cross(P, g_hat)
    iso_dir /= (np.linalg.norm(iso_dir, axis=1, keepdims=True) + 1e-9)
    if params["DIFFUSION"] > 0.0:
        R = rng.normal(size=P.shape)
        R -= (np.sum(R*P, axis=1, keepdims=True)) * P
        R /= (np.linalg.norm(R, axis=1, keepdims=True) + 1e-9)
    else:
        R = 0.0
    soft    = g_norm / (g_norm + params["SOFTNESS"])
    V_target= params["MOVE_SPEED"] * (params["ATTRACT_GAIN"] * soft * g_hat + params["ALONG_GAIN"] * iso_dir) + params["DIFFUSION"] * R

    V_prev = params["VEL_SMOOTH"] * V_prev + (1.0 - params["VEL_SMOOTH"]) * V_target
    step   = dt * V_prev
    step_len = np.linalg.norm(step, axis=1, keepdims=True) + 1e-9
    clamp    = np.minimum(step_len, params["STEP_CLAMP"]) / step_len
    step    *= clamp
    P = P + step
    P /= np.linalg.norm(P, axis=1, keepdims=True)
    obj = bpy.data.objects.get(params["OBJ_NAME"])
    if obj and obj.data:
        obj.data.vertices.foreach_set("co", (P * params["RADIUS"]).astype(np.float32).reshape(-1))
        obj.data.update()

def register_wave_animation_handler():
    if advect_points not in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.append(advect_points)

def unregister_wave_animation_handler():
    if advect_points in bpy.app.handlers.frame_change_pre:
        bpy.app.handlers.frame_change_pre.remove(advect_points)