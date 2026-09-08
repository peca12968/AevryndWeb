import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v11.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v12.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v12.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "face-v12"


def gaussian(value, center, spread):
    return math.exp(-0.5 * ((value - center) / spread) ** 2)


def segment_distance(px, pz, ax, az, bx, bz):
    abx, abz = bx - ax, bz - az
    length_squared = abx * abx + abz * abz
    t = max(0.0, min(1.0, ((px - ax) * abx + (pz - az) * abz) / length_squared))
    qx, qz = ax + abx * t, az + abz * t
    return math.hypot(px - qx, pz - qz)


def sculpt_secondary_forms(body):
    inverse = body.matrix_world.inverted()
    changed = 0
    maximum = 0.0
    components = {"cheek": 0.0, "tear_trough": 0.0, "philtrum": 0.0, "nasolabial": 0.0, "chin": 0.0}
    for vertex in body.data.vertices:
        source = body.matrix_world @ vertex.co
        if source.y > -0.090 or not (1.445 <= source.z <= 1.635) or abs(source.x) > 0.095:
            continue
        front = max(0.0, min(1.0, (-source.y - 0.090) / 0.055))
        cheek = gaussian(abs(source.x), 0.057, 0.023) * gaussian(source.z, 1.568, 0.030) * front
        tear = gaussian(abs(source.x), 0.036, 0.020) * gaussian(source.z, 1.589, 0.009) * front
        philtrum = gaussian(source.x, 0.0, 0.0065) * gaussian(source.z, 1.551, 0.014) * front
        side = 1.0 if source.x >= 0.0 else -1.0
        fold_distance = segment_distance(abs(source.x), source.z, 0.018, 1.558, 0.038, 1.521)
        nasolabial = math.exp(-0.5 * (fold_distance / 0.0045) ** 2) * front
        nasolabial *= max(0.0, min(1.0, (abs(source.x) - 0.010) / 0.018))
        chin = gaussian(abs(source.x), 0.020, 0.025) * gaussian(source.z, 1.477, 0.018) * front
        target = source.copy()
        target.y -= 0.00120 * cheek
        target.y += 0.00048 * tear + 0.00062 * philtrum + 0.00038 * nasolabial
        target.y -= 0.00072 * chin
        target.x += side * 0.00022 * cheek
        delta = (target - source).length
        if delta > 1e-8:
            vertex.co = inverse @ target
            changed += 1
            maximum = max(maximum, delta)
            components["cheek"] = max(components["cheek"], 0.00120 * cheek)
            components["tear_trough"] = max(components["tear_trough"], 0.00048 * tear)
            components["philtrum"] = max(components["philtrum"], 0.00062 * philtrum)
            components["nasolabial"] = max(components["nasolabial"], 0.00038 * nasolabial)
            components["chin"] = max(components["chin"], 0.00072 * chin)
    body.data.update()
    body["aevrynd_secondary_form_revision"] = 12
    body["aevrynd_secondary_form_vertices"] = changed
    body["aevrynd_secondary_form_max_delta_m"] = maximum
    return changed, maximum, components


def add_skin_tone_attribute(body):
    name = "AevryndSkinTone"
    existing = body.data.color_attributes.get(name)
    if existing:
        body.data.color_attributes.remove(existing)
    colors = body.data.color_attributes.new(name=name, type="BYTE_COLOR", domain="POINT")
    minimum = [1.0, 1.0, 1.0]
    for vertex, entry in zip(body.data.vertices, colors.data):
        point = body.matrix_world @ vertex.co
        front = max(0.0, min(1.0, (-point.y - 0.075) / 0.065))
        cheek = gaussian(abs(point.x), 0.058, 0.028) * gaussian(point.z, 1.563, 0.035) * front
        nose = gaussian(point.x, 0.0, 0.024) * gaussian(point.z, 1.570, 0.042) * front
        under_eye = gaussian(abs(point.x), 0.036, 0.024) * gaussian(point.z, 1.592, 0.013) * front
        ear = gaussian(abs(point.x), 0.098, 0.014) * gaussian(point.z, 1.585, 0.055)
        redness = min(1.0, 0.65 * cheek + 0.32 * nose + 0.42 * ear)
        shadow = min(1.0, 0.55 * under_eye)
        color = (
            1.0 - 0.030 * shadow,
            1.0 - 0.050 * redness - 0.035 * shadow,
            1.0 - 0.075 * redness - 0.025 * shadow,
            1.0,
        )
        entry.color = color
        for index in range(3):
            minimum[index] = min(minimum[index], color[index])

    skin = body.data.materials[0]
    nodes = skin.node_tree.nodes
    links = skin.node_tree.links
    for node in list(nodes):
        if node.name in {"Aevrynd Skin Tone Attribute", "Aevrynd Skin Tone Multiply"}:
            nodes.remove(node)
    shader = nodes.get("Principled BSDF")
    base = nodes.get("Aevrynd Runtime BaseColor")
    attribute = nodes.new("ShaderNodeVertexColor")
    attribute.name = "Aevrynd Skin Tone Attribute"
    attribute.layer_name = name
    multiply = nodes.new("ShaderNodeMixRGB")
    multiply.name = "Aevrynd Skin Tone Multiply"
    multiply.blend_type = "MULTIPLY"
    multiply.inputs[0].default_value = 1.0
    for link in list(shader.inputs["Base Color"].links):
        links.remove(link)
    if base:
        links.new(base.outputs["Color"], multiply.inputs[1])
    else:
        multiply.inputs[1].default_value = shader.inputs["Base Color"].default_value
    links.new(attribute.outputs["Color"], multiply.inputs[2])
    links.new(multiply.outputs["Color"], shader.inputs["Base Color"])
    skin["aevrynd_skin_tone_revision"] = 12
    return name, minimum


def surface(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    return BVHTree.FromObject(evaluated, depsgraph), evaluated.matrix_world, evaluated.matrix_world.inverted()


def front_point(surface_data, x, z, offset=0.00035):
    tree, matrix, inverse = surface_data
    origin = Vector((x, -0.35, z))
    direction = Vector((0.0, 1.0, 0.0))
    location, normal, _, _ = tree.ray_cast(inverse @ origin, (inverse.to_3x3() @ direction).normalized(), 0.6)
    if location is None:
        raise RuntimeError(f"face surface miss at {x}, {z}")
    point = matrix @ location
    normal_world = (matrix.inverted().transposed().to_3x3() @ normal).normalized()
    if normal_world.y > 0.0:
        normal_world.negate()
    return point + normal_world * offset


def layer_material(name, color, roughness, emission=0.0):
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    if shader.inputs.get("Specular IOR Level"):
        shader.inputs["Specular IOR Level"].default_value = 0.18
    if emission and shader.inputs.get("Emission Color"):
        shader.inputs["Emission Color"].default_value = color
        shader.inputs["Emission Strength"].default_value = emission
    return result


def parent_head(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


def eyelid_fold(name, center_x, surface_data, fold_material, rig):
    columns = 32
    vertices = []
    for index in range(columns):
        t = index / (columns - 1) * 2.0 - 1.0
        x = center_x + t * 0.0172
        arc = math.sqrt(max(0.0, 1.0 - t * t))
        center_z = 1.6135 + 0.0062 * arc
        vertices.append(front_point(surface_data, x, center_z - 0.00017, 0.00042))
        vertices.append(front_point(surface_data, x, center_z + 0.00017, 0.00042))
    faces = []
    for index in range(columns - 1):
        a = index * 2
        faces.append((a, a + 1, a + 3, a + 2))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(fold_material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    obj["aevrynd_role"] = "upper_eyelid_fold"
    obj["aevrynd_face_revision"] = 12
    obj["aevrynd_surface_offset_m"] = 0.00042
    parent_head(obj, rig)
    return obj


def catchlight(name, center, catchlight_material, rig):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.00078, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name + "Mesh"
    obj.data.materials.append(catchlight_material)
    obj["aevrynd_role"] = "eye_catchlight"
    obj["aevrynd_face_revision"] = 12
    parent_head(obj, rig)
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target):
    scene = bpy.context.scene
    scene.frame_set(1)
    camera.data.lens = 86
    camera.location = location
    look_at(camera, target)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    for obj in bpy.data.objects:
        if obj.get("aevrynd_role") == "cornea":
            obj.hide_render = True
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
bpy.context.scene.frame_set(1)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BUILD.parent.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]
rig = bpy.data.objects["AevryndFemaleRig"]
changed, maximum, components = sculpt_secondary_forms(body)
color_name, minimum_color = add_skin_tone_attribute(body)
body["aevrynd_face_revision"] = 12
upper_lip = bpy.data.objects["Lip_Upper"]
upper_lip_clearance = upper_lip.modifiers.get("Aevrynd Face Layer Clearance")
if upper_lip_clearance is None:
    raise RuntimeError("upper-lip clearance modifier is missing")
upper_lip_clearance.strength = 0.00110
upper_lip["aevrynd_dynamic_clearance_m"] = 0.00110
surface_data = surface(body)
fold_material = layer_material("Aevrynd_EyelidFold", (0.28, 0.11, 0.085, 1.0), 0.76)
folds = [
    eyelid_fold("Eye_L_UpperFold", 0.034527, surface_data, fold_material, rig),
    eyelid_fold("Eye_R_UpperFold", -0.034443, surface_data, fold_material, rig),
]
catchlight_material = layer_material("Aevrynd_EyeCatchlight", (1.0, 0.93, 0.82, 1.0), 0.18, 1.8)
catchlights = [
    catchlight("Eye_L_Catchlight", (0.0336, -0.11415, 1.6092), catchlight_material, rig),
    catchlight("Eye_R_Catchlight", (-0.0354, -0.11415, 1.6092), catchlight_material, rig),
]

bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-face-front", (0.0, -0.70, 1.570), (0.0, -0.005, 1.555))
render(camera, "female-face-three-quarter", (0.27, -0.62, 1.575), (0.0, 0.0, 1.548))
render(camera, "female-face-side", (0.65, -0.05, 1.570), (0.0, 0.0, 1.545))

body_multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_multires = (body_multires.levels, body_multires.sculpt_levels, body_multires.render_levels)
body_multires.levels = body_multires.sculpt_levels = body_multires.render_levels = 0
bpy.ops.object.select_all(action="DESELECT")
runtime = [obj for obj in bpy.data.objects if obj.type in {"MESH", "ARMATURE"}]
for obj in runtime:
    obj.hide_render = False
    obj.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(
    filepath=str(BUILD), export_format="GLB", use_selection=True,
    export_apply=True, export_yup=True, export_extras=True,
    export_animations=True, export_frame_range=True,
    export_attributes=True,
    export_vertex_color="ACTIVE",
)
body_multires.levels, body_multires.sculpt_levels, body_multires.render_levels = old_multires

print("AEVRYND_FACE_V12_REPORT=" + json.dumps({
    "state": "AUTHORING",
    "secondary_form_vertices": changed,
    "maximum_secondary_form_delta_m": maximum,
    "component_maxima_m": components,
    "skin_color_attribute": color_name,
    "minimum_skin_color_multiplier": minimum_color,
    "eyelid_fold_layers": [obj.name for obj in folds],
    "catchlight_layers": [obj.name for obj in catchlights],
    "runtime_glb": str(BUILD),
}))
