import json
import math
import os
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = Path(os.environ.get(
    "AEVRYND_KNEE_SUPPORT_SOURCE",
    ASSETS / "aevrynd-female-cc0-elbow-crease-volume-r732.blend",
))
REVISION = os.environ.get("AEVRYND_KNEE_SUPPORT_REVISION", "r843")
STRENGTH = float(os.environ.get("AEVRYND_KNEE_SUPPORT_STRENGTH", "0.7"))
SIGMA = float(os.environ.get("AEVRYND_KNEE_SUPPORT_SIGMA", "0.055"))
INFLUENCE = float(os.environ.get("AEVRYND_KNEE_SUPPORT_ROTATION", "0.5"))
OUTPUT = ASSETS / f"aevrynd-female-cc0-knee-support-bones-{REVISION}.blend"
REPORT = ASSETS / f"female-v249-mainline-cc0-knee-support-bones-{REVISION}.build.json"
BODY = "AevryndFemaleCC0Baseline_v259"
RIG = "AevryndFemaleRig"


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
rig = bpy.data.objects[RIG]

bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
created_bones = {}
for side in ("L", "R"):
    shin = rig.data.edit_bones[f"shin.{side}"]
    support = rig.data.edit_bones.new(f"knee_support.{side}")
    support.head = shin.head
    support.tail = shin.tail
    support.roll = shin.roll
    support.parent = rig.data.edit_bones[f"thigh.{side}"]
    support.use_connect = False
    support.use_deform = True
    created_bones[side] = {
        "head": list(support.head), "tail": list(support.tail),
        "parent": support.parent.name,
    }
bpy.ops.object.mode_set(mode="POSE")
for side in ("L", "R"):
    support = rig.pose.bones[f"knee_support.{side}"]
    support.rotation_mode = "QUATERNION"
    constraint = support.constraints.new("COPY_ROTATION")
    constraint.name = "AevryndKneePartialFlex"
    constraint.target = rig
    constraint.subtarget = f"shin.{side}"
    constraint.target_space = "LOCAL"
    constraint.owner_space = "LOCAL"
    constraint.mix_mode = "REPLACE"
    constraint.influence = INFLUENCE
bpy.ops.object.mode_set(mode="OBJECT")

weight_report = {}
for side, sign in (("L", 1.0), ("R", -1.0)):
    thigh_group = body.vertex_groups[f"thigh.{side}"]
    shin_group = body.vertex_groups[f"shin.{side}"]
    support_group = body.vertex_groups.new(name=f"knee_support.{side}")
    joint = rig.data.bones[f"shin.{side}"].head_local
    changed = 0
    maximum_support = 0.0
    for vertex in body.data.vertices:
        try:
            thigh_weight = thigh_group.weight(vertex.index)
        except RuntimeError:
            thigh_weight = 0.0
        try:
            shin_weight = shin_group.weight(vertex.index)
        except RuntimeError:
            shin_weight = 0.0
        combined = thigh_weight + shin_weight
        if combined <= 1e-9:
            continue
        distance = (body.matrix_world @ vertex.co - rig.matrix_world @ joint).length
        falloff = math.exp(-(distance * distance) / (2.0 * SIGMA * SIGMA))
        support_weight = min(combined, combined * STRENGTH * falloff)
        if support_weight < 0.001:
            continue
        retained = max(0.0, (combined - support_weight) / combined)
        thigh_group.add([vertex.index], thigh_weight * retained, "REPLACE")
        shin_group.add([vertex.index], shin_weight * retained, "REPLACE")
        support_group.add([vertex.index], support_weight, "REPLACE")
        changed += 1
        maximum_support = max(maximum_support, support_weight)
    weight_report[side] = {
        "vertices": changed,
        "maximumSupportWeight": maximum_support,
        "joint": list(joint),
    }

bpy.context.view_layer.update()
body["aevrynd_revision"] = f"v249{REVISION}"
body["aevrynd_knee_support_bones"] = "partial-flex support bones with localized normalized weights"
rig["aevrynd_knee_support_rotation_fraction"] = INFLUENCE
scene["aevrynd_mainline_revision"] = f"v249{REVISION}-cc0-knee-support-bones"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "FULL_JOINT_DEFORMATION_AND_COLLISION_AUDIT_PENDING"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "revision": REVISION,
    "strength": STRENGTH, "sigmaM": SIGMA, "rotationInfluence": INFLUENCE,
    "bones": created_bones, "weights": weight_report,
    "status": "FULL_JOINT_DEFORMATION_AND_COLLISION_AUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_KNEE_SUPPORT_BONES=" + json.dumps(report, sort_keys=True))
