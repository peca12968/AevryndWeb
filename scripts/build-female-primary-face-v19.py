import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v18.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v19.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v19.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v19-lod1.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "primary-face-v19"


def gaussian(value, center, spread):
    return math.exp(-0.5 * ((value - center) / spread) ** 2)


def clamp01(value):
    return max(0.0, min(1.0, value))


def reshape_primary_face(body):
    inverse = body.matrix_world.inverted()
    changed = 0
    maximum = 0.0
    totals = {name: 0.0 for name in (
        "lower_face_taper", "cheekbone", "buccal", "chin", "mental_crease",
        "jaw_angle", "nose_tip", "alar_taper",
    )}
    for vertex in body.data.vertices:
        source = body.matrix_world @ vertex.co
        x_abs = abs(source.x)
        if source.y > 0.025 or not (1.450 <= source.z <= 1.635) or x_abs > 0.108:
            continue

        front = clamp01((-source.y - 0.074) / 0.064)
        contour = clamp01((0.025 - source.y) / 0.080)
        eye_guard = gaussian(x_abs, 0.035, 0.025) * gaussian(source.z, 1.608, 0.020)
        mouth_guard = gaussian(x_abs, 0.027, 0.034) * gaussian(source.z, 1.536, 0.014)
        guard = (1.0 - 0.90 * eye_guard) * (1.0 - 0.88 * mouth_guard)

        lower = gaussian(source.z, 1.500, 0.038) * clamp01((x_abs - 0.025) / 0.055) * contour
        jaw = gaussian(source.z, 1.474, 0.025) * gaussian(x_abs, 0.073, 0.026) * contour
        cheekbone = gaussian(source.z, 1.570, 0.021) * gaussian(x_abs, 0.058, 0.020) * front
        buccal = gaussian(source.z, 1.535, 0.021) * gaussian(x_abs, 0.061, 0.021) * front
        chin = gaussian(source.z, 1.480, 0.017) * gaussian(x_abs, 0.014, 0.025) * front
        mental = gaussian(source.z, 1.505, 0.0075) * gaussian(x_abs, 0.018, 0.027) * front
        nose_tip = gaussian(source.z, 1.575, 0.015) * gaussian(x_abs, 0.0, 0.014) * front
        alar = gaussian(source.z, 1.563, 0.012) * gaussian(x_abs, 0.021, 0.010) * front

        side = 1.0 if source.x >= 0.0 else -1.0
        # Primary silhouette: taper the mandible, retain a lateral zygomatic arc,
        # and give the chin a distinct pad instead of one continuous flat plane.
        x_delta = side * (
            -0.0090 * lower
            -0.0050 * jaw
            +0.00135 * cheekbone
            -0.0014 * chin
            -0.0011 * alar
        ) * guard
        y_delta = (
            -0.0042 * cheekbone
            +0.0030 * buccal
            -0.0040 * chin
            +0.0016 * mental
            +0.0018 * jaw
            -0.00115 * nose_tip
        ) * guard
        z_delta = (0.00125 * jaw - 0.00065 * chin) * guard

        # Deliberately retain small human asymmetry without moving protected seams.
        asymmetry = gaussian(source.z, 1.555, 0.050) * gaussian(x_abs, 0.055, 0.035) * front * guard
        y_delta += (-0.00035 if source.x >= 0.0 else 0.00022) * asymmetry

        target = source + Vector((x_delta, y_delta, z_delta))
        delta = (target - source).length
        if delta <= 1e-7:
            continue
        vertex.co = inverse @ target
        changed += 1
        maximum = max(maximum, delta)
        totals["lower_face_taper"] = max(totals["lower_face_taper"], abs(0.0090 * lower * guard))
        totals["cheekbone"] = max(totals["cheekbone"], abs(0.0042 * cheekbone * guard))
        totals["buccal"] = max(totals["buccal"], abs(0.0030 * buccal * guard))
        totals["chin"] = max(totals["chin"], abs(0.0040 * chin * guard))
        totals["mental_crease"] = max(totals["mental_crease"], abs(0.0016 * mental * guard))
        totals["jaw_angle"] = max(totals["jaw_angle"], abs(0.0050 * jaw * guard))
        totals["nose_tip"] = max(totals["nose_tip"], abs(0.00115 * nose_tip * guard))
        totals["alar_taper"] = max(totals["alar_taper"], abs(0.0011 * alar * guard))
    body.data.update()
    body["aevrynd_face_revision"] = 19
    body["aevrynd_primary_face_vertices"] = changed
    body["aevrynd_primary_face_max_delta_m"] = maximum
    return changed, maximum, totals


def replace_face_smoothing(body):
    old = body.modifiers.get("Aevrynd Face Planar Smoothing")
    if old:
        body.modifiers.remove(old)
    old_group = body.vertex_groups.get("AevryndFacePlanarSmooth")
    if old_group:
        body.vertex_groups.remove(old_group)

    group = body.vertex_groups.new(name="AevryndFacePrimarySmooth")
    count = 0
    maximum = 0.0
    for vertex in body.data.vertices:
        point = body.matrix_world @ vertex.co
        x_abs = abs(point.x)
        if point.y > 0.015 or not (1.458 <= point.z <= 1.600) or x_abs > 0.103:
            continue
        front = clamp01((-point.y - 0.073) / 0.065)
        contour = clamp01((0.015 - point.y) / 0.085)
        cheek = gaussian(x_abs, 0.060, 0.033) * gaussian(point.z, 1.548, 0.047) * front
        jaw = gaussian(x_abs, 0.063, 0.036) * gaussian(point.z, 1.486, 0.030) * contour
        eye_guard = gaussian(x_abs, 0.035, 0.025) * gaussian(point.z, 1.606, 0.020)
        nose_guard = gaussian(point.x, 0.0, 0.025) * gaussian(point.z, 1.567, 0.045)
        mouth_guard = gaussian(point.x, 0.0, 0.041) * gaussian(point.z, 1.536, 0.017)
        weight = 0.72 * cheek + 0.42 * jaw
        weight *= (1.0 - 0.92 * eye_guard) * (1.0 - 0.90 * nose_guard) * (1.0 - 0.94 * mouth_guard)
        weight = min(0.62, weight)
        if weight <= 0.02:
            continue
        group.add([vertex.index], weight, "REPLACE")
        count += 1
        maximum = max(maximum, weight)

    modifier = body.modifiers.new("Aevrynd Face Primary Smoothing", "LAPLACIANSMOOTH")
    modifier.vertex_group = group.name
    modifier.lambda_factor = 0.16
    modifier.iterations = 4
    modifier.use_volume_preserve = True
    armature_index = next(i for i, item in enumerate(body.modifiers) if item.type == "ARMATURE")
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_move_to_index(modifier=modifier.name, index=armature_index)
    return count, maximum


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens=86):
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.data.lens = lens
    camera.location = location
    look_at(camera, target)
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
changed, maximum_delta, components = reshape_primary_face(body)
smooth_vertices, smooth_maximum = replace_face_smoothing(body)
bpy.context.scene["aevrynd_face_revision"] = 19
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-primary-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555))
render(camera, "female-primary-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55))
render(camera, "female-primary-left", (-0.66, -0.05, 1.575), (0.0, 0.0, 1.545))
render(camera, "female-primary-right", (0.66, -0.05, 1.575), (0.0, 0.0, 1.545))
render(camera, "female-primary-close", (0.0, -0.48, 1.575), (0.0, -0.075, 1.565), 102)

multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_levels = (multires.levels, multires.sculpt_levels, multires.render_levels)
multires.levels = multires.sculpt_levels = multires.render_levels = 0
export_runtime(BUILD, rig)
export_runtime(LOD1, rig, {"HairMain", "HairFlyaways"})
multires.levels, multires.sculpt_levels, multires.render_levels = old_levels

print("AEVRYND_PRIMARY_FACE_V19_REPORT=" + json.dumps({
    "state": "AUTHORING",
    "changed_vertices": changed,
    "maximum_delta_m": maximum_delta,
    "component_maxima_m": components,
    "smoothing_vertices": smooth_vertices,
    "maximum_smoothing_weight": smooth_maximum,
    "runtime_glb": str(BUILD),
    "lod1_glb": str(LOD1),
}))
