"""Sweep eyelid relief selected in r995's active mixed-shape coordinate space."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-target-native-lashes-r995.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-mixed-space-eyelid-relief-r1000-study.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-mixed-space-eyelid-relief-r1000.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1000-mixed-space-eyelid-relief"
BODY = "AevryndFemaleCC0Baseline_v259"
KEY = "Aevrynd_MixedSpaceEyelidRelief_R1000"
STRENGTHS = (("a-baseline", 0.0), ("b-half", 0.5), ("c-full", 1.0), ("d-strong", 1.5))


def gaussian(value, sigma):
    return math.exp(-0.5 * (value / sigma) ** 2)


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


def mixed_coordinates(body):
    """Return pre-modifier coordinates after all currently active relative keys."""
    blocks = body.data.shape_keys.key_blocks
    basis = blocks[0]
    coordinates = [item.co.copy() for item in basis.data]
    active = []
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        relative = block.relative_key
        active.append({"name": block.name, "value": float(block.value)})
        for index, coordinate in enumerate(coordinates):
            coordinate += block.value * (block.data[index].co - relative.data[index].co)
    return coordinates, active


def make_key(body):
    if body.data.shape_keys is None:
        body.shape_key_add(name="Basis", from_mix=False)
    old = body.data.shape_keys.key_blocks.get(KEY)
    if old:
        body.shape_key_remove(old)
    mixed, active = mixed_coordinates(body)
    key = body.shape_key_add(name=KEY, from_mix=False)
    moved = 0
    maximum = 0.0
    local_vector = body.matrix_world.inverted().to_3x3()
    for index, coordinate in enumerate(mixed):
        world = body.matrix_world @ coordinate
        # The source mesh Basis is not the rendered face: 22 active MPFB keys
        # move the head substantially. Select against their actual mixed pose.
        if world.y >= -0.070 or not (1.433 < world.z < 1.472):
            continue
        center_x = 0.02815 if world.x >= 0.0 else -0.02815
        dx = world.x - center_x
        if abs(dx) >= 0.016:
            continue
        lateral = max(0.0, 1.0 - (abs(dx) / 0.016) ** 2)
        arc = math.sqrt(max(0.0, 1.0 - (dx / 0.0135) ** 2))
        upper_z = 1.4518 + 0.0064 * arc
        lower_z = 1.4513 - 0.0040 * arc
        upper_ridge = gaussian(world.z - upper_z, 0.00175) * lateral
        lower_ridge = gaussian(world.z - lower_z, 0.00145) * lateral
        upper_crease = gaussian(world.z - (upper_z + 0.0042), 0.00135) * lateral
        # Build a rounded palpebral ridge toward the camera; the shallow
        # crease recedes only 0.18 mm at full strength and remains outside the
        # r995 eye stack.
        dy = -0.00072 * upper_ridge - 0.00030 * lower_ridge + 0.00018 * upper_crease
        dz = 0.00016 * upper_ridge * max(0.0, 1.0 - abs(dx) / 0.011)
        delta_world = Vector((0.0, dy, dz))
        if delta_world.length < 1e-7:
            continue
        key.data[index].co += local_vector @ delta_world
        moved += 1
        maximum = max(maximum, delta_world.length)
    key.value = 0.0
    key.slider_min = 0.0
    key.slider_max = 1.5
    return key, moved, maximum, active


def collision(body):
    body_tree = world_tree(body)
    names = tuple(
        f"Eye_{side}_{layer}"
        for side in ("L", "R")
        for layer in ("Sclera", "Cornea", "Iris", "UpperLashes", "LowerLashes")
    )
    counts = {name: len(body_tree.overlap(world_tree(bpy.data.objects[name]))) for name in names}
    return counts, sum(counts.values())


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY]
key, moved, maximum, active = make_key(body)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
scene.render.resolution_x = scene.render.resolution_y = 900
camera = scene.camera
camera.location = (0.0, -0.48, 1.485)
camera.data.lens = 105
look_at(camera, (0.0, -0.060, 1.485))

results = []
for label, strength in STRENGTHS:
    key.value = strength
    bpy.context.view_layer.update()
    counts, total = collision(body)
    scene.render.filepath = str(RENDER_DIR / f"{label}.png")
    bpy.ops.render.render(write_still=True)
    results.append(
        {
            "label": label,
            "strength": strength,
            "bodyTriangleOverlaps": counts,
            "totalBodyTriangleOverlaps": total,
            "status": "PASS" if total == 0 else "FAIL",
        }
    )

key.value = 0.0
scene["aevrynd_mainline_revision"] = "v249r1000-mixed-space-eyelid-relief-study"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "STUDY_ONLY_VISUAL_REVIEW_REQUIRED"
scene["aevrynd_website_promotion"] = "forbidden"
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "shapeKey": KEY,
    "selection": "active mixed-shape surface; outer band worldY < -0.070",
    "activeSourceShapeKeys": active,
    "movedVertexCount": moved,
    "maximumBasisDisplacementM": maximum,
    "results": results,
    "selectedStrength": None,
    "status": "VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R1000_MIXED_SPACE_EYELID_RELIEF=" + json.dumps(report, sort_keys=True))
