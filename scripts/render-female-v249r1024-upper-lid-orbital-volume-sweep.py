"""Sweep upper-lid levator volume and orbital-fat transition on r1023."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-canthus-closure-r1023-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-upper-lid-orbital-volume-r1024-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1024-upper-lid-orbital-volume-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1024-upper-lid-orbital-volume"
BODY = "AevryndFemaleCC0Baseline_v259"
KEY = "Aevrynd_UpperLidOrbitalVolume_R1024"
FRAMES = (1, 20, 33, 61)
STRENGTHS = (("a-baseline", 0.0), ("b-restrained", 0.35), ("c-balanced", 0.65), ("d-authored", 1.0))


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
        upper_lid = gaussian(world.z - (upper_z + 0.0007), 0.0022) * lateral
        orbital_fat = gaussian(world.z - (upper_z + 0.0053), 0.0028) * lateral
        levator_crease = gaussian(world.z - (upper_z + 0.0034), 0.00105) * lateral
        # Add a broad continuous lid/fat volume while preserving a restrained
        # levator crease. Negative world Y moves toward the review camera.
        dy = -0.00042 * upper_lid - 0.00020 * orbital_fat + 0.00015 * levator_crease
        dz = 0.00008 * upper_lid * max(0.0, 1.0 - abs(dx) / 0.011)
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
    for side in ("L", "R"):
        patch_name = f"Eye_{side}_MedialCaruncle_R1023"
        if patch_name not in bpy.data.objects:
            continue
        patch_tree = world_tree(bpy.data.objects[patch_name])
        counts[f"{patch_name}:Body"] = len(patch_tree.overlap(body_tree))
        for layer in ("Sclera", "Cornea", "UpperLashes", "LowerLashes"):
            counts[f"{patch_name}:{layer}"] = len(patch_tree.overlap(world_tree(bpy.data.objects[f"Eye_{side}_{layer}"])))
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
camera.data.lens = 105

hidden = []
for obj in scene.objects:
    is_hair = obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES"
    is_brow_or_lash = "Brow" in obj.name or obj.name.endswith(("UpperLashes", "LowerLashes"))
    if is_hair and not is_brow_or_lash and not obj.hide_render:
        obj.hide_render = True
        hidden.append(obj.name)

results = []
for label, strength in STRENGTHS:
    key.value = strength
    frame_results = {}
    failures = []
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        counts, total = collision(body)
        frame_results[str(frame)] = counts
        if total:
            failures.append({"frame": frame, "totalBodyTriangleOverlaps": total, "counts": counts})
    scene.frame_set(1)
    bpy.context.view_layer.update()
    rendered = []
    for view, location, target in (
        ("front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.485)),
        ("three-quarter-left", (0.205, -0.425, 1.490), (0.0, -0.057, 1.482)),
        ("three-quarter-right", (-0.205, -0.425, 1.490), (0.0, -0.057, 1.482)),
    ):
        camera.location = location
        look_at(camera, target)
        path = RENDER_DIR / f"{label}-{view}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        rendered.append(str(path))
    results.append(
        {
            "label": label,
            "strength": strength,
            "frameBodyTriangleOverlaps": frame_results,
            "collisionFailures": failures,
            "rendered": rendered,
            "status": "PASS" if not failures else "FAIL",
        }
    )

key.value = 0.65
for name in hidden:
    bpy.data.objects[name].hide_render = False
scene["aevrynd_mainline_revision"] = "v249r1024-balanced-upper-lid-orbital-volume"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "LOCAL_TECHNICAL_PASS_VISUAL_HERO_FAIL"
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
    "selectedStrength": 0.65,
    "status": "R1024C_LOCAL_TECHNICAL_PASS_VISUAL_HERO_FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R1024_UPPER_LID_ORBITAL_VOLUME=" + json.dumps(report, sort_keys=True))

