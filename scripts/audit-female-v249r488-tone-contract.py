import json
import os
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
BASE_BLEND = Path(os.environ.get("AEVRYND_TONE_BASE_BLEND", ASSETS / "aevrynd-female-authoring-v249-mainline-balanced-lower-lip-r485.blend"))
CAND_BLEND = Path(os.environ.get("AEVRYND_TONE_CAND_BLEND", ASSETS / "aevrynd-female-authoring-v249-mainline-owned-lip-normal-r488.blend"))
BASE_IMAGE = Path(os.environ.get("AEVRYND_TONE_BASE_IMAGE", ASSETS / "reviews/v249r488-lip-normal-sweep/s0.00-face-f01.png"))
CAND_IMAGE = Path(os.environ.get("AEVRYND_TONE_CAND_IMAGE", ASSETS / "reviews/v249r488-lip-normal-sweep/s0.35-face-f01.png"))
REPORT = Path(os.environ.get("AEVRYND_TONE_REPORT", ASSETS / "female-v249-mainline-owned-lip-normal-r488.tone-contract-audit.json"))
BODY = "AevryndFemaleBodyBaseV118"


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    material = bpy.data.objects[BODY].active_material
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    base = shader.inputs["Base Color"]
    return {
        "file": path.name,
        "viewTransform": scene.view_settings.view_transform,
        "look": scene.view_settings.look,
        "exposure": scene.view_settings.exposure,
        "gamma": scene.view_settings.gamma,
        "baseColorLinked": base.is_linked,
        "baseColorSourceNode": base.links[0].from_node.name if base.is_linked else None,
        "baseColorSourceSocket": base.links[0].from_socket.name if base.is_linked else None,
        "baseColorDefault": [float(value) for value in base.default_value],
    }


def luminance(path, rectangle):
    image = bpy.data.images.load(str(path), check_existing=False)
    width, height = image.size
    pixels = image.pixels[:]
    x0, y0, x1, y1 = [
        int(value * (width if index % 2 == 0 else height))
        for index, value in enumerate(rectangle)
    ]
    total = 0.0
    count = 0
    for y in range(y0, y1):
        for x in range(x0, x1):
            offset = (y * width + x) * 4
            total += 0.2126 * pixels[offset] + 0.7152 * pixels[offset + 1] + 0.0722 * pixels[offset + 2]
            count += 1
    bpy.data.images.remove(image)
    return total / count


base = snapshot(BASE_BLEND)
candidate = snapshot(CAND_BLEND)
locked = (
    "viewTransform",
    "look",
    "exposure",
    "gamma",
    "baseColorLinked",
    "baseColorSourceNode",
    "baseColorSourceSocket",
    "baseColorDefault",
)
violations = []
for field in locked:
    if base[field] != candidate[field]:
        violations.append({
            "type": "lockedToneSettingChanged",
            "field": field,
            "baseline": base[field],
            "candidate": candidate[field],
        })

rectangles = {
    "leftCheek": (0.13, 0.28, 0.31, 0.54),
    "rightCheek": (0.69, 0.28, 0.87, 0.54),
    "forehead": (0.42, 0.77, 0.58, 0.90),
    "wholeFace": (0.08, 0.02, 0.92, 0.92),
}
regions = {}
for name, rectangle in rectangles.items():
    before = luminance(BASE_IMAGE, rectangle)
    after = luminance(CAND_IMAGE, rectangle)
    delta = (after - before) * 100.0 / before if before else 0.0
    regions[name] = {"baseline": before, "candidate": after, "deltaPercent": delta}
    if abs(delta) > 1.0:
        violations.append({"type": "luminanceDriftOver1Percent", "region": name, "deltaPercent": delta})

report = {
    "baseline": base,
    "candidate": candidate,
    "linearLuminanceRegions": regions,
    "violations": violations,
    "status": "PASS" if not violations else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R488_TONE=" + json.dumps({"status": report["status"], "regions": regions, "violations": violations}, sort_keys=True))
