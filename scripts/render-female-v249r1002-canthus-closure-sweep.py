"""Sweep continuous-body medial/lateral canthus closure on r1001."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-mixed-space-eyelid-relief-r1001.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-canthus-closure-r1002-study.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-canthus-closure-r1002.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1002-canthus-closure"
BODY = "AevryndFemaleCC0Baseline_v259"
KEY = "Aevrynd_CanthusClosure_R1002"
STRENGTHS = (("a-baseline", 0.0), ("b-half", 0.5), ("c-full", 1.0), ("d-strong", 1.5))
VIEWS = (
    ("front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.485)),
    ("three-quarter-left", (0.155, -0.445, 1.485), (0.0, -0.060, 1.480)),
    ("three-quarter-right", (-0.155, -0.445, 1.485), (0.0, -0.060, 1.480)),
)


def gaussian(value, sigma):
    return math.exp(-0.5 * (value / sigma) ** 2)


def mixed_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    coordinates = [item.co.copy() for item in blocks[0].data]
    active = []
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        active.append({"name": block.name, "value": float(block.value)})
        for index, coordinate in enumerate(coordinates):
            coordinate += block.value * (
                block.data[index].co - block.relative_key.data[index].co
            )
    return coordinates, active


def world_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def make_key(body):
    if body.data.shape_keys is None:
        body.shape_key_add(name="Basis", from_mix=False)
    old = body.data.shape_keys.key_blocks.get(KEY)
    if old:
        body.shape_key_remove(old)
    mixed, active = mixed_coordinates(body)
    key = body.shape_key_add(name=KEY, from_mix=False)
    local_vector = body.matrix_world.inverted().to_3x3()
    moved = 0
    maximum = 0.0
    side_counts = {"L": 0, "R": 0}
    for index, coordinate in enumerate(mixed):
        world = body.matrix_world @ coordinate
        side = "L" if world.x >= 0.0 else "R"
        center_x = 0.02815 if side == "L" else -0.02815
        dx = world.x - center_x
        if not (0.007 < abs(dx) < 0.0175 and 1.440 < world.z < 1.4605):
            continue
        if not (-0.128 < world.y < -0.070):
            continue
        corner = gaussian(abs(dx) - 0.0118, 0.00235)
        vertical = gaussian(world.z - 1.4495, 0.0035)
        recession = min(1.0, max(0.0, (world.y + 0.128) / 0.034))
        weight = corner * vertical * recession
        if weight < 0.01:
            continue
        # Pull the recessed corner wall toward the face and narrow the opening
        # slightly. The move remains part of the original manifold body.
        dy = -0.00245 * weight
        dx_world = -math.copysign(0.00055 * weight, dx)
        dz = (1.4495 - world.z) * 0.055 * weight
        delta_world = Vector((dx_world, dy, dz))
        key.data[index].co += local_vector @ delta_world
        moved += 1
        side_counts[side] += 1
        maximum = max(maximum, delta_world.length)
    key.value = 0.0
    key.slider_min = 0.0
    key.slider_max = 1.5
    return key, moved, side_counts, maximum, active


def collision(body):
    body_tree = world_tree(body)
    names = tuple(
        f"Eye_{side}_{layer}"
        for side in ("L", "R")
        for layer in ("Sclera", "Cornea", "Iris", "UpperLashes", "LowerLashes")
    )
    counts = {name: len(body_tree.overlap(world_tree(bpy.data.objects[name]))) for name in names}
    return counts, sum(counts.values())


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY]
key, moved, side_counts, maximum, active = make_key(body)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
scene.render.resolution_x = scene.render.resolution_y = 800
camera = scene.camera
camera.data.lens = 105

# Isolate face, brows, eyes and lashes during the topology sweep.
hidden = []
for obj in scene.objects:
    if obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type in {"CURVES", "CURVE"}:
        if not obj.hide_render:
            obj.hide_render = True
            hidden.append(obj.name)

results = []
for label, strength in STRENGTHS:
    key.value = strength
    bpy.context.view_layer.update()
    counts, total = collision(body)
    rendered = []
    for view_name, location, target in VIEWS:
        camera.location = location
        look_at(camera, target)
        path = RENDER_DIR / f"{label}-{view_name}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        rendered.append(str(path))
    results.append(
        {
            "label": label,
            "strength": strength,
            "bodyTriangleOverlaps": counts,
            "totalBodyTriangleOverlaps": total,
            "rendered": rendered,
            "status": "PASS" if total == 0 else "FAIL",
        }
    )

for name in hidden:
    bpy.data.objects[name].hide_render = False
key.value = 0.0
scene["aevrynd_mainline_revision"] = "v249r1002-canthus-closure-study"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "STUDY_ONLY_VISUAL_REVIEW_REQUIRED"
scene["aevrynd_website_promotion"] = "forbidden"
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "shapeKey": KEY,
    "activeSourceShapeKeys": active,
    "movedVertexCount": moved,
    "movedVertexCountBySide": side_counts,
    "maximumBasisDisplacementM": maximum,
    "results": results,
    "selectedStrength": None,
    "status": "VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R1002_CANTHUS_CLOSURE=" + json.dumps(report, sort_keys=True))
