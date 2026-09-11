import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-smoothed-long-hair-r231.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-smoothed-long-hair-r231.build-report.json"
MAIN = "AevryndFemaleCC0LongHairStudyMain_v249r85"
STRENGTH = 0.85
PASSES = 2


def smooth_curves(obj):
    data = obj.data
    original = [point.position.copy() for point in data.points]
    positions = [point.copy() for point in original]
    for _ in range(PASSES):
        updated = [point.copy() for point in positions]
        for curve in data.curves:
            start = curve.first_point_index
            end = start + curve.points_length
            for index in range(start + 1, end - 1):
                laplacian = (positions[index - 1] + positions[index + 1]) * 0.5
                updated[index] = positions[index].lerp(laplacian, STRENGTH)
        positions = updated
    maximum = 0.0
    total = 0.0
    changed = 0
    for index, point in enumerate(data.points):
        delta = (positions[index] - original[index]).length
        point.position = positions[index]
        if delta > 1e-8:
            changed += 1
            maximum = max(maximum, delta)
            total += delta
    data.update_tag()
    return {
        "curves": len(data.curves),
        "points": len(data.points),
        "changedPoints": changed,
        "strength": STRENGTH,
        "passes": PASSES,
        "maximumDeltaMm": maximum * 1000.0,
        "meanChangedDeltaMm": total / changed * 1000.0,
        "rootAndTipPositionsPreserved": True,
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.scene.frame_set(1)
main = bpy.data.objects[MAIN]
metrics = smooth_curves(main)
main["aevrynd_revision"] = "v249r231-smoothed-long-hair"
main["aevrynd_parent_revision"] = "v249r210"
main["aevrynd_smoothing_strength"] = STRENGTH
main["aevrynd_smoothing_passes"] = PASSES
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "geometry": metrics,
    "status": "STATIC_COLLISION_AND_RUNTIME_REBUILD_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R231_SMOOTHED_LONG_HAIR=" + json.dumps(report, sort_keys=True))
