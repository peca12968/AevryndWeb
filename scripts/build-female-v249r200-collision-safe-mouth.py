import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-mouth-placement-r198.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-collision-safe-mouth-r200.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-collision-safe-mouth-r200.build-report.json"
OFFSET = 0.00030
LAYERS = ("Lip_Upper", "Mouth_WetLine")


def offset_world_y(obj, amount):
    obj.data = obj.data.copy()
    inverse = obj.matrix_world.inverted()
    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        world.y -= amount
        vertex.co = inverse @ world
    obj.data.update()
    obj["aevrynd_face_revision"] = "v249r200"
    obj["aevrynd_clearance_offset_mm"] = amount * 1000.0
    return len(obj.data.vertices)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
counts = {name: offset_world_y(bpy.data.objects[name], OFFSET) for name in LAYERS}
body = bpy.data.objects["AevryndFemaleBodyBaseV118"]
body["aevrynd_face_revision"] = "v249r200"
body["aevrynd_face_layers"] = ["philtrum.consolidated", "eye_aperture.consolidated", "eyelid.anatomical.r183", "mouth.placement.r198", "mouth.clearance.r200"]
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_face_revision"] = "v249r200"
scene["aevrynd_mainline_revision"] = "collision-safe-mouth-r200"
scene["aevrynd_release_state"] = "R200_COLLISION_AND_VISUAL_REVIEW_PENDING"
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "mouthShiftMm": 5.0,
    "clearanceOffsetMm": OFFSET * 1000.0, "offsetLayers": counts,
    "status": "COLLISION_AND_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249R200_COLLISION_SAFE_MOUTH=" + json.dumps(report, sort_keys=True))
