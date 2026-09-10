import json
import math
import os
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get(
    "AEVRYND_CHARACTER_SOURCE",
    ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-root-density-r90.blend",
))
OUTPUT = Path(os.environ.get(
    "AEVRYND_CHARACTER_COLLISION_REPORT",
    ROOT / "assets-source/aevrynd-character/female-v249-mainline-cc0-root-density-r90.collision-audit.json",
))
HAIR = tuple(os.environ.get(
    "AEVRYND_HAIR_OBJECTS",
    "AevryndFemaleCC0LongHairFitMain_v249r86;"
    "AevryndFemaleCC0LongHairFitFlyaway_v249r86;"
    "AevryndFemaleCC0LongHairRootDensity_v249r90",
).split(";"))
SOLIDS = (
    "AevryndFemaleBodyBaseV118",
    "Clothing_Bandeau_v160",
    "Clothing_BandeauBinding_v162",
    "Clothing_BodyFitShorts_v135",
)
NEAR = {
    "AevryndFemaleBodyBaseV118": 0.025,
    "Clothing_Bandeau_v160": 0.010,
    "Clothing_BandeauBinding_v162": 0.010,
    "Clothing_BodyFitShorts_v135": 0.010,
}
LIMIT = -0.0005


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def world_points(obj):
    if obj.type == "CURVES":
        return [obj.matrix_world @ point.position for point in obj.data.points]
    if obj.type == "MESH":
        return [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    raise TypeError(f"Unsupported collision layer type: {obj.type}")


def sample(points, tree, near):
    count = 0
    minimum = math.inf
    examples = []
    for index, point in enumerate(points):
        hit = tree.find_nearest(point)
        if hit is None or hit[1] is None or hit[3] > near:
            continue
        signed = (point - hit[0]).dot(hit[1].normalized())
        minimum = min(minimum, signed)
        if signed < LIMIT:
            count += 1
            if len(examples) < 20:
                examples.append(index)
    return {
        "sample_count": len(points),
        "minimum_signed_m": minimum if math.isfinite(minimum) else None,
        "penetrating_count": count,
        "penetrating_indices_sample": examples,
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
frames = {}
violations = []
for frame in (1, 20):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    trees = {name: evaluated_tree(bpy.data.objects[name], depsgraph) for name in SOLIDS}
    layers = {}
    for name in HAIR:
        points = world_points(bpy.data.objects[name])
        layers[name] = {}
        for solid in SOLIDS:
            result = sample(points, trees[solid], NEAR[solid])
            layers[name][solid] = result
            if result["penetrating_count"]:
                violations.append({"frame": frame, "hair": name, "solid": solid, "count": result["penetrating_count"]})
    frames[str(frame)] = layers

report = {
    "source": str(SOURCE),
    "frames": frames,
    "penetration_limit_m": LIMIT,
    "violations": violations,
    "status": "PASS" if not violations else "FAIL",
}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249_CC0_ROOT_DENSITY_R90_AUDIT=" + json.dumps({
    "output": str(OUTPUT), "violations": violations, "status": report["status"],
}, sort_keys=True))
if violations:
    raise SystemExit(2)
