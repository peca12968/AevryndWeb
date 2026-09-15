import json
import math
import os
from pathlib import Path

import bpy
from mathutils import Quaternion


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = Path(os.environ.get(
    "AEVRYND_VALIDATION_SOURCE",
    ASSETS / "aevrynd-female-cc0-shoulder-corrective-shapekeys-r616.blend",
))
REVISION = os.environ.get("AEVRYND_VALIDATION_REVISION", "r617")
HIGH_CLAVICLE = float(os.environ.get("AEVRYND_HIGH_CLAVICLE", "1.25"))
HIGH_ARM = float(os.environ.get("AEVRYND_HIGH_ARM", "1.55"))
OUTPUT = ASSETS / f"aevrynd-female-cc0-dynamic-validation-{REVISION}.blend"
REPORT = ASSETS / f"female-v249-mainline-cc0-dynamic-validation-{REVISION}.build.json"
RIG = "AevryndFemaleRig"
DEFORM_BONES = (
    "pelvis", "spine_01", "spine_02", "chest", "neck", "head",
    "clavicle.L", "upper_arm.L", "forearm.L", "hand.L",
    "clavicle.R", "upper_arm.R", "forearm.R", "hand.R",
    "thigh.L", "shin.L", "foot.L", "thigh.R", "shin.R", "foot.R",
)
ARM_BONES = ("clavicle.L", "upper_arm.L", "clavicle.R", "upper_arm.R")


def scaled_rotation(quaternion, factor):
    quaternion = quaternion.normalized()
    return Quaternion(quaternion.axis, quaternion.angle * factor)


def set_identity(rig):
    for name in DEFORM_BONES:
        bone = rig.pose.bones[name]
        bone.rotation_mode = "QUATERNION"
        bone.location = (0.0, 0.0, 0.0)
        bone.rotation_quaternion = Quaternion()
        bone.scale = (1.0, 1.0, 1.0)


def key_pose(rig, frame, rotations):
    set_identity(rig)
    for name, quaternion in rotations.items():
        rig.pose.bones[name].rotation_quaternion = quaternion
    for name in DEFORM_BONES:
        bone = rig.pose.bones[name]
        bone.keyframe_insert("location", frame=frame, group=name)
        bone.keyframe_insert("rotation_quaternion", frame=frame, group=name)
        bone.keyframe_insert("scale", frame=frame, group=name)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
rig = bpy.data.objects[RIG]
scene.frame_set(20)
bpy.context.view_layer.update()
raised = {name: rig.pose.bones[name].rotation_quaternion.copy() for name in ARM_BONES}

action = bpy.data.actions.new(f"AevryndDynamicValidation_{REVISION}")
rig.animation_data_create()
rig.animation_data.action = action

identity = Quaternion()
poses = {
    1: ("neutral", {}),
    20: ("bilateral_raise", raised),
    33: ("left_raise", {
        "clavicle.L": raised["clavicle.L"],
        "upper_arm.L": raised["upper_arm.L"],
    }),
    61: ("right_raise", {
        "clavicle.R": raised["clavicle.R"],
        "upper_arm.R": raised["upper_arm.R"],
    }),
    80: ("bilateral_high_raise", {
        "clavicle.L": scaled_rotation(raised["clavicle.L"], HIGH_CLAVICLE),
        "upper_arm.L": scaled_rotation(raised["upper_arm.L"], HIGH_ARM),
        "clavicle.R": scaled_rotation(raised["clavicle.R"], HIGH_CLAVICLE),
        "upper_arm.R": scaled_rotation(raised["upper_arm.R"], HIGH_ARM),
    }),
    90: ("torso_twist", {
        "spine_02": Quaternion((0.0, 0.0, 1.0), math.radians(-12.0)),
    }),
    100: ("neck_turn", {
        "neck": Quaternion((0.0, 0.0, 1.0), math.radians(25.0)),
    }),
    110: ("torso_neck_twist_with_raise", {
        **raised,
        "spine_02": Quaternion((0.0, 0.0, 1.0), math.radians(-12.0)),
        "neck": Quaternion((0.0, 0.0, 1.0), math.radians(25.0)),
    }),
}
for frame, (_label, rotations) in poses.items():
    key_pose(rig, frame, rotations)
for layer in action.layers:
    for strip in layer.strips:
        for channelbag in strip.channelbags:
            for curve in channelbag.fcurves:
                for point in curve.keyframe_points:
                    point.interpolation = "LINEAR"

scene.frame_start = 1
scene.frame_end = 110
scene.frame_set(1)
scene["aevrynd_mainline_revision"] = f"v249{REVISION}-cc0-dynamic-validation"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_validation_frames"] = ",".join(str(frame) for frame in poses)
scene["aevrynd_release_state"] = "EXPANDED_DEFORMATION_AND_COLLISION_AUDIT_PENDING"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "action": action.name,
    "revision": REVISION,
    "highRaiseFactors": {"clavicle": HIGH_CLAVICLE, "upperArm": HIGH_ARM},
    "poses": {str(frame): label for frame, (label, _rotations) in poses.items()},
    "raisedQuaternions": {name: list(value) for name, value in raised.items()},
    "status": "EXPANDED_DEFORMATION_AND_COLLISION_AUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R617_VALIDATION_ACTION=" + json.dumps(report, sort_keys=True))
