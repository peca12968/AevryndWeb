import json
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-recessed-natural-eyes-r301.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-body-eye-intersection-r312.audit.json"
BODY = "AevryndFemaleBody_CC0_R249"
FRAMES = (1, 20)


def tree(obj, depsgraph):
    return BVHTree.FromObject(obj, depsgraph)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
shape_keys = []
if body.data.shape_keys:
    shape_keys = [{"name": block.name, "value": block.value} for block in body.data.shape_keys.key_blocks]
stack = {
    "object": body.name,
    "meshVertices": len(body.data.vertices),
    "meshPolygons": len(body.data.polygons),
    "evaluatedVerticesFrame1": None,
    "modifiers": [{"name": modifier.name, "type": modifier.type, "showRender": modifier.show_render, "showViewport": modifier.show_viewport} for modifier in body.modifiers],
    "shapeKeys": shape_keys,
}
frames = {}
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    evaluated_mesh = evaluated.to_mesh()
    if frame == 1:
        stack["evaluatedVerticesFrame1"] = len(evaluated_mesh.vertices)
    evaluated.to_mesh_clear()
    body_tree = tree(body, depsgraph)
    rows = {}
    for side in ("L", "R"):
        parts = {}
        for part in ("Sclera_R249", "Cornea_R252", "Limbal_R253", "Iris_R253", "Pupil_R253"):
            obj = bpy.data.objects[f"AevryndEye_{side}_{part}"]
            parts[part] = len(body_tree.overlap(tree(obj, depsgraph)))
        rows[side] = parts
    frames[str(frame)] = rows
report = {
    "source": str(SOURCE),
    "bodyStack": stack,
    "frames": frames,
    "totalTriangleOverlaps": sum(value for frame in frames.values() for side in frame.values() for value in side.values()),
}
report["status"] = "PASS" if report["totalTriangleOverlaps"] == 0 else "FAIL_BODY_EYE_INTERSECTION"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R312_BODY_EYE_INTERSECTION=" + json.dumps(report, sort_keys=True))
