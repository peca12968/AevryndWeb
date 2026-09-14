import hashlib
import json
import struct
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
BASELINE = ASSETS / "aevrynd-female-authoring-v249-mainline-layered-rear-locks-r506.blend"
CANDIDATE = ASSETS / "aevrynd-female-authoring-v249-mainline-lighter-neutral-skin-r510.blend"
REPORT = ASSETS / "female-v249-mainline-lighter-neutral-skin-r510.material-parity-audit.json"
BODY = "AevryndFemaleBodyBaseV118"


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
    meshes = {obj.name: digest(obj) for obj in bpy.data.objects if obj.type == "MESH"}
    armatures = {
        obj.name: [(bone.name, tuple(bone.head_local), tuple(bone.tail_local), bone.parent.name if bone.parent else None) for bone in obj.data.bones]
        for obj in bpy.data.objects if obj.type == "ARMATURE"
    }
    material = bpy.data.objects[BODY].data.materials[0]
    ramp = material.node_tree.nodes["Aevrynd restrained melanin range"].color_ramp
    return {
        "meshes": meshes,
        "armatures": armatures,
        "skinMaterial": material.name,
        "skinNodeCount": len(material.node_tree.nodes),
        "skinLinkCount": len(material.node_tree.links),
        "ramp": [list(element.color) for element in ramp.elements],
    }


baseline = inventory(BASELINE)
candidate = inventory(CANDIDATE)
changed_meshes = sorted(name for name, value in baseline["meshes"].items() if candidate["meshes"].get(name) != value)
failures = []
if set(baseline["meshes"]) != set(candidate["meshes"]):
    failures.append("mesh inventory changed")
if changed_meshes:
    failures.append("mesh geometry changed")
if baseline["armatures"] != candidate["armatures"]:
    failures.append("armature changed")
if baseline["skinNodeCount"] != candidate["skinNodeCount"] or baseline["skinLinkCount"] != candidate["skinLinkCount"]:
    failures.append("skin shader topology changed")
expected = [[0.145, 0.050, 0.032, 1.0], [0.188, 0.070, 0.042, 1.0]]
for actual, target in zip(candidate["ramp"], expected):
    if any(abs(a - b) > 1e-6 for a, b in zip(actual, target)):
        failures.append("candidate ramp does not match selected r509 b values")
        break
report = {
    "baseline": str(BASELINE),
    "candidate": str(CANDIDATE),
    "meshCount": len(candidate["meshes"]),
    "changedMeshes": changed_meshes,
    "armatureExact": baseline["armatures"] == candidate["armatures"],
    "shaderTopologyExact": baseline["skinNodeCount"] == candidate["skinNodeCount"] and baseline["skinLinkCount"] == candidate["skinLinkCount"],
    "baselineRampLinearRGBA": baseline["ramp"],
    "candidateRampLinearRGBA": candidate["ramp"],
    "failures": failures,
    "status": "PASS" if not failures else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R510_MATERIAL_PARITY=" + json.dumps({"status": report["status"], "changedMeshes": changed_meshes}))
if failures:
    raise SystemExit(2)
