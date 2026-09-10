import json
import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-collision-safe-mouth-r200.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-natural-eye-aperture-r203.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-natural-eye-aperture-r203.build-report.json"
BODY = "AevryndFemaleBodyBaseV118"
EYES = (0.034528, -0.034443)
STRENGTH = 1.5


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def consolidate(body, name):
    key = body.shape_key_add(name=name, from_mix=True)
    previous = [old.name for old in body.data.shape_keys.key_blocks[1:-1]]
    for old in body.data.shape_keys.key_blocks[1:-1]:
        old.value = 0.0
    key.value = 1.0
    return key, previous


def eye_weight(p, center_x):
    dx = (p.x - center_x) / 0.0315
    if abs(dx) >= 1.05 or p.y > -0.094 or not (1.588 < p.z < 1.626):
        return 0.0, 0.0
    horizontal = max(0.0, 1.0 - (abs(dx) / 1.05) ** 3) ** 1.35
    front = gaussian(p.y, -0.126, 0.023)
    return (
        horizontal * front * gaussian(p.z, 1.6096, 0.0037),
        horizontal * front * gaussian(p.z, 1.5995, 0.0035),
    )


def open_body(key):
    moved = 0
    maximum = 0.0
    upper_maximum = 0.0
    lower_maximum = 0.0
    for point in key.data:
        upper = lower = 0.0
        for center_x in EYES:
            local_upper, local_lower = eye_weight(point.co, center_x)
            upper = max(upper, local_upper)
            lower = max(lower, local_lower)
        delta = STRENGTH * (0.00100 * upper - 0.00038 * lower)
        if abs(delta) <= 1e-7:
            continue
        point.co.z += delta
        moved += 1
        maximum = max(maximum, abs(delta))
        upper_maximum = max(upper_maximum, max(delta, 0.0))
        lower_maximum = max(lower_maximum, max(-delta, 0.0))
    return {
        "verticesMoved": moved,
        "maximumMoveMm": maximum * 1000.0,
        "upperMaximumMm": upper_maximum * 1000.0,
        "lowerMaximumMm": lower_maximum * 1000.0,
        "nominalApertureIncreaseMm": STRENGTH * 1.38,
    }


def move_accessory(obj, direction, center_z, sigma):
    obj.data = obj.data.copy()
    inverse = obj.matrix_world.inverted()
    moved = 0
    maximum = 0.0
    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        horizontal = 0.0
        for center_x in EYES:
            dx = (world.x - center_x) / 0.0315
            if abs(dx) < 1.08:
                horizontal = max(horizontal, max(0.0, 1.0 - (abs(dx) / 1.08) ** 3) ** 1.35)
        amount = STRENGTH * direction * horizontal * gaussian(world.z, center_z, sigma)
        if abs(amount) <= 1e-7:
            continue
        world.z += amount
        vertex.co = inverse @ world
        moved += 1
        maximum = max(maximum, abs(amount))
    obj.data.update()
    obj["aevrynd_face_revision"] = "v249r203"
    return {"verticesMoved": moved, "maximumMoveMm": maximum * 1000.0}


def synchronize_layers():
    result = {}
    for side in ("L", "R"):
        lash = bpy.data.objects[f"Eye_{side}_UpperLashes"]
        result[lash.name] = move_accessory(lash, 0.00100, 1.6096, 0.0042)
        tear = bpy.data.objects[f"Eye_{side}_TearMeniscus"]
        result[tear.name] = move_accessory(tear, -0.00038, 1.5995, 0.0040)
        caruncle = bpy.data.objects[f"Eye_{side}_Caruncle"]
        result[caruncle.name] = move_accessory(caruncle, -0.00008, 1.6050, 0.0060)
    return result


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
key, previous = consolidate(body, "Aevrynd_NaturalEyeAperture_R203")
metrics = open_body(key)
metrics["shapeKey"] = key.name
metrics["consolidatedShapeKeys"] = previous
metrics["synchronizedLayers"] = synchronize_layers()
body.data.update()
body["aevrynd_face_revision"] = "v249r203"
body["aevrynd_eye_aperture"] = "r202 c-open selected; synchronized upper lashes, tear menisci and caruncles"
body["aevrynd_face_layers"] = ["philtrum.consolidated", "eyelid.anatomical.r183", "mouth.placement.r200", "eye.aperture.r203"]
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_face_revision"] = "v249r203"
scene["aevrynd_mainline_revision"] = "natural-eye-aperture-r203"
scene["aevrynd_release_state"] = "R203_COLLISION_AND_VISUAL_REVIEW_PENDING"
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "selectedSweepVariant": "r202 c-open",
    "strength": STRENGTH,
    "metrics": metrics,
    "status": "COLLISION_AND_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249R203_NATURAL_EYE_APERTURE=" + json.dumps(report, sort_keys=True))
