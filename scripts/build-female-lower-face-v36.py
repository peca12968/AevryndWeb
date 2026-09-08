import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v35.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v36.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v36.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v36-lod1.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "lower-face-v36"


def gaussian(value, center, spread):
    return math.exp(-0.5 * ((value - center) / spread) ** 2)


def clamp01(value):
    return max(0.0, min(1.0, value))


def sculpt_lower_face(body):
    inverse = body.matrix_world.inverted()
    changed = 0
    maximum = 0.0
    components = {name: 0.0 for name in (
        "jaw_taper", "chin_projection", "chin_length", "malar_projection",
        "buccal_transition", "alar_taper", "nose_tip_projection", "asymmetry",
    )}
    for vertex in body.data.vertices:
        point = body.matrix_world @ vertex.co
        x_abs = abs(point.x)
        if point.y > 0.015 or x_abs > 0.105 or not (1.425 <= point.z <= 1.590):
            continue
        front = clamp01((-point.y + 0.015) / 0.090)
        side = 1.0 if point.x >= 0.0 else -1.0

        jaw_outer = clamp01((x_abs - 0.018) / 0.030)
        jaw_shell = clamp01((0.015 - point.y) / 0.025)
        jaw_ceiling = clamp01((1.540 - point.z) / 0.018)
        jaw = gaussian(point.z, 1.475, 0.036) * jaw_outer * jaw_shell * jaw_ceiling
        # Keep the lip attachment zone fixed while tapering the lower third.
        jaw *= 1.0 - gaussian(point.z, 1.532, 0.012) * gaussian(x_abs, 0.025, 0.020)
        chin = gaussian(x_abs, 0.0, 0.024) * gaussian(point.z, 1.472, 0.023) * front
        chin_bottom = gaussian(x_abs, 0.0, 0.021) * gaussian(point.z, 1.452, 0.017) * front
        malar = gaussian(x_abs, 0.049, 0.018) * gaussian(point.z, 1.565, 0.019) * front
        buccal = gaussian(x_abs, 0.056, 0.020) * gaussian(point.z, 1.522, 0.021) * front
        ala = gaussian(x_abs, 0.022, 0.010) * gaussian(point.z, 1.559, 0.011) * front
        nose_tip = gaussian(x_abs, 0.0, 0.011) * gaussian(point.z, 1.573, 0.010) * front
        asymmetry = gaussian(x_abs, 0.045, 0.030) * gaussian(point.z, 1.535, 0.050) * front

        x_delta = side * (-0.00300 * jaw + 0.00058 * malar - 0.00062 * ala)
        y_delta = (
            -0.00074 * chin
            -0.00078 * malar
            +0.00052 * buccal
            -0.00056 * nose_tip
            +(-0.00010 if point.x >= 0.0 else 0.00007) * asymmetry
        )
        z_delta = -0.00048 * chin_bottom
        target = point + Vector((x_delta, y_delta, z_delta))
        delta = (target - point).length
        if delta <= 1e-7:
            continue
        vertex.co = inverse @ target
        changed += 1
        maximum = max(maximum, delta)
        for name, value in {
            "jaw_taper": 0.00300 * jaw,
            "chin_projection": 0.00074 * chin,
            "chin_length": 0.00048 * chin_bottom,
            "malar_projection": math.hypot(0.00058 * malar, 0.00078 * malar),
            "buccal_transition": 0.00052 * buccal,
            "alar_taper": 0.00062 * ala,
            "nose_tip_projection": 0.00056 * nose_tip,
            "asymmetry": 0.00010 * asymmetry,
        }.items():
            components[name] = max(components[name], value)
    body.data.update()
    body["aevrynd_face_revision"] = 36
    body["aevrynd_lower_face_vertices"] = changed
    body["aevrynd_lower_face_max_delta_m"] = maximum
    return changed, maximum, components


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens=96):
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
            obj.hide_render = False
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
changed, maximum, components = sculpt_lower_face(body)
bpy.context.scene["aevrynd_face_revision"] = 36
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-face-front", (0.0, -0.72, 1.575), (0.0, -0.005, 1.555))
render(camera, "female-face-three-quarter", (0.28, -0.64, 1.58), (0.0, 0.0, 1.55))
render(camera, "female-face-left", (-0.66, -0.05, 1.575), (0.0, 0.0, 1.545), 88)
render(camera, "female-face-right", (0.66, -0.05, 1.575), (0.0, 0.0, 1.545), 88)

multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_levels = (multires.levels, multires.sculpt_levels, multires.render_levels)
multires.levels = multires.sculpt_levels = multires.render_levels = 0
export_runtime(BUILD, rig)
export_runtime(LOD1, rig, {"HairMain", "HairFlyaways"})
multires.levels, multires.sculpt_levels, multires.render_levels = old_levels

print("AEVRYND_LOWER_FACE_V36_REPORT=" + json.dumps({
    "state": "AUTHORING",
    "changed_vertices": changed,
    "maximum_delta_m": maximum,
    "components_m": components,
    "runtime_glb": str(BUILD),
    "lod1_glb": str(LOD1),
}))
