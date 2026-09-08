import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v17.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v18.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v18.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v18-lod1.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "identity-v18"


def gaussian(value, center, spread):
    return math.exp(-0.5 * ((value - center) / spread) ** 2)


def segment_distance(px, pz, ax, az, bx, bz):
    abx, abz = bx - ax, bz - az
    length_squared = abx * abx + abz * abz
    t = max(0.0, min(1.0, ((px - ax) * abx + (pz - az) * abz) / length_squared))
    qx, qz = ax + abx * t, az + abz * t
    return math.hypot(px - qx, pz - qz)


def sculpt_identity_forms(body):
    inverse = body.matrix_world.inverted()
    changed = 0
    maximum = 0.0
    component_maxima = {
        "zygomatic": 0.0,
        "tear_trough": 0.0,
        "buccal_hollow": 0.0,
        "nasolabial": 0.0,
        "nose": 0.0,
        "chin": 0.0,
        "jaw": 0.0,
    }
    for vertex in body.data.vertices:
        source = body.matrix_world @ vertex.co
        if source.y > -0.082 or not (1.448 <= source.z <= 1.630) or abs(source.x) > 0.100:
            continue
        front = max(0.0, min(1.0, (-source.y - 0.082) / 0.058))
        side_bias = 1.055 if source.x >= 0.0 else 0.945
        x_abs = abs(source.x)
        zygomatic = gaussian(x_abs, 0.054, 0.020) * gaussian(source.z, 1.570, 0.022) * front * side_bias
        lower_cheek = gaussian(x_abs, 0.050, 0.024) * gaussian(source.z, 1.548, 0.020) * front
        tear = gaussian(x_abs, 0.034, 0.016) * gaussian(source.z, 1.594, 0.0075) * front
        buccal = gaussian(x_abs, 0.066, 0.018) * gaussian(source.z, 1.532, 0.020) * front * (2.0 - side_bias)
        fold_distance = segment_distance(x_abs, source.z, 0.020, 1.558, 0.041, 1.520)
        nasolabial = math.exp(-0.5 * (fold_distance / 0.0040) ** 2) * front
        nasolabial *= max(0.0, min(1.0, (x_abs - 0.012) / 0.016))
        alar = gaussian(x_abs, 0.020, 0.009) * gaussian(source.z, 1.565, 0.014) * front
        nose_tip = gaussian(source.x, 0.0, 0.014) * gaussian(source.z, 1.578, 0.015) * front
        chin_pad = gaussian(x_abs, 0.018, 0.024) * gaussian(source.z, 1.482, 0.016) * front
        mental_crease = gaussian(x_abs, 0.016, 0.024) * gaussian(source.z, 1.506, 0.008) * front
        jaw_softening = gaussian(x_abs, 0.078, 0.017) * gaussian(source.z, 1.486, 0.027) * front

        y_delta = (
            -0.00120 * zygomatic
            -0.00036 * lower_cheek
            +0.00042 * tear
            +0.00080 * buccal
            +0.00038 * nasolabial
            -0.00040 * alar
            -0.00032 * nose_tip
            -0.00085 * chin_pad
            +0.00036 * mental_crease
            +0.00050 * jaw_softening
        )
        target = source.copy()
        target.y += y_delta
        cheek_side = 1.0 if source.x >= 0.0 else -1.0
        target.x += cheek_side * 0.00018 * zygomatic
        target.x += 0.00024 * nose_tip
        delta = (target - source).length
        if delta <= 1e-8:
            continue
        vertex.co = inverse @ target
        changed += 1
        maximum = max(maximum, delta)
        component_maxima["zygomatic"] = max(component_maxima["zygomatic"], 0.00120 * zygomatic)
        component_maxima["tear_trough"] = max(component_maxima["tear_trough"], 0.00042 * tear)
        component_maxima["buccal_hollow"] = max(component_maxima["buccal_hollow"], 0.00080 * buccal)
        component_maxima["nasolabial"] = max(component_maxima["nasolabial"], 0.00038 * nasolabial)
        component_maxima["nose"] = max(component_maxima["nose"], 0.00040 * alar + 0.00032 * nose_tip)
        component_maxima["chin"] = max(component_maxima["chin"], 0.00085 * chin_pad)
        component_maxima["jaw"] = max(component_maxima["jaw"], 0.00050 * jaw_softening)
    body.data.update()
    body["aevrynd_identity_revision"] = 18
    body["aevrynd_identity_vertices"] = changed
    body["aevrynd_identity_max_delta_m"] = maximum
    return changed, maximum, component_maxima


def refine_skin_tone(body):
    name = "AevryndSkinTone"
    old = body.data.color_attributes.get(name)
    if old:
        body.data.color_attributes.remove(old)
    colors = body.data.color_attributes.new(name=name, type="BYTE_COLOR", domain="POINT")
    minimum = [1.0, 1.0, 1.0]
    maximum = [0.0, 0.0, 0.0]
    for vertex, entry in zip(body.data.vertices, colors.data):
        point = body.matrix_world @ vertex.co
        front = max(0.0, min(1.0, (-point.y - 0.070) / 0.070))
        cheek = gaussian(abs(point.x), 0.057, 0.030) * gaussian(point.z, 1.562, 0.038) * front
        nose = gaussian(point.x, 0.0, 0.025) * gaussian(point.z, 1.570, 0.040) * front
        under_eye = gaussian(abs(point.x), 0.035, 0.024) * gaussian(point.z, 1.594, 0.012) * front
        ear = gaussian(abs(point.x), 0.098, 0.014) * gaussian(point.z, 1.585, 0.055)
        asymmetry = 1.04 if point.x >= 0.0 else 0.96
        redness = min(1.0, (0.52 * cheek + 0.24 * nose + 0.34 * ear) * asymmetry)
        cool = min(1.0, 0.42 * under_eye * (2.0 - asymmetry))
        color = (
            1.0 - 0.012 * cool,
            1.0 - 0.026 * redness - 0.010 * cool,
            1.0 - 0.041 * redness,
            1.0,
        )
        entry.color = color
        for index in range(3):
            minimum[index] = min(minimum[index], color[index])
            maximum[index] = max(maximum[index], color[index])
    body.data.materials[0]["aevrynd_skin_tone_revision"] = 18
    return minimum, maximum


def add_planar_smoothing(body):
    group_name = "AevryndFacePlanarSmooth"
    old_group = body.vertex_groups.get(group_name)
    if old_group:
        body.vertex_groups.remove(old_group)
    group = body.vertex_groups.new(name=group_name)
    weighted = 0
    maximum = 0.0
    for vertex in body.data.vertices:
        point = body.matrix_world @ vertex.co
        if point.y > -0.078 or not (1.470 <= point.z <= 1.608) or abs(point.x) > 0.098:
            continue
        x_abs = abs(point.x)
        front = max(0.0, min(1.0, (-point.y - 0.078) / 0.060))
        cheek = gaussian(x_abs, 0.058, 0.028) * gaussian(point.z, 1.558, 0.043) * front
        jaw = gaussian(x_abs, 0.060, 0.038) * gaussian(point.z, 1.495, 0.025) * front
        eye_exclusion = gaussian(x_abs, 0.035, 0.022) * gaussian(point.z, 1.610, 0.016)
        nose_exclusion = gaussian(point.x, 0.0, 0.025) * gaussian(point.z, 1.565, 0.045)
        mouth_exclusion = gaussian(point.x, 0.0, 0.040) * gaussian(point.z, 1.535, 0.018)
        weight = min(0.72, (0.62 * cheek + 0.34 * jaw) * (1.0 - 0.85 * eye_exclusion) * (1.0 - 0.88 * nose_exclusion) * (1.0 - 0.92 * mouth_exclusion))
        if weight <= 0.015:
            continue
        group.add([vertex.index], weight, "REPLACE")
        weighted += 1
        maximum = max(maximum, weight)
    old_modifier = body.modifiers.get("Aevrynd Face Planar Smoothing")
    if old_modifier:
        body.modifiers.remove(old_modifier)
    modifier = body.modifiers.new("Aevrynd Face Planar Smoothing", "LAPLACIANSMOOTH")
    modifier.vertex_group = group_name
    modifier.lambda_factor = 0.085
    modifier.iterations = 2
    modifier.use_volume_preserve = True
    armature_index = next((index for index, item in enumerate(body.modifiers) if item.type == "ARMATURE"), len(body.modifiers) - 1)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_move_to_index(modifier=modifier.name, index=armature_index)
    body["aevrynd_planar_smoothing_revision"] = 18
    body["aevrynd_planar_smoothing_vertices"] = weighted
    return weighted, maximum


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens=86):
    scene = bpy.context.scene
    scene.frame_set(1)
    camera.data.lens = lens
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


def export_runtime(path, rig, excluded=()):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.data.objects:
        if obj.type in {"MESH", "ARMATURE"} and obj.name not in excluded:
            obj.hide_render = False
            obj.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format="GLB", use_selection=True,
        export_apply=True, export_yup=True, export_extras=True,
        export_animations=True, export_frame_range=True,
        export_attributes=True, export_vertex_color="ACTIVE",
    )


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
bpy.context.scene.frame_set(1)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BUILD.parent.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]
rig = bpy.data.objects["AevryndFemaleRig"]
changed, maximum_delta, components = sculpt_identity_forms(body)
tone_minimum, tone_maximum = refine_skin_tone(body)
smoothing_vertices, maximum_smoothing_weight = add_planar_smoothing(body)
body["aevrynd_face_revision"] = 18
bpy.context.scene["aevrynd_face_revision"] = 18
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-identity-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555))
render(camera, "female-identity-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55))
render(camera, "female-identity-left", (-0.66, -0.05, 1.575), (0.0, 0.0, 1.545))
render(camera, "female-identity-right", (0.66, -0.05, 1.575), (0.0, 0.0, 1.545))
render(camera, "female-identity-close", (0.0, -0.48, 1.575), (0.0, -0.075, 1.565), 102)

body_multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_multires = (body_multires.levels, body_multires.sculpt_levels, body_multires.render_levels)
body_multires.levels = body_multires.sculpt_levels = body_multires.render_levels = 0
export_runtime(BUILD, rig)
export_runtime(LOD1, rig, {"HairMain", "HairFlyaways"})
body_multires.levels, body_multires.sculpt_levels, body_multires.render_levels = old_multires

print("AEVRYND_IDENTITY_V18_REPORT=" + json.dumps({
    "state": "AUTHORING",
    "changed_vertices": changed,
    "maximum_delta_m": maximum_delta,
    "component_maxima_m": components,
    "skin_tone_minimum": tone_minimum,
    "skin_tone_maximum": tone_maximum,
    "smoothing_vertices": smoothing_vertices,
    "maximum_smoothing_weight": maximum_smoothing_weight,
    "runtime_glb": str(BUILD),
    "lod1_glb": str(LOD1),
}))
