import bpy
import json
from pathlib import Path
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249.blend"

def surface(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ v.co for v in mesh.vertices]
    faces = [tuple(p.vertices) for p in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(points, faces, all_triangles=False)

def points(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    result = [evaluated.matrix_world @ v.co for v in mesh.vertices]
    evaluated.to_mesh_clear()
    return result

def overlap_count(first, second, depsgraph):
    return len(surface(first, depsgraph).overlap(surface(second, depsgraph)))

bpy.ops.wm.open_mainfile(filepath=str(MODEL))
body = bpy.data.objects["AevryndFemaleBodyBaseV118"]
garments = [
    bpy.data.objects["Clothing_Bandeau_v160"],
    bpy.data.objects["Clothing_BandeauBinding_v162"],
    bpy.data.objects["Clothing_BodyFitShorts_v135"],
]
report = {"frames": {}, "pass": True}
for frame in (1, 20):
    bpy.context.scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    tree = surface(body, depsgraph)
    report["frames"][str(frame)] = {}
    for garment in garments:
        values = []
        for point in points(garment, depsgraph):
            location, normal, _, _ = tree.find_nearest(point)
            if location is not None:
                values.append((point - location).dot(normal.normalized()))
        item = {
            "samples": len(values),
            "minimum_signed_distance_mm": min(values) * 1000.0,
            "penetrating_samples": sum(v <= 0.0 for v in values),
            "samples_below_0_5mm": sum(v < 0.0005 for v in values),
            "triangle_overlaps": overlap_count(body, garment, depsgraph),
        }
        report["frames"][str(frame)][garment.name] = item
        report["pass"] &= item["triangle_overlaps"] == 0
print("AEVRYND_V249_CLOTHING_AUDIT=" + json.dumps(report, sort_keys=True))
if not report["pass"]:
    raise SystemExit(2)






