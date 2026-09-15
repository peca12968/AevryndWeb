"""Identify body faces visible through the r1044 mouth aperture."""

import json
from collections import Counter
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-local-inner-lip-r1044-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1044-aperture-ray-inspection.json"
BODY = "AevryndFemaleCC0Baseline_v259"


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
mesh = body.data
blocks = mesh.shape_keys.key_blocks
mixed = [item.co.copy() for item in blocks[0].data]
for block in blocks[1:]:
    if block.mute or abs(block.value) < 1e-8:
        continue
    for index, item in enumerate(block.data):
        mixed[index] += block.value * (item.co - block.relative_key.data[index].co)
points = [body.matrix_world @ point for point in mixed]
polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
tree = BVHTree.FromPolygons(points, polygons)

hits = []
for x_step in range(-36, 37):
    x = x_step * 0.0005
    for z_step in range(-3, 4):
        z = 1.3862 + z_step * 0.0002
        location, normal, polygon_index, distance = tree.ray_cast(Vector((x, -0.40, z)), Vector((0.0, 1.0, 0.0)), 0.50)
        if polygon_index is None:
            continue
        polygon = mesh.polygons[polygon_index]
        center = sum((points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
        hits.append({
            "sample": [x, z],
            "polygon": polygon_index,
            "material": polygon.material_index,
            "center": list(center),
            "normal": list(body.matrix_world.to_3x3() @ polygon.normal),
            "distance": distance,
        })

counts = Counter(hit["polygon"] for hit in hits)
unique = []
for polygon_index, count in counts.most_common():
    example = next(hit for hit in hits if hit["polygon"] == polygon_index)
    unique.append({**example, "samples": count})
report = {
    "revision": "v249r1044-aperture-ray-inspection",
    "source": str(SOURCE),
    "sampleCount": len(hits),
    "uniqueFirstHitBodyFaces": unique,
    "materialCounts": dict(Counter(hit["material"] for hit in hits)),
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1044_APERTURE_RAYS=" + json.dumps({"samples": len(hits), "uniqueFaces": len(unique), "materialCounts": report["materialCounts"]}, sort_keys=True))
