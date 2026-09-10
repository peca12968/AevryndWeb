import json
import math
import os
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get(
    "AEVRYND_MAINLINE_GROOM_MODEL",
    ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r1.blend",
))
OUTPUT = Path(os.environ.get(
    "AEVRYND_MAINLINE_GROOM_REPORT",
    ROOT / "assets-source/aevrynd-character/female-v249-mainline-hair-r1.collision-audit.json",
))
BODY = "AevryndFemaleBodyBaseV118"
HAIR = ("AevryndFemaleGuideBob_v378", "AevryndFemaleScalpCoverage_v378")
SOLIDS = (
    BODY,
    "Clothing_Bandeau_v160",
    "Clothing_BandeauBinding_v162",
    "Clothing_BodyFitShorts_v135",
)
PENETRATION_LIMIT = -0.0005
NEAR_SURFACE_LIMIT = 0.025


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


def sample(obj, depsgraph, tree):
    evaluated = obj.evaluated_get(depsgraph)
    if evaluated.type == "CURVES":
        points = [point.position for point in evaluated.data.points]
    elif evaluated.type == "MESH":
        points = [vertex.co for vertex in evaluated.data.vertices]
    else:
        raise TypeError(evaluated.type)
    penetrating = []
    minimum = math.inf
    for index, local in enumerate(points):
        world = evaluated.matrix_world @ local
        nearest = tree.find_nearest(world)
        if nearest is None or nearest[1] is None:
            continue
        location, normal, distance = nearest[0], nearest[1].normalized(), nearest[3]
        # A nearest-face normal has no inside/outside meaning for remote open
        # garment shells.  Only classify signed penetration in the local
        # contact neighbourhood; distant points are clear by definition.
        if distance > NEAR_SURFACE_LIMIT:
            continue
        signed = (world - location).dot(normal)
        minimum = min(minimum, signed)
        if signed < PENETRATION_LIMIT:
            penetrating.append(index)
    return {
        "sample_count": len(points),
        "penetrating_indices": penetrating,
        "minimum_signed_m": minimum if math.isfinite(minimum) else None,
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
hair_names = tuple(
    obj.name for obj in bpy.data.objects
    if bool(obj.get("aevrynd_mainline_hair_collision"))
)
if not hair_names:
    hair_names = HAIR
frames = {}
for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    trees = {name: evaluated_tree(bpy.data.objects[name], depsgraph) for name in SOLIDS}
    frames[str(frame)] = {
        hair_name: {
            solid_name: sample(bpy.data.objects[hair_name], depsgraph, tree)
            for solid_name, tree in trees.items()
        }
        for hair_name in hair_names
    }

violations = []
for frame, hair_values in frames.items():
    for hair_name, solid_values in hair_values.items():
        for solid_name, result in solid_values.items():
            # Keep a bounded sample so a failed candidate can remove or repair
            # the exact offending strand instead of deforming the whole groom.
            indices = result.pop("penetrating_indices", [])
            count = len(indices)
            result["penetrating_count"] = count
            result["penetrating_indices_sample"] = indices[:20]
            if count:
                violations.append({
                    "frame": int(frame),
                    "hair": hair_name,
                    "solid": solid_name,
                    "penetrating_count": count,
                })

report = {
    "source": str(SOURCE),
    "mainline_base": "v249",
    "penetration_limit_m": PENETRATION_LIMIT,
    "near_surface_limit_m": NEAR_SURFACE_LIMIT,
    "frames": frames,
    "violations": violations,
    "status": "PASS" if not violations else "FAIL",
}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249_MAINLINE_HAIR_R1_COLLISION=" + json.dumps(report, sort_keys=True))
if violations:
    raise SystemExit(2)
