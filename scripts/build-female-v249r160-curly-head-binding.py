import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-curly-r156.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-curly-head-binding-r160.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-curly-head-binding-r160.build-report.json"
HAIR = "AevryndFemaleOwnedCurlyHairMain_v249r156"
RIG = "AevryndFemaleRig"


def bone_parent(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
hair = bpy.data.objects[HAIR]
before = {
    "parent": hair.parent.name if hair.parent else None,
    "parentType": hair.parent_type,
    "parentBone": hair.parent_bone,
}
bone_parent(hair, bpy.data.objects[RIG])
hair.name = "AevryndFemaleOwnedCurlyHairMain_v249r160"
hair.data.name = hair.name + "Data"
hair["aevrynd_revision"] = "v249r160"
hair["aevrynd_binding"] = "rigid head-bone parent"
hair["aevrynd_collision_status"] = "PENDING_STRICT_AUDIT"
scene["aevrynd_revision"] = "v249r160"
scene["aevrynd_candidate_status"] = "COLLISION_AND_VISUAL_REVIEW_PENDING"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "object": hair.name,
    "before": before,
    "after": {
        "parent": hair.parent.name if hair.parent else None,
        "parentType": hair.parent_type,
        "parentBone": hair.parent_bone,
    },
    "curves": len(hair.data.curves),
    "points": len(hair.data.points),
    "runtimeDependency": "none",
    "status": "COLLISION_AND_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R160_BUILD=" + json.dumps(report, sort_keys=True))
