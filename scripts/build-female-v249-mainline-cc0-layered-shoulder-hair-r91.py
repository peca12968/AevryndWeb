import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-root-density-r90.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-layered-shoulder-hair-r91.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-cc0-layered-shoulder-hair-r91"
MAIN = "AevryndFemaleCC0LongHairFitMain_v249r86"
FLY = "AevryndFemaleCC0LongHairFitFlyaway_v249r86"
HAIR = (MAIN, FLY)
SOLIDS = (
    "AevryndFemaleBodyBaseV118",
    "Clothing_Bandeau_v160",
    "Clothing_BandeauBinding_v162",
    "Clothing_BodyFitShorts_v135",
)
TARGET = 0.0015
NEAR = 0.060


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def correct_frame(obj, trees):
    inverse = obj.matrix_world.inverted()
    corrected = 0
    maximum = 0.0
    for point in obj.data.points:
        world = obj.matrix_world @ point.position
        total_delta = Vector((0.0, 0.0, 0.0))
        for tree in trees:
            hit = tree.find_nearest(world + total_delta)
            if hit is None or hit[1] is None or hit[3] > NEAR:
                continue
            normal = hit[1].normalized()
            signed = (world + total_delta - hit[0]).dot(normal)
            if signed < TARGET:
                total_delta += normal * (TARGET - signed)
        if total_delta.length_squared:
            point.position = inverse @ (world + total_delta)
            corrected += 1
            maximum = max(maximum, total_delta.length)
    obj.data.update_tag()
    return corrected, maximum


def lengthen(obj, flyaway=False):
    records = []
    for curve_index, curve in enumerate(obj.data.curves):
        root = obj.data.points[curve.first_point_index].position.copy()
        front_center = root.y < -0.055 and abs(root.x) < 0.085
        jitter = math.sin(curve_index * 1.61803398875) * (0.035 if front_center else 0.075)
        factor = (1.08 if front_center else 1.39) + jitter
        if flyaway:
            factor = 1.16 + 0.08 * math.sin(curve_index * 2.173)
        before_tip = obj.data.points[curve.first_point_index + curve.points_length - 1].position.z
        for local_index in range(1, curve.points_length):
            point = obj.data.points[curve.first_point_index + local_index]
            t = local_index / max(1, curve.points_length - 1)
            blend = smoothstep((t - 0.12) / 0.88)
            relative = point.position - root
            point.position.z = root.z + relative.z * (1.0 + (factor - 1.0) * blend)
            point.position.x = root.x + relative.x * (1.0 + 0.035 * blend)
            if not front_center:
                point.position.y = root.y + relative.y * (1.0 + 0.025 * blend)
        after_tip = obj.data.points[curve.first_point_index + curve.points_length - 1].position.z
        records.append(after_tip - before_tip)
    obj.data.update_tag()
    return {
        "curves": len(records),
        "averageTipDeltaM": sum(records) / len(records),
        "minimumTipDeltaM": min(records),
        "maximumTipDeltaM": max(records),
    }


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
lengthening = {
    MAIN: lengthen(bpy.data.objects[MAIN]),
    FLY: lengthen(bpy.data.objects[FLY], True),
}
passes = []
for pass_index in range(4):
    pass_record = {"pass": pass_index + 1, "frames": {}}
    for frame in (1, 20):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        trees = [evaluated_tree(bpy.data.objects[name], depsgraph) for name in SOLIDS]
        frame_record = {}
        for name in HAIR:
            corrected, maximum = correct_frame(bpy.data.objects[name], trees)
            frame_record[name] = {"corrected": corrected, "maximumCorrectionM": maximum}
        pass_record["frames"][str(frame)] = frame_record
    passes.append(pass_record)

for name in HAIR:
    obj = bpy.data.objects[name]
    obj["aevrynd_revision"] = "v249-mainline-cc0-layered-shoulder-hair-r91"
    obj["aevrynd_layer"] = "hair.cc0-baked.main" if name == MAIN else "hair.cc0-baked.flyaway"
    obj["aevrynd_collision_frames"] = "1,20"
    obj["aevrynd_collision_clearance_m"] = TARGET
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "cc0-layered-shoulder-hair-r91"
scene["aevrynd_release_state"] = "R91_STRICT_VISUAL_AND_RUNTIME_REVIEW_REQUIRED"
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
for args in (
    ("01-front", (0.0, -2.15, 1.55), (0.0, 0.0, 1.55), 82),
    ("02-three-quarter", (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82),
    ("03-profile", (2.15, 0.0, 1.57), (0.0, 0.0, 1.55), 86),
    ("04-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82),
    ("05-top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78),
    ("06-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
):
    render(camera, *args)

report = {
    "source": str(SOURCE), "output": str(OUTPUT), "lengthening": lengthening,
    "targetClearanceM": TARGET, "correctionPasses": passes,
    "status": "STRICT_VISUAL_AND_RUNTIME_REVIEW_REQUIRED",
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_CC0_LAYERED_SHOULDER_R91=" + json.dumps(report, sort_keys=True))
