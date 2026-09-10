import hashlib
import json
import struct
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-hair-material-r129.blend"
CANDIDATE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-anatomical-hairline-fade-r187.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-anatomical-hairline-fade-r187.hair-parity.json"
HAIR = (
    "AevryndFemaleCC0LongHairStudyMain_v249r85",
    "AevryndFemaleCC0LongHairStudyFlyaway_v249r85",
)


def digest_file(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    frames = {}
    for frame in (1, 20):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        objects = {}
        for name in HAIR:
            obj = bpy.data.objects[name].evaluated_get(depsgraph)
            digest = hashlib.sha256()
            for point in obj.data.points:
                world = obj.matrix_world @ point.position
                digest.update(struct.pack("<3d", world.x, world.y, world.z))
            offsets = list(obj.data.curve_offset_data)
            for item in offsets:
                digest.update(struct.pack("<q", int(item.value)))
            objects[name] = {
                "points": len(obj.data.points),
                "curves": len(obj.data.curves),
                "sha256": digest.hexdigest(),
            }
        frames[str(frame)] = objects
    return frames


baseline = digest_file(BASELINE)
candidate = digest_file(CANDIDATE)
mismatches = []
for frame in ("1", "20"):
    for name in HAIR:
        if baseline[frame][name] != candidate[frame][name]:
            mismatches.append({"frame": int(frame), "object": name})
report = {
    "baseline": str(BASELINE),
    "candidate": str(CANDIDATE),
    "objects": list(HAIR),
    "baselineFrames": baseline,
    "candidateFrames": candidate,
    "mismatches": mismatches,
    "status": "PASS" if not mismatches else "FAIL",
}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R187_HAIR_PARITY=" + json.dumps({"output": str(OUTPUT), "mismatches": mismatches, "status": report["status"]}, sort_keys=True))
if mismatches:
    raise SystemExit(2)
