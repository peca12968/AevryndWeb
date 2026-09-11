import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-physical-hair-r244.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-back-seam-closure-r246.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-back-seam-closure-r246.build-report.json"
TARGET_LAYERS = ("hair.main", "hair.overlay")
SHIFT = 0.005


def smoothstep(edge0, edge1, value):
    value = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return value * value * (3.0 - 2.0 * value)


def target_objects():
    return [
        obj for obj in bpy.context.scene.objects
        if obj.type == "CURVES" and any(str(obj.get("aevrynd_layer", "")).startswith(prefix) for prefix in TARGET_LAYERS)
    ]


def close_back_seam(objects):
    per_object = {}
    for obj in objects:
        inverse_vector = obj.matrix_world.inverted().to_3x3()
        moved = 0
        maximum = 0.0
        for curve in obj.data.curves:
            for local_index in range(1, curve.points_length):
                index = curve.first_point_index + local_index
                point = obj.data.points[index]
                world = obj.matrix_world @ point.position
                if world.y <= 0.0 or abs(world.x) >= 0.075:
                    continue
                t = local_index / max(1, curve.points_length - 1)
                backness = smoothstep(0.0, 0.080, world.y)
                root_release = smoothstep(0.12, 0.58, t)
                center = 1.0 - smoothstep(0.025, 0.075, abs(world.x))
                weight = backness * root_release * (0.35 + 0.65 * center)
                direction = -1.0 if world.x > 0.0 else 1.0
                delta = Vector((direction * SHIFT * weight, 0.0, 0.0))
                point.position += inverse_vector @ delta
                if delta.length > 1e-8:
                    moved += 1
                    maximum = max(maximum, delta.length)
        obj.data.update_tag()
        obj["aevrynd_revision"] = "v249r246-back-seam-closure"
        obj["aevrynd_back_seam_shift_m"] = SHIFT
        per_object[obj.name] = {"pointsMoved": moved, "maximumMoveMm": maximum * 1000.0}
    return per_object


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
movement = close_back_seam(target_objects())
scene["aevrynd_mainline_revision"] = "v249r246-back-seam-closure"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "FULL_COLLISION_AND_DYNAMIC_REBUILD_PENDING"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "selectedSweepVariant": "r245 b-close-5mm",
    "shiftM": SHIFT,
    "movement": movement,
    "status": "FULL_COLLISION_AND_DYNAMIC_REBUILD_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R246_BACK_SEAM_CLOSURE=" + json.dumps(report, sort_keys=True))
