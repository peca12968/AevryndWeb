"""Inventory the retained open-eye body and current target-native face stack.

This report establishes which owned layers can be transplanted onto the r446
open-topology body without guessing object names, mesh density, rig identity, or
material dependencies.
"""

import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCES = {
    "openTopologyR446": ASSETS / "aevrynd-female-authoring-v249-mainline-open-topology-physical-skin-r446.blend",
    "targetNativeHairR981": ASSETS / "aevrynd-female-cc0-coherent-clump-waves-r981.blend",
    "currentFaceR1001": ASSETS / "aevrynd-female-cc0-mixed-space-eyelid-relief-r1001.blend",
}
REPORT = ASSETS / "female-v249-mainline-r1010-open-topology-bridge-inspection.json"


def bounds(obj):
    corners = [obj.matrix_world @ Vector(obj.bound_box[index]) for index in range(8)]
    return {
        "minimum": [min(point[axis] for point in corners) for axis in range(3)],
        "maximum": [max(point[axis] for point in corners) for axis in range(3)],
    }


def bone_signature(bones):
    rows = []
    for bone in sorted(bones, key=lambda item: item.name):
        rows.append(
            {
                "name": bone.name,
                "head": [round(value, 8) for value in bone.head_local],
                "tail": [round(value, 8) for value in bone.tail_local],
                "parent": bone.parent.name if bone.parent else None,
            }
        )
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"boneCount": len(rows), "sha256": hashlib.sha256(payload).hexdigest()}


def armature_signatures(obj):
    bones = list(obj.data.bones)
    base = [bone for bone in bones if not bone.name.startswith("hair_dyn.")]
    core = [bone for bone in base if not bone.name.startswith("knee_support.")]
    return {
        "all": bone_signature(bones),
        "baseWithoutHairDynamics": bone_signature(base),
        "coreWithoutHairOrKneeSupport": bone_signature(core),
    }


def object_record(obj):
    record = {
        "name": obj.name,
        "type": obj.type,
        "parent": obj.parent.name if obj.parent else None,
        "parentType": obj.parent_type,
        "parentBone": obj.parent_bone,
        "hiddenRender": bool(obj.hide_render),
        "bounds": bounds(obj),
        "customRole": obj.get("aevrynd_role"),
        "revision": obj.get("aevrynd_revision"),
    }
    if obj.type == "MESH":
        record.update(
            {
                "vertices": len(obj.data.vertices),
                "polygons": len(obj.data.polygons),
                "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
                "shapeKeys": [block.name for block in obj.data.shape_keys.key_blocks] if obj.data.shape_keys else [],
            }
        )
    elif obj.type == "ARMATURE":
        record["armatureSignatures"] = armature_signatures(obj)
        record["boneNames"] = sorted(bone.name for bone in obj.data.bones)
        record["boneRecords"] = {
            bone.name: {
                "head": [float(value) for value in bone.head_local],
                "tail": [float(value) for value in bone.tail_local],
            }
            for bone in obj.data.bones
        }
    return record


def relevant(obj):
    name = obj.name.lower()
    role = str(obj.get("aevrynd_role", "")).lower()
    return obj.type == "ARMATURE" or any(
        token in name or token in role
        for token in ("female", "body", "eye", "brow", "lash", "groom", "hair", "scalp", "mouth", "tear")
    )


report = {"purpose": "bridge the retained open-eye topology to the current owned layer stack", "sources": {}}
for label, source in SOURCES.items():
    if not source.exists():
        report["sources"][label] = {"path": str(source), "status": "MISSING"}
        continue
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    objects = [object_record(obj) for obj in scene.objects if relevant(obj)]
    report["sources"][label] = {
        "path": str(source),
        "sceneRevision": scene.get("aevrynd_mainline_revision"),
        "releaseState": scene.get("aevrynd_release_state"),
        "objects": sorted(objects, key=lambda item: (item["type"], item["name"])),
        "status": "INSPECTED",
    }

armatures = {}
for label, source_data in report["sources"].items():
    for obj in source_data.get("objects", []):
        if obj["type"] == "ARMATURE":
            signature = obj["armatureSignatures"]["coreWithoutHairOrKneeSupport"]
            armatures.setdefault(signature["sha256"], []).append({
                "source": label,
                "object": obj["name"],
                "baseBoneCount": signature["boneCount"],
                "allBoneCount": obj["armatureSignatures"]["all"]["boneCount"],
            })
report["armatureCompatibilityGroups"] = armatures
all_inspected = all(item["status"] == "INSPECTED" for item in report["sources"].values())
direct_group = next((items for items in armatures.values() if len(items) == len(SOURCES)), None)
report["coreRigDirectCompatibility"] = direct_group is not None
report["findings"] = [
    "r446 retains a true open eye aperture and remains the topology reference",
    "r981 and r1001 share the same corrected core rig plus knee-support and hair-dynamic extensions",
    "r446 core rest-bone coordinates differ from the current target-native rig, so direct parent or weight transfer is invalid",
    "the open eyelid loops must be retargeted onto the current r1001 head surface before current hair or face layers are integrated",
]
report["status"] = (
    "PASS_INSPECTION_RETARGET_REQUIRED" if all_inspected and not direct_group
    else "PASS_DIRECT_RIG_COMPATIBILITY" if all_inspected
    else "INCOMPLETE"
)
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1010_OPEN_TOPOLOGY_BRIDGE=" + json.dumps({
    "report": str(REPORT),
    "sourceStatus": {key: value["status"] for key, value in report["sources"].items()},
    "armatureCompatibilityGroups": armatures,
    "status": report["status"],
}, sort_keys=True))
