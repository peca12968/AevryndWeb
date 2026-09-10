import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-long-hair-study-r85.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-natural-long-hair-r94.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-cc0-natural-long-hair-r94"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
FLY = "AevryndFemaleCC0LongHairStudyFlyaway_v249r85"
HAIR = (MAIN, FLY)
BODY = "AevryndFemaleBodyBaseV118"
RIG = "AevryndFemaleRig"
HIDDEN = ("AevryndFemaleScalpCoverage_v378", "AevryndFemaleScalpPart_v249r25")
TARGET = 0.0015
NEAR = 0.035


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def project_body_clearance(obj, tree):
    inverse = obj.matrix_world.inverted()
    corrected = 0
    maximum = 0.0
    for point in obj.data.points:
        world = obj.matrix_world @ point.position
        hit = tree.find_nearest(world)
        if hit is None or hit[1] is None or hit[3] > NEAR:
            continue
        normal = hit[1].normalized()
        signed = (world - hit[0]).dot(normal)
        if signed >= TARGET:
            continue
        delta = normal * (TARGET - signed)
        point.position = inverse @ (world + delta)
        corrected += 1
        maximum = max(maximum, delta.length)
    obj.data.update_tag()
    return corrected, maximum


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
for name in HIDDEN:
    obj = bpy.data.objects.get(name)
    if obj:
        obj.hide_render = True
        obj.hide_viewport = True
rig = bpy.data.objects[RIG]
scene.frame_set(1)
for name in HAIR:
    obj = bpy.data.objects[name]
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world

passes = []
for pass_index in range(5):
    record = {"pass": pass_index + 1, "frames": {}}
    for frame in (1, 20):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        tree = evaluated_tree(bpy.data.objects[BODY], bpy.context.evaluated_depsgraph_get())
        values = {}
        for name in HAIR:
            corrected, maximum = project_body_clearance(bpy.data.objects[name], tree)
            values[name] = {"corrected": corrected, "maximumCorrectionM": maximum}
        record["frames"][str(frame)] = values
    passes.append(record)

for name in HAIR:
    obj = bpy.data.objects[name]
    obj["aevrynd_revision"] = "v249-mainline-cc0-natural-long-hair-r94"
    obj["aevrynd_layer"] = "hair.cc0-baked.main" if name == MAIN else "hair.cc0-baked.flyaway"
    obj["aevrynd_source"] = "Blender official Hair Nodes female styles, CC0; baked offline, Aevrynd fitted"
    obj["aevrynd_runtime_dependency"] = "none"
    obj["aevrynd_collision_frames"] = "1,20"
    obj["aevrynd_collision_clearance_m"] = TARGET
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "cc0-natural-long-hair-r94"
scene["aevrynd_release_state"] = "R94_STATIC_COLLISION_AND_RUNTIME_REVIEW_REQUIRED"
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

report = {"source": str(SOURCE), "output": str(OUTPUT), "hidden": HIDDEN,
          "targetClearanceM": TARGET, "passes": passes,
          "status": "STATIC_COLLISION_AND_RUNTIME_REVIEW_REQUIRED"}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_CC0_NATURAL_LONG_HAIR_R94=" + json.dumps({
    "output": str(OUTPUT), "lastPass": passes[-1], "status": report["status"]
}, sort_keys=True))
