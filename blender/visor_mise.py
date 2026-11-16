# Visor Mise: HMD de cartón con celular (video passthrough)
# Blender 4.x / 5.x -> pestaña Scripting > Open > Run Script
# Frames 1-120: turntable | 121-220: vista explotada
import bpy, math

# ---------- Limpiar ----------
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete()
for c in (bpy.data.meshes, bpy.data.materials, bpy.data.curves):
    for d in list(c):
        c.remove(d)

sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, 220
sc.render.fps = 30
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080

# ---------- Materiales ----------
def mat(name, color, rough=0.6, metal=0.0, emit=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = 3
    return m

CARTON = mat("Carton", (0.32, 0.18, 0.08), 0.85)
CARTON_OSC = mat("CartonOscuro", (0.22, 0.12, 0.05), 0.9)
FOAM = mat("Fomi", (0.03, 0.03, 0.035), 0.95)
LIGA = mat("Liga", (0.01, 0.01, 0.01), 0.7)
CEL = mat("Celular", (0.02, 0.02, 0.025), 0.25, 0.3)
LENTE = mat("LenteCam", (0.01, 0.01, 0.01), 0.05, 0.8)
PANTALLA = mat("Pantalla", (0.02, 0.02, 0.02), 0.1, emit=(0.6, 0.85, 1.0))
CABEZA = mat("Maniqui", (0.45, 0.44, 0.42), 0.5)
TEXTO = mat("Texto", (1, 1, 1), 0.4)

def obj_set(o, m, bevel=0.0, seg=3):
    o.data.materials.append(m)
    if bevel:
        b = o.modifiers.new("Bevel", "BEVEL")
        b.width, b.segments = bevel, seg
    bpy.ops.object.shade_smooth() if bevel else None
    return o

def cube(name, size, loc, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return obj_set(o, m, bevel)

def cut(target, cutter):
    b = target.modifiers.new("Corte", "BOOLEAN")
    b.operation, b.object = "DIFFERENCE", cutter
    cutter.hide_render = cutter.hide_viewport = True
    cutter.parent = target

# ---------- Raíz (gira en turntable) ----------
bpy.ops.object.empty_add(location=(0, 0, 0))
root = bpy.context.active_object
root.name = "Visor_Root"

# ---------- Caja principal ----------
caja = cube("Caja", (0.17, 0.085, 0.10), (0, 0.0425, 0), CARTON, 0.006)
# Hueco para la nariz
bpy.ops.mesh.primitive_cylinder_add(radius=0.028, depth=0.2, location=(0, 0.03, -0.055), rotation=(math.radians(90), 0, 0))
cut(caja, bpy.context.active_object)
# Ranuras de ventilación (antiempañante por el vapor)
for i in (-1, 0, 1):
    cube(f"Ranura{i}", (0.03, 0.008, 0.05), (i * 0.045, 0.02, 0.05), CARTON)
    cut(caja, bpy.context.active_object)

# ---------- Fomi (contacto con la cara) ----------
fomi = cube("Fomi", (0.172, 0.018, 0.102), (0, -0.009, 0), FOAM, 0.008)
bpy.ops.mesh.primitive_cylinder_add(radius=0.03, depth=0.1, location=(0, -0.009, -0.055), rotation=(math.radians(90), 0, 0))
cut(fomi, bpy.context.active_object)

# ---------- Celular ----------
cel = cube("Celular", (0.16, 0.008, 0.075), (0, 0.089, 0), CEL, 0.004)
pant = cube("Pantalla", (0.152, 0.001, 0.068), (0, 0.0847, 0), PANTALLA)
pant.parent = cel
pant.matrix_parent_inverse = cel.matrix_world.inverted()
bpy.ops.mesh.primitive_cylinder_add(radius=0.006, depth=0.004, location=(-0.06, 0.094, 0.022), rotation=(math.radians(90), 0, 0))
cam = bpy.context.active_object
cam.name = "CamaraCel"
obj_set(cam, LENTE)
cam.parent = cel
cam.matrix_parent_inverse = cel.matrix_world.inverted()

# ---------- Tapa frontal (sostiene el cel) ----------
tapa = cube("Tapa", (0.176, 0.004, 0.104), (0, 0.095, 0), CARTON_OSC, 0.002)
bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.05, location=(-0.06, 0.095, 0.022), rotation=(math.radians(90), 0, 0))
cut(tapa, bpy.context.active_object)

# Texto MISE en la tapa
bpy.ops.object.text_add(location=(0.03, 0.0975, -0.035), rotation=(math.radians(90), 0, math.radians(180)))
txt = bpy.context.active_object
txt.name = "Logo"
txt.data.body = "MISE"
txt.data.size = 0.022
txt.data.extrude = 0.0006
txt.data.align_x = "CENTER"
txt.data.materials.append(TEXTO)
txt.parent = tapa
txt.matrix_parent_inverse = tapa.matrix_world.inverted()

# ---------- Liga trasera ----------
bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.04, major_segments=64, minor_segments=8, location=(0, -0.07, 0))
liga = bpy.context.active_object
liga.name = "Liga"
liga.scale = (0.092, 0.145, 0.15)
bpy.ops.object.transform_apply(scale=True)
obj_set(liga, LIGA)
bpy.ops.object.shade_smooth()

# ---------- Liga superior ----------
bpy.ops.mesh.primitive_torus_add(major_radius=1, minor_radius=0.04, major_segments=64, minor_segments=8,
                                 location=(0, -0.07, 0.0), rotation=(0, math.radians(90), 0))
top = bpy.context.active_object
top.name = "LigaSuperior"
top.scale = (0.15, 0.145, 0.12)
bpy.ops.object.transform_apply(scale=True)
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="DESELECT")
bpy.ops.object.mode_set(mode="OBJECT")
for v in top.data.vertices:
    v.select = v.co.z < 0.0
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.delete(type="VERT")
bpy.ops.object.mode_set(mode="OBJECT")
obj_set(top, LIGA)
bpy.ops.object.shade_smooth()

# ---------- Cabeza maniquí ----------
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(0, -0.115, 0.01))
cabeza = bpy.context.active_object
cabeza.name = "Maniqui"
cabeza.scale = (0.078, 0.1, 0.115)
bpy.ops.object.transform_apply(scale=True)
obj_set(cabeza, CABEZA)
bpy.ops.object.shade_smooth()

for o in (caja, fomi, cel, tapa, liga, top, cabeza):
    o.parent = root

# ---------- Animación ----------
def key(o, frame, path, value, idx=None):
    if idx is None:
        setattr(o, path, value)
        o.keyframe_insert(path, frame=frame)
    else:
        getattr(o, path)[idx] = value
        o.keyframe_insert(path, index=idx, frame=frame)

# Turntable 1-120
key(root, 1, "rotation_euler", math.radians(-30), 2)
key(root, 120, "rotation_euler", math.radians(330), 2)
key(root, 220, "rotation_euler", math.radians(330 + 20), 2)

# Explotada 130-170
EXP = {tapa: 0.07, cel: 0.04, fomi: -0.05, liga: -0.06, top: -0.06}
for o, d in EXP.items():
    y = o.location.y
    key(o, 130, "location", y, 1)
    key(o, 170, "location", y + d, 1)
key(cabeza, 128, "hide_render", False)
key(cabeza, 129, "hide_render", True)
key(cabeza, 128, "hide_viewport", False)
key(cabeza, 129, "hide_viewport", True)

for o in bpy.data.objects:
    if o.animation_data and o.animation_data.action:
        try:
            for fc in o.animation_data.action.fcurves:
                if fc.data_path == "rotation_euler":
                    for k in fc.keyframe_points:
                        k.interpolation = "LINEAR"
        except AttributeError:
            pass  # Blender 5 (acciones por capas): queda en Bezier

# ---------- Cámara ----------
bpy.ops.object.empty_add(location=(0, -0.02, 0))
target = bpy.context.active_object
target.name = "Target"
bpy.ops.object.camera_add(location=(0.58, 0.58, 0.22))
camera = bpy.context.active_object
camera.data.lens = 50
t = camera.constraints.new("TRACK_TO")
t.target, t.track_axis, t.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"
sc.camera = camera

# ---------- Luces ----------
def area(loc, energy, size, color=(1, 1, 1)):
    bpy.ops.object.light_add(type="AREA", location=loc)
    l = bpy.context.active_object
    l.data.energy, l.data.size, l.data.color = energy, size, color
    c = l.constraints.new("TRACK_TO")
    c.target, c.track_axis, c.up_axis = target, "TRACK_NEGATIVE_Z", "UP_Y"

area((0.5, 0.3, 0.5), 12, 0.5, (1, 0.95, 0.88))
area((-0.5, 0.2, 0.2), 4, 0.6, (0.85, 0.9, 1))
area((0, -0.5, 0.4), 8, 0.3)

# ---------- Fondo ----------
w = sc.world or bpy.data.worlds.new("World")
sc.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.92, 0.9, 0.87, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.35

# ---------- Render ----------
for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
    try:
        sc.render.engine = eng
        break
    except TypeError:
        pass
try:
    sc.view_settings.view_transform = "AgX"
except TypeError:
    sc.view_settings.view_transform = "Filmic"
try:
    sc.render.image_settings.media_type = "VIDEO"  # Blender 5
except AttributeError:
    pass
try:
    sc.render.image_settings.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"
    sc.render.ffmpeg.codec = "H264"
except TypeError:
    pass
sc.render.filepath = "//visor_mise_"
print("Visor Mise listo")
