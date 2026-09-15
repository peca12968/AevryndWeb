"""Sweep a lateral-only canthus reconstruction on the active r1001 face.

The earlier r1002 study moved medial and lateral corners together.  This study
keeps the medial anatomy untouched, hides lower lashes for shape judgement, and
records lower-lash contact separately because those fibers must be regenerated
after a new lid margin is selected.
"""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-mixed-space-eyelid-relief-r1001.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-lateral-canthus-r1008-study.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-lateral-canthus-r1008.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1008-lateral-canthus"
BODY = "AevryndFemaleCC0Baseline_v259"
KEY = "Aevrynd_LateralCanthus_R1008"
STRENGTHS = (
    ("a-baseline", 0.0),
    ("b-conservative", 0.55),
    ("c-authored", 1.0),
    ("d-strong", 1.35),
)
VIEWS = (
    ("front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.484)),
    ("three-quarter-left", (0.205, -0.425, 1.490), (0.0, -0.057, 1.482)),
    ("three-quarter-right", (-0.205, -0.425, 1.490), (0.0, -0.057, 1.482)),
    ("profile-left", (0.43, -0.115, 1.490), (0.020, -0.055, 1.482)),
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
        temple_sign = 1.0 if side == "L" else -1.0
        center_x = 0.02815 * temple_sign
        dx = world.x - center_x
        lateral_dx = dx * temple_sign
        if not (0.0068 < lateral_dx < 0.0182):
            continue
        if not (1.4395 < world.z < 1.4605 and -0.130 < world.y < -0.069):
            continue

        lateral = gaussian(lateral_dx - 0.0124, 0.00255)
        vertical = gaussian(world.z - 1.4497, 0.00365)
        # Prefer the recessed socket wall; avoid flattening the visible cheek.
        depth = min(1.0, max(0.0, (world.y + 0.130) / 0.037))
        weight = lateral * vertical * depth
        if weight < 0.008:
            continue

        # Form a short, rounded lateral commissure: bring the socket wall
        # forward, taper it toward the globe, and converge on the lid midline.
        dy = -0.00355 * weight
        dx_world = -temple_sign * 0.00092 * weight
        dz = (1.4497 - world.z) * 0.095 * weight
        # A shallow upper return prevents the corner from reading as a flat
        # horizontal cut while preserving the lower-lid support plane.
        dz += 0.00020 * gaussian(world.z - 1.4526, 0.0017) * lateral * depth
        delta_world = Vector((dx_world, dy, dz))
        key.data[index].co += local_vector @ delta_world
        moved += 1
        side_counts[side] += 1
        maximum = max(maximum, delta_world.length)

    key.value = 0.0
    key.slider_min = 0.0
    key.slider_max = 1.35
    return key, moved, side_counts, maximum, active


def collision(body):
    body_tree = world_tree(body)
    names = tuple(
        f"Eye_{side}_{layer}"
        for side in ("L", "R")
        for layer in ("Sclera", "Cornea", "Iris", "UpperLashes", "LowerLashes")
    )
    counts = {name: len(body_tree.overlap(world_tree(bpy.data.objects[name]))) for name in names}
    structural = sum(
        count for name, count in counts.items() if not name.endswith("LowerLashes")
    )
    lower_lash = sum(
        count for name, count in counts.items() if name.endswith("LowerLashes")
    )
    return counts, structural, lower_lash


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY]
key, moved, side_counts, maximum, active = make_key(body)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
scene.render.resolution_x = scene.render.resolution_y = 900
camera = scene.camera
camera.data.lens = 105

# Hair and lower lashes are omitted from this diagnostic so the lateral skin
# silhouette can be judged directly. Lower-lash intersections remain audited.
hidden = []
for obj in scene.objects:
    is_hair = obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type in {"CURVES", "CURVE"}
    is_lower_lash = obj.name.endswith("LowerLashes")
    if (is_hair or is_lower_lash) and not obj.hide_render:
        obj.hide_render = True
        hidden.append(obj.name)

results = []
for label, strength in STRENGTHS:
    key.value = strength
    bpy.context.view_layer.update()
    counts, structural, lower_lash = collision(body)
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
            "structuralOverlapCountExcludingLowerLashes": structural,
            "lowerLashOverlapCountRequiresRefit": lower_lash,
            "rendered": rendered,
            "status": "STRUCTURAL_PASS" if structural == 0 else "STRUCTURAL_FAIL",
        }
    )

for name in hidden:
    bpy.data.objects[name].hide_render = False
key.value = 0.0
scene["aevrynd_mainline_revision"] = "v249r1008-lateral-canthus-study"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "STUDY_ONLY_LOWER_LASH_REFIT_REQUIRED"
scene["aevrynd_website_promotion"] = "forbidden"
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "shapeKey": KEY,
    "scope": "lateral canthus only; medial canthus and caruncle unchanged",
    "activeSourceShapeKeys": active,
    "movedVertexCount": moved,
    "movedVertexCountBySide": side_counts,
    "maximumFullStrengthDisplacementM": maximum,
    "renderIsolation": {"hair": "hidden", "lowerLashes": "hidden but collision-audited"},
    "results": results,
    "selectedStrength": None,
    "status": "VISUAL_REVIEW_REQUIRED_BEFORE_LASH_REFIT",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R1008_LATERAL_CANTHUS=" + json.dumps(report, sort_keys=True))
