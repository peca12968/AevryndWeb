import json
import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-long-hair-integration-r185.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-anatomical-hairline-fade-r187.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-anatomical-hairline-fade-r187.build-report.json"
SCALP = "AevryndFemaleDeformMatchedScalp_v249r163"


def clamp01(value):
    return max(0.0, min(1.0, value))


def smoothstep(edge0, edge1, value):
    value = clamp01((value - edge0) / (edge1 - edge0))
    return value * value * (3.0 - 2.0 * value)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scalp = bpy.data.objects[SCALP]
scalp.data = scalp.data.copy()
density = scalp.data.attributes["aevrynd_root_density"]
changed = 0
multipliers = []
for vertex, item in zip(scalp.data.vertices, density.data):
    x, y, z = vertex.co
    frontness = smoothstep(-0.040, -0.105, y)
    lateral = min(1.0, abs(x) / 0.090)
    center_peak = math.exp(-0.5 * (x / 0.027) ** 2)
    threshold = 1.666 - 0.008 * lateral + 0.010 * center_peak
    height_fade = smoothstep(threshold - 0.004, threshold + 0.020, z)
    multiplier = (1.0 - frontness) + frontness * (0.10 + 0.90 * height_fade)
    old = item.value
    item.value = max(0.015, old * multiplier)
    if abs(item.value - old) > 1e-7:
        changed += 1
    multipliers.append(multiplier)
scalp.data.update()
scalp["aevrynd_density_revision"] = "v249r187"
scalp["aevrynd_hairline_method"] = "anatomical height and temple-aware front density fade"

scene = bpy.context.scene
scene["aevrynd_mainline_revision"] = "anatomical-hairline-fade-r187"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_candidate_status"] = "COLLISION_AND_11SHOT_REVIEW_PENDING"
scene["aevrynd_runtime_dependency"] = "none"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "scalp": SCALP,
    "densityAttribute": "aevrynd_root_density",
    "verticesChanged": changed,
    "minimumMultiplier": min(multipliers),
    "averageMultiplier": sum(multipliers) / len(multipliers),
    "runtimeDependency": "none",
    "status": "COLLISION_AND_11SHOT_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R187_HAIRLINE_FADE=" + json.dumps(report, sort_keys=True))
