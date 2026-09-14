import hashlib
import json
import struct
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
BASELINE = ASSETS / "aevrynd-female-authoring-v249-mainline-sorted-tear-film-r499.blend"
CANDIDATE = ASSETS / "aevrynd-female-authoring-v249-mainline-layered-rear-locks-r506.blend"
REPORT = ASSETS / "female-v249-mainline-layered-rear-locks-r506.static-parity-audit.json"
OLD_REAR = "AevryndFemaleRuntimeCards_rear_R467"
NEW_REAR = "AevryndFemaleRuntimeLayeredLocks_rear_R506"


def digest(obj):
    value = hashlib.sha256()
    value.update(struct.pack("<II", len(obj.data.vertices), len(obj.data.polygons)))
    for vertex in obj.data.vertices:
        value.update(struct.pack("<fff", *vertex.co))
    for polygon in obj.data.polygons:
        value.update(struct.pack("<I", len(polygon.vertices)))
        for index in polygon.vertices:
            value.update(struct.pack("<I", index))
    return value.hexdigest()


def inventory(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    return {obj.name: digest(obj) for obj in bpy.data.objects if obj.type == "MESH"}


baseline = inventory(BASELINE)
candidate = inventory(CANDIDATE)
added = sorted(set(candidate) - set(baseline))
removed = sorted(set(baseline) - set(candidate))
changed = sorted(name for name, value in baseline.items() if candidate.get(name) != value)

bpy.ops.wm.open_mainfile(filepath=str(CANDIDATE))
old = bpy.data.objects[OLD_REAR]
new = bpy.data.objects[NEW_REAR]
topology = {
    "oldRear": {
        "vertices": len(old.data.vertices),
        "polygons": len(old.data.polygons),
        "cards": int(old.get("aevrynd_card_count", 0)),
        "hideRender": old.hide_render,
        "hideViewport": old.hide_viewport,
        "replacedBy": old.get("aevrynd_replaced_by"),
    },
    "newRear": {
        "vertices": len(new.data.vertices),
        "polygons": len(new.data.polygons),
        "cards": int(new.get("aevrynd_card_count", 0)),
        "parent": new.parent.name if new.parent else None,
        "armatureModifiers": [modifier.object.name for modifier in new.modifiers if modifier.type == "ARMATURE" and modifier.object],
        "vertexGroups": [group.name for group in new.vertex_groups],
        "layer": new.get("aevrynd_layer"),
        "ownership": new.get("aevrynd_ownership"),
    },
}
failures = []
if added != [NEW_REAR]:
    failures.append({"category": "unexpectedAddedMeshes", "actual": added})
if removed:
    failures.append({"category": "removedMeshes", "actual": removed})
if changed:
    failures.append({"category": "changedExistingGeometry", "actual": changed})
if not old.hide_render or not old.hide_viewport or old.get("aevrynd_replaced_by") != NEW_REAR:
    failures.append({"category": "oldRearNotExplicitlyReplaced", "actual": topology["oldRear"]})
if topology["newRear"]["cards"] != 280 or topology["newRear"]["vertices"] != 13440 or topology["newRear"]["polygons"] != 6440:
    failures.append({"category": "unexpectedNewRearTopology", "actual": topology["newRear"]})
if topology["newRear"]["parent"] != "AevryndFemaleRig" or topology["newRear"]["armatureModifiers"] != ["AevryndFemaleRig"]:
    failures.append({"category": "invalidNewRearBinding", "actual": topology["newRear"]})

report = {
    "baseline": str(BASELINE),
    "candidate": str(CANDIDATE),
    "addedMeshes": added,
    "removedMeshes": removed,
    "changedExistingGeometry": changed,
    "topology": topology,
    "visibleRearCardDelta": -200,
    "visibleRearVertexDelta": -9600,
    "visibleRearPolygonDelta": -4600,
    "failures": failures,
    "status": "PASS" if not failures else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R506_STATIC_PARITY=" + json.dumps({"status": report["status"], "failures": failures}, sort_keys=True))
if failures:
    raise SystemExit(2)
