import json
import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-satin-hair-r192.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-mouth-placement-r198.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-mouth-placement-r198.build-report.json"
BODY = "AevryndFemaleBodyBaseV118"
MOUTH_OBJECTS = ("Lip_Lower", "Lip_Upper", "Mouth_OralCavity", "Mouth_Tongue", "Mouth_UpperTeeth", "Mouth_WetLine")
SHIFT = 0.005


def smoothstep(edge0, edge1, value):
    value = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return value * value * (3.0 - 2.0 * value)


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def body_weight(p):
    if abs(p.x) > 0.082 or p.y > -0.072 or not (1.455 < p.z < 1.565):
        return 0.0
    lateral = gaussian(abs(p.x), 0.0, 0.050)
    front = smoothstep(-0.072, -0.116, p.y)
    upper = smoothstep(1.565, 1.548, p.z)
    lower = smoothstep(1.455, 1.492, p.z)
    return lateral * front * upper * lower


def move_object_world_z(obj, shift):
    obj.data = obj.data.copy()
    inverse = obj.matrix_world.inverted()
    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        world.z -= shift
        vertex.co = inverse @ world
    obj.data.update()
    obj["aevrynd_face_revision"] = "v249r198"
    return len(obj.data.vertices)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
key = body.shape_key_add(name="Aevrynd_MouthPlacement_R198_5mm", from_mix=True)
consolidated = [old.name for old in body.data.shape_keys.key_blocks[1:-1]]
for old in body.data.shape_keys.key_blocks[1:-1]:
    old.value = 0.0
key.value = 1.0
moved = 0
maximum = 0.0
for point in key.data:
    weight = body_weight(point.co)
    if weight <= 1e-6:
        continue
    delta = SHIFT * weight
    point.co.z -= delta
    moved += 1
    maximum = max(maximum, delta)
mouth_counts = {name: move_object_world_z(bpy.data.objects[name], SHIFT) for name in MOUTH_OBJECTS}
body.data.update()
body["aevrynd_face_revision"] = "v249r198"
body["aevrynd_face_layers"] = ["philtrum.consolidated", "eye_aperture.consolidated", "eyelid.anatomical.r183", "mouth.placement.r198"]
body["aevrynd_mouth_shift_mm"] = SHIFT * 1000.0
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_face_revision"] = "v249r198"
scene["aevrynd_mainline_revision"] = "mouth-placement-r198"
scene["aevrynd_release_state"] = "R198_COLLISION_AND_VISUAL_REVIEW_PENDING"
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "shapeKey": key.name,
    "consolidatedShapeKeys": consolidated, "mouthShiftMm": SHIFT * 1000.0,
    "bodyVerticesMoved": moved, "maximumBodyMoveMm": maximum * 1000.0,
    "mouthObjects": mouth_counts, "status": "COLLISION_AND_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249R198_MOUTH_PLACEMENT=" + json.dumps(report, sort_keys=True))
