"""Measure every surface layer behind the retained r1044 mouth slit."""

import json
from collections import Counter, defaultdict
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-local-inner-lip-r1044-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1046-mouth-depth-stack.inspect.json"
BODY = "AevryndFemaleCC0Baseline_v259"
CENTER_Z = 1.3862


def mixed_coordinates(obj):
    blocks = obj.data.shape_keys.key_blocks
    result = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-9:
            continue
        relative = block.relative_key
        for index, coordinate in enumerate(result):
            coordinate += block.value * (block.data[index].co - relative.data[index].co)
    return result


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
points = mixed_coordinates(body)
polygons = [tuple(polygon.vertices) for polygon in body.data.polygons]
tree = BVHTree.FromPolygons(points, polygons, all_triangles=False)
materials = [material.name if material else "<none>" for material in body.data.materials]
rays = []
unique_faces = set()
face_y = defaultdict(list)
material_hits = Counter()

for x_step in range(-36, 37, 2):
    x = x_step * 0.0005
    for z_step in range(-3, 4):
        z = CENTER_Z + z_step * 0.0002
        origin = Vector((x, -0.40, z))
        hits = []
        for depth_order in range(32):
            location, normal, polygon_index, distance = tree.ray_cast(origin, Vector((0.0, 1.0, 0.0)), 0.60)
            if polygon_index is None:
                break
            polygon = body.data.polygons[polygon_index]
            material = materials[polygon.material_index] if polygon.material_index < len(materials) else f"slot-{polygon.material_index}"
            center = sum((points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
            hit = {
                "order": depth_order,
                "face": polygon_index,
                "material": material,
                "hitY": round(location.y, 7),
                "center": [round(center.x, 7), round(center.y, 7), round(center.z, 7)],
                "normalY": round(normal.y, 6),
            }
            hits.append(hit)
            unique_faces.add(polygon_index)
            face_y[polygon_index].append(location.y)
            material_hits[material] += 1
            origin = location + Vector((0.0, 0.00005, 0.0))
        rays.append({"x": x, "z": z, "hits": hits})

skin_name = materials[0]
internal_skin_faces = []
for face_index in sorted(unique_faces):
    polygon = body.data.polygons[face_index]
    center = sum((points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
    if polygon.material_index == 0 and -0.125 < center.y < -0.025 and abs(center.x) < 0.026 and abs(center.z - CENTER_Z) < 0.006:
        internal_skin_faces.append({
            "face": face_index,
            "center": [round(center.x, 7), round(center.y, 7), round(center.z, 7)],
            "hitYRange": [round(min(face_y[face_index]), 7), round(max(face_y[face_index]), 7)],
        })

hit_counts = Counter(len(ray["hits"]) for ray in rays)
report = {
    "revision": "v249r1046-mouth-depth-stack",
    "source": str(SOURCE),
    "rayCount": len(rays),
    "hitCountDistribution": dict(sorted(hit_counts.items())),
    "materialHitCounts": dict(material_hits),
    "skinMaterial": skin_name,
    "uniqueHitFaces": len(unique_faces),
    "internalSkinFacesInRebuildCorridor": internal_skin_faces,
    "internalSkinFaceCount": len(internal_skin_faces),
    "rays": rays,
    "status": "MEASURED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1046_DEPTH_STACK=" + json.dumps({
    "rays": len(rays),
    "hitCountDistribution": report["hitCountDistribution"],
    "materials": report["materialHitCounts"],
    "uniqueFaces": len(unique_faces),
    "internalSkinFaces": len(internal_skin_faces),
}, sort_keys=True))
