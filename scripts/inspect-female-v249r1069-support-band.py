"""Inspect the baked r1068 support vertices and faces as a controllable band."""
import json
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-exact-edge-support-r1068-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1069-support-band.inspect.json"
BODY = "AevryndFemaleCC0ExactEdgeSupport_R1068"
ORIGINAL_VERTEX_COUNT = 13583

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
mesh = body.data
new_vertices = set(range(ORIGINAL_VERTEX_COUNT, len(mesh.vertices)))
new_faces = [polygon for polygon in mesh.polygons if any(index in new_vertices for index in polygon.vertices)]
fully_new_faces = [polygon for polygon in new_faces if all(index in new_vertices for index in polygon.vertices)]
points = [body.matrix_world @ mesh.shape_keys.key_blocks[0].data[index].co for index in sorted(new_vertices)]
blocks = mesh.shape_keys.key_blocks
neutral = [blocks[0].data[index].co.copy() for index in sorted(new_vertices)]
for block in blocks[1:]:
    if block.name in ("Aevrynd_MouthOpenTest_R1030", "Aevrynd_SmileTest_R1030") or block.mute or abs(block.value) < 1e-8:
        continue
    for offset, index in enumerate(sorted(new_vertices)):
        neutral[offset] += block.value * (block.data[index].co - block.relative_key.data[index].co)
neutral_points = [body.matrix_world @ point for point in neutral]
report = {
    "revision": "v249r1069-support-band-inspection",
    "source": str(SOURCE),
    "body": BODY,
    "topology": {"vertices": len(mesh.vertices), "faces": len(mesh.polygons)},
    "newVertexCount": len(new_vertices),
    "facesTouchingNewVertices": len(new_faces),
    "facesOnlyNewVertices": len(fully_new_faces),
    "newVertexBounds": {
        "x": [min(point.x for point in points), max(point.x for point in points)],
        "y": [min(point.y for point in points), max(point.y for point in points)],
        "z": [min(point.z for point in points), max(point.z for point in points)],
    },
    "newVertexNeutralBounds": {
        "x": [min(point.x for point in neutral_points), max(point.x for point in neutral_points)],
        "y": [min(point.y for point in neutral_points), max(point.y for point in neutral_points)],
        "z": [min(point.z for point in neutral_points), max(point.z for point in neutral_points)],
    },
    "newFaceMaterialCounts": {
        str(index): sum(polygon.material_index == index for polygon in new_faces)
        for index in range(len(body.material_slots))
    },
    "shapeKeys": len(mesh.shape_keys.key_blocks),
    "newVertexIndices": sorted(new_vertices),
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1069_SUPPORT_INSPECT=" + json.dumps({key: report[key] for key in ("newVertexCount", "facesTouchingNewVertices", "facesOnlyNewVertices", "newVertexBounds", "newFaceMaterialCounts", "shapeKeys")}, sort_keys=True))
