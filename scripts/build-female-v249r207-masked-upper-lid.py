import json
import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-collision-safe-mouth-r200.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-masked-upper-lid-r207.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-masked-upper-lid-r207.build-report.json"
BODY = "AevryndFemaleBodyBaseV118"
EYES = (0.034528, -0.034443)
STRENGTH = 1.75
LASH_CLEARANCE = 0.00045


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def smoothstep(edge0, edge1, value):
    value = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return value * value * (3.0 - 2.0 * value)


def consolidate(body, name):
    key = body.shape_key_add(name=name, from_mix=True)
    previous = [old.name for old in body.data.shape_keys.key_blocks[1:-1]]
    for old in body.data.shape_keys.key_blocks[1:-1]:
        old.value = 0.0
    key.value = 1.0
    return key, previous


def upper_weight(p, center_x):
    dx = (p.x - center_x) / 0.0315
    if abs(dx) >= 1.05 or p.y > -0.094 or not (1.603 < p.z < 1.626):
        return 0.0
    horizontal = max(0.0, 1.0 - (abs(dx) / 1.05) ** 3) ** 1.35
    lower_guard = smoothstep(1.6030, 1.6060, p.z)
    return horizontal * lower_guard * gaussian(p.y, -0.126, 0.023) * gaussian(p.z, 1.6096, 0.0037)


def open_upper_lid(key):
    moved = 0
    maximum = 0.0
    for point in key.data:
        weight = max(upper_weight(point.co, center_x) for center_x in EYES)
        delta = STRENGTH * 0.00100 * weight
        if delta <= 1e-7:
            continue
        point.co.z += delta
        moved += 1
        maximum = max(maximum, delta)
    return {"verticesMoved": moved, "maximumMoveMm": maximum * 1000.0, "lowerGuardStartZ": 1.6030, "lowerGuardFullZ": 1.6060}


def move_lashes(obj):
    obj.data = obj.data.copy()
    inverse = obj.matrix_world.inverted()
    moved = 0
    maximum_z = 0.0
    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        horizontal = 0.0
        for center_x in EYES:
            dx = (world.x - center_x) / 0.0315
            if abs(dx) < 1.08:
                horizontal = max(horizontal, max(0.0, 1.0 - (abs(dx) / 1.08) ** 3) ** 1.35)
        delta_z = STRENGTH * 0.00100 * horizontal * gaussian(world.z, 1.6096, 0.0042)
        world.z += delta_z
        world.y -= LASH_CLEARANCE
        vertex.co = inverse @ world
        moved += 1
        maximum_z = max(maximum_z, delta_z)
    obj.data.update()
    obj["aevrynd_face_revision"] = "v249r207"
    obj["aevrynd_clearance_offset_mm"] = LASH_CLEARANCE * 1000.0
    return {"verticesMoved": moved, "maximumVerticalMoveMm": maximum_z * 1000.0, "outwardClearanceMm": LASH_CLEARANCE * 1000.0}


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
key, previous = consolidate(body, "Aevrynd_MaskedUpperLid_R207")
metrics = open_upper_lid(key)
metrics["shapeKey"] = key.name
metrics["consolidatedShapeKeys"] = previous
metrics["upperLashes"] = {
    f"Eye_{side}_UpperLashes": move_lashes(bpy.data.objects[f"Eye_{side}_UpperLashes"])
    for side in ("L", "R")
}
body.data.update()
body["aevrynd_face_revision"] = "v249r207"
body["aevrynd_eye_aperture"] = "r205 d-open with lower-lid guard and 0.45mm upper-lash clearance"
body["aevrynd_face_layers"] = ["philtrum.consolidated", "eyelid.anatomical.r183", "mouth.placement.r200", "upper_lid.masked_opening.r207"]
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_face_revision"] = "v249r207"
scene["aevrynd_mainline_revision"] = "masked-upper-lid-r207"
scene["aevrynd_release_state"] = "R207_COLLISION_AND_VISUAL_REVIEW_PENDING"
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "selectedSweepVariant": "r205 d-open",
    "strength": STRENGTH,
    "lashClearanceMm": LASH_CLEARANCE * 1000.0,
    "preservedLayers": ["lower eyelid body region", "tear menisci", "caruncles"],
    "metrics": metrics,
    "status": "COLLISION_AND_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249R207_MASKED_UPPER_LID=" + json.dumps(report, sort_keys=True))
