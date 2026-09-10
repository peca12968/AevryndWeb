import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cornea-response-r175.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-soft-clearance-lids-r182.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-soft-clearance-lids-r182.build-report.json"
FACTOR = 0.72


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def sculpt(key, normals):
    moved = 0
    maximum = 0.0
    for point, normal in zip(key.data, normals):
        p = point.co.copy()
        if p.y > -0.096 or not (1.580 < p.z < 1.632):
            continue
        delta = Vector((0.0, 0.0, 0.0))
        for cx in (-0.035, 0.035):
            u = (p.x - cx) / 0.034
            if abs(u) >= 1.12:
                continue
            horizontal = max(0.0, 1.0 - (u / 1.12) ** 2) ** 1.65
            front = gaussian(p.y, -0.126, 0.022)
            arch = max(0.0, 1.0 - u * u)
            upper_center = 1.6078 + 0.0042 * arch
            lower_center = 1.5994 - 0.0015 * arch
            crease_center = upper_center + 0.0084
            upper = horizontal * front * gaussian(p.z, upper_center, 0.0025)
            lower = horizontal * front * gaussian(p.z, lower_center, 0.0027)
            crease = horizontal * front * gaussian(p.z, crease_center, 0.0026)
            trough = horizontal * front * gaussian(p.z, lower_center - 0.0085, 0.0035)
            delta += normal * FACTOR * (0.00058 * upper + 0.00034 * lower - 0.00050 * crease - 0.00016 * trough)
            outer_axis = u * (1.0 if cx > 0.0 else -1.0)
            tilt = 0.00052 * outer_axis * horizontal * front
            delta.z += FACTOR * tilt * (upper + lower)
            delta.z -= FACTOR * 0.00018 * upper * arch
        if delta.length > 1e-7:
            point.co += delta
            moved += 1
            maximum = max(maximum, delta.length)
    return {"verticesMoved": moved, "maxMoveMm": maximum * 1000.0}




def adjust_eye_clearance():
    shifted = {}
    for side in ("L", "R"):
        for part in ("Cornea", "Iris", "Pupil", "Sclera"):
            obj = bpy.data.objects[f"Eye_{side}_{part}"]
            obj.data = obj.data.copy()
            for vertex in obj.data.vertices:
                vertex.co.y += 0.00100
            obj.data.update()
            shifted[obj.name] = 1.00
        lashes = bpy.data.objects[f"Eye_{side}_UpperLashes"]
        lashes.data = lashes.data.copy()
        for vertex in lashes.data.vertices:
            vertex.co.y -= 0.00055
        lashes.data.update()
        shifted[lashes.name] = -0.55
    return shifted

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects["AevryndFemaleBodyBaseV118"]
key = body.shape_key_add(name="Aevrynd_EvaluatedAnatomicalLids_R182", from_mix=True)
consolidated = [old.name for old in body.data.shape_keys.key_blocks[1:-1]]
for old in body.data.shape_keys.key_blocks[1:-1]:
    old.value = 0.0
key.value = 1.0
body.data.update()
normals = [vertex.normal.copy() for vertex in body.data.vertices]
metrics = sculpt(key, normals)
eye_shifts = adjust_eye_clearance()
body.data.update()
body["aevrynd_face_revision"] = "v249r182"
body["aevrynd_face_layers"] = ["philtrum.consolidated", "eye_aperture.consolidated", "eyelid.anatomical.r180"]
body["aevrynd_eyelid_method"] = "sculpted on evaluated shape-key mix; upper/lower roll, crease, trough and outer canthus"
scene["aevrynd_face_revision"] = "v249r182"
scene["aevrynd_candidate_status"] = "COLLISION_AND_VISUAL_REVIEW_PENDING"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "shapeKey": key.name,
    "consolidatedShapeKeys": consolidated, "factor": FACTOR, "eyeClearanceShiftMm": eye_shifts, **metrics,
    "status": "COLLISION_AND_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R182_EVALUATED_LIDS=" + json.dumps(report, sort_keys=True))
