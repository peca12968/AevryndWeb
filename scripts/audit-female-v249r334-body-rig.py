import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-continuous-upper-lower-eyelids-r334.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-continuous-upper-lower-eyelids-r334.body-rig-audit.json"
BODY = "AevryndFemaleBody_CC0_R249"
FRAMES = (1, 20)


def evaluated_positions(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    positions = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = len(mesh.polygons)
    evaluated.to_mesh_clear()
    return positions, polygons


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
failures = []
armatures = [modifier for modifier in body.modifiers if modifier.type == "ARMATURE"]
if len(armatures) != 1:
    failures.append({"armatureModifierCount": len(armatures), "expected": 1})
unweighted = sum(1 for vertex in body.data.vertices if not vertex.groups)
if unweighted:
    failures.append({"unweightedVertices": unweighted})
snapshots = {}
polygons = {}
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    snapshots[frame], polygons[frame] = evaluated_positions(body)
if len(snapshots[1]) != len(snapshots[20]):
    failures.append({"evaluatedVertexCountMismatch": [len(snapshots[1]), len(snapshots[20])]})
count = min(len(snapshots[1]), len(snapshots[20]))
deltas = [(snapshots[20][index] - snapshots[1][index]).length for index in range(count)]
maximum = max(deltas, default=0.0)
moved = sum(value > 1e-6 for value in deltas)
if maximum <= 1e-6 or moved == 0:
    failures.append({"missingDeformation": {"maximumM": maximum, "movedVertices": moved}})
report = {
    "model": str(MODEL), "baseVertices": len(body.data.vertices), "basePolygons": len(body.data.polygons),
    "vertexGroups": len(body.vertex_groups), "unweightedVertices": unweighted,
    "modifiers": [{"name": item.name, "type": item.type} for item in body.modifiers],
    "evaluatedVertices": {str(frame): len(snapshots[frame]) for frame in FRAMES},
    "evaluatedPolygons": {str(frame): polygons[frame] for frame in FRAMES},
    "frame1To20": {"movedVerticesOver1um": moved, "maximumDisplacementM": maximum},
    "failures": failures, "status": "PASS" if not failures else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R328_BODY_RIG_AUDIT=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
