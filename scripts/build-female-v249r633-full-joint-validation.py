import json
import math
import os
from pathlib import Path

import bpy
from mathutils import Quaternion


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = Path(os.environ.get(
    "AEVRYND_FULL_JOINT_SOURCE",
    ASSETS / "aevrynd-female-cc0-twist-raise-interaction-r630.blend",
))
REVISION = os.environ.get("AEVRYND_FULL_JOINT_REVISION", "r633")
OUTPUT = ASSETS / f"aevrynd-female-cc0-full-joint-validation-{REVISION}.blend"
REPORT = ASSETS / f"female-v249-mainline-cc0-full-joint-validation-{REVISION}.build.json"
RIG = "AevryndFemaleRig"
DEFORM_BONES = (
    "pelvis", "spine_01", "spine_02", "chest", "neck", "head",
    "clavicle.L", "upper_arm.L", "forearm.L", "hand.L",
    "clavicle.R", "upper_arm.R", "forearm.R", "hand.R",
    "thigh.L", "shin.L", "foot.L", "thigh.R", "shin.R", "foot.R",
)
ARM_BONES = ("clavicle.L", "upper_arm.L", "clavicle.R", "upper_arm.R")


def rotation(axis, degrees):
    return Quaternion(axis, math.radians(degrees))


def reset_pose(rig):
    for name in DEFORM_BONES:
        bone = rig.pose.bones[name]
        bone.rotation_mode = "QUATERNION"
        bone.location = (0.0, 0.0, 0.0)
        bone.rotation_quaternion = Quaternion()
        bone.scale = (1.0, 1.0, 1.0)


def key_pose(rig, frame, rotations):
    reset_pose(rig)
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

action = bpy.data.actions.new(f"AevryndFullJointValidation_{REVISION}")
rig.animation_data_create()
rig.animation_data.action = action
poses = {
    1: ("neutral", {}),
    20: ("left_elbow_flex", {"forearm.L": rotation((0, 0, 1), -70)}),
    30: ("right_elbow_flex", {"forearm.R": rotation((0, 0, 1), 70)}),
    40: ("bilateral_elbow_flex", {
        "forearm.L": rotation((0, 0, 1), -70),
        "forearm.R": rotation((0, 0, 1), 70),
    }),
    50: ("bilateral_forearm_pronation", {
        "forearm.L": rotation((0, 1, 0), 60),
        "forearm.R": rotation((0, 1, 0), -60),
    }),
    60: ("bilateral_wrist_flex", {
        "hand.L": rotation((1, 0, 0), 35),
        "hand.R": rotation((1, 0, 0), 35),
    }),
    70: ("left_hip_flex", {"thigh.L": rotation((1, 0, 0), -45)}),
    80: ("right_hip_flex", {"thigh.R": rotation((1, 0, 0), -45)}),
    90: ("bilateral_hip_flex", {
        "thigh.L": rotation((1, 0, 0), -45),
        "thigh.R": rotation((1, 0, 0), -45),
    }),
    100: ("left_knee_flex", {"shin.L": rotation((1, 0, 0), 75)}),
    110: ("right_knee_flex", {"shin.R": rotation((1, 0, 0), 75)}),
    120: ("bilateral_knee_flex", {
        "shin.L": rotation((1, 0, 0), 75),
        "shin.R": rotation((1, 0, 0), 75),
    }),
    130: ("squat_chain", {
        "thigh.L": rotation((1, 0, 0), -45),
        "thigh.R": rotation((1, 0, 0), -45),
        "shin.L": rotation((1, 0, 0), 85),
        "shin.R": rotation((1, 0, 0), 85),
        "foot.L": rotation((1, 0, 0), -40),
        "foot.R": rotation((1, 0, 0), -40),
    }),
    140: ("stride", {
        "thigh.L": rotation((1, 0, 0), -30),
        "shin.L": rotation((1, 0, 0), 18),
        "thigh.R": rotation((1, 0, 0), 25),
        "shin.R": rotation((1, 0, 0), 35),
    }),
    150: ("raised_arms_with_elbow_flex", {
        **raised,
        "forearm.L": rotation((0, 0, 1), -70),
        "forearm.R": rotation((0, 0, 1), 70),
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
scene.frame_end = 150
scene.frame_set(1)
scene["aevrynd_mainline_revision"] = f"v249{REVISION}-cc0-full-joint-validation"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_validation_frames"] = ",".join(str(frame) for frame in poses)
scene["aevrynd_release_state"] = "FULL_JOINT_DEFORMATION_AND_COLLISION_AUDIT_PENDING"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "action": action.name,
    "revision": REVISION,
    "poses": {str(frame): label for frame, (label, _rotations) in poses.items()},
    "status": "FULL_JOINT_DEFORMATION_AND_COLLISION_AUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R633_FULL_JOINT_VALIDATION=" + json.dumps(report, sort_keys=True))
