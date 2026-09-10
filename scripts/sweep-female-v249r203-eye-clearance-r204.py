import json
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-natural-eye-aperture-r203.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-eye-clearance-r204.sweep-report.json"
BODY = "AevryndFemaleBodyBaseV118"
LAYERS = ("Eye_L_UpperLashes", "Eye_R_UpperLashes", "Eye_L_TearMeniscus", "Eye_R_TearMeniscus")
OFFSETS_MM = (0.0, 0.15, 0.30, 0.45, 0.60, 0.80)


def tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    try:
        points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
        faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
        return BVHTree.FromPolygons(points, faces, all_triangles=False)
    finally:
        evaluated.to_mesh_clear()


def offset_world_y(obj, amount):
    obj.data = obj.data.copy()
    inverse = obj.matrix_world.inverted()
    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        world.y -= amount
        vertex.co = inverse @ world
    obj.data.update()


report = {"source": str(SOURCE), "offsets": {}, "selectionRule": "minimum symmetric offset with zero body overlaps at frames 1 and 20"}
for offset_mm in OFFSETS_MM:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    amount = offset_mm / 1000.0
    if amount:
        for name in LAYERS:
            offset_world_y(bpy.data.objects[name], amount)
    frames = {}
    for frame in (1, 20):
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        body_tree = tree(bpy.data.objects[BODY], depsgraph)
        frames[str(frame)] = {
            name: len(body_tree.overlap(tree(bpy.data.objects[name], depsgraph)))
            for name in LAYERS
        }
    report["offsets"][f"{offset_mm:.2f}mm"] = frames

selected = None
for offset_mm in OFFSETS_MM:
    frames = report["offsets"][f"{offset_mm:.2f}mm"]
    if all(count == 0 for values in frames.values() for count in values.values()):
        selected = offset_mm
        break
report["selectedOffsetMm"] = selected
report["status"] = "PASS" if selected is not None else "FAIL"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R204_EYE_CLEARANCE=" + json.dumps(report, sort_keys=True))
if selected is None:
    raise SystemExit(2)
