import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v6.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v7.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v7.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "eyelids-v7"


def smoothstep(low, high, value):
    if high == low:
        return float(value >= high)
    t = max(0.0, min(1.0, (value - low) / (high - low)))
    return t * t * (3.0 - 2.0 * t)


def refine_eye_aperture(body):
    inverse = body.matrix_world.inverted()
    center_z = 1.6078
    changed = 0
    maximum_delta = 0.0
    per_eye = {}
    for side, center_x in (("L", 0.034527), ("R", -0.034443)):
        side_count = 0
        for vertex in body.data.vertices:
            source = body.matrix_world @ vertex.co
            dx = source.x - center_x
            dz = source.z - center_z
            if abs(dx) >= 0.021 or abs(dz) >= 0.014 or source.y > -0.105:
                continue
            horizontal = 1.0 - smoothstep(0.012, 0.021, abs(dx))
            front = smoothstep(-0.105, -0.128, source.y)
            lid_band = smoothstep(0.0015, 0.0040, abs(dz)) * (1.0 - smoothstep(0.009, 0.014, abs(dz)))
            factor = 0.18 * horizontal * front * lid_band
            target = source.copy()
            target.z = center_z + dz * (1.0 - factor)
            delta = (target - source).length
            if delta <= 1e-8:
                continue
            vertex.co = inverse @ target
            changed += 1
            side_count += 1
            maximum_delta = max(maximum_delta, delta)
        per_eye[side] = side_count
    body.data.update()
    body["aevrynd_eyelid_revision"] = 7
    body["aevrynd_eyelid_changed_vertices"] = changed
    body["aevrynd_eyelid_max_delta_m"] = maximum_delta
    return changed, maximum_delta, per_eye


def follow_lids():
    shifts = {
        "Eye_L_UpperLashes": -0.00085,
        "Eye_R_UpperLashes": -0.00085,
        "Eye_L_LowerLashes": 0.00065,
        "Eye_R_LowerLashes": 0.00065,
        "Eye_L_TearMeniscus": 0.00065,
        "Eye_R_TearMeniscus": 0.00065,
    }
    for name, shift in shifts.items():
        obj = bpy.data.objects[name]
        obj.location.z += shift
        obj["aevrynd_eyelid_follow_revision"] = 7
    return shifts


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target):
    camera.data.lens = 78
    camera.location = location
    look_at(camera, target)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    for obj in bpy.data.objects:
        if obj.get("aevrynd_role") == "cornea":
            obj.hide_render = True
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BUILD.parent.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]
changed, maximum_delta, per_eye = refine_eye_aperture(body)
followed = follow_lids()
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_multires = (multires.levels, multires.sculpt_levels, multires.render_levels)
multires.levels = multires.sculpt_levels = multires.render_levels = 0
bpy.ops.object.select_all(action="DESELECT")
runtime = [obj for obj in bpy.data.objects if obj.type == "MESH"]
for obj in runtime:
    obj.hide_render = False
    obj.select_set(True)
bpy.context.view_layer.objects.active = body
bpy.ops.export_scene.gltf(
    filepath=str(BUILD), export_format="GLB", use_selection=True,
    export_apply=True, export_yup=True, export_extras=True,
)
multires.levels, multires.sculpt_levels, multires.render_levels = old_multires

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-eyelids-front", (0, -0.78, 1.56), (0, -0.01, 1.545))
render(camera, "female-eyelids-three-quarter", (0.30, -0.68, 1.57), (0, -0.005, 1.54))
render(camera, "female-eyelids-side", (0.70, -0.08, 1.57), (0, 0, 1.54))

print(
    "AEVRYND_EYELID_V7_REPORT="
    + json.dumps({
        "state": "AUTHORING",
        "changed_vertices": changed,
        "changed_vertices_per_eye": per_eye,
        "maximum_delta_m": maximum_delta,
        "followed_layers": followed,
        "runtime_objects": len(runtime),
        "runtime_glb": str(BUILD),
    })
)
