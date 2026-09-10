import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r17.blend"
BONES = ("root", "pelvis", "spine", "chest", "neck", "head", "upper_arm.L", "upper_arm.R")

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
rig = bpy.data.objects["AevryndFemaleRig"]
report = {}
for frame in (1, 20):
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    values = {}
    for name in BONES:
        bone = rig.pose.bones.get(name)
        if bone:
            matrix = rig.matrix_world @ bone.matrix
            values[name] = {
                "translation": [round(value, 6) for value in matrix.translation],
                "quaternion": [round(value, 6) for value in matrix.to_quaternion()],
            }
    report[str(frame)] = values
print("AEVRYND_V249_POSE_TRANSFORMS=" + json.dumps(report, sort_keys=True))
