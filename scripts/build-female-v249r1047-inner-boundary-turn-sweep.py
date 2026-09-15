"""Turn only the eight measured pale inner-lip faces inward on r1046."""

import json
from collections import Counter
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-depth-cleanup-r1046-study.blend"
ISOLATION = ASSETS / "female-v249-mainline-r1047-boundary-face-isolation.inspect.json"
REPORT = ASSETS / "female-v249-mainline-r1047-inner-boundary-turn-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "v249r1047-inner-boundary-turn-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
KEY = "Aevrynd_InnerLipBoundaryTurn_R1047"
CENTER_Z = 1.3862
VARIANTS = (("source-r1046", 0.0), ("a-2p5mm", 0.0025), ("b-4mm", 0.0040), ("c-6mm", 0.0060))


def mixed_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    result = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-9:
            continue
        relative = block.relative_key
        for index, coordinate in enumerate(result):
            coordinate += block.value * (block.data[index].co - relative.data[index].co)
    return result


def make_turn_key(body, target_faces, depth):
    if body.data.shape_keys.key_blocks.get(KEY):
        body.shape_key_remove(body.data.shape_keys.key_blocks[KEY])
    key = body.shape_key_add(name=KEY, from_mix=False)
    key.value = 1.0
    key.slider_min, key.slider_max = 0.0, 1.25
    mesh = body.data
    target_use = Counter()
    total_use = Counter()
    for polygon in mesh.polygons:
        for index in polygon.vertices:
            total_use[index] += 1
            if polygon.index in target_faces:
                target_use[index] += 1
    points = mixed_coordinates(body)
    inverse3 = body.matrix_world.inverted().to_3x3()
    movements = []
    for index, uses in target_use.items():
        weight = min(1.0, uses / max(1, total_use[index]) * 2.0)
        point = points[index]
        vertical = point.z - CENTER_Z
        movement = Vector((0.0, depth * weight, -vertical * 0.16 * weight))
        key.data[index].co += inverse3 @ movement
        movements.append((index, weight, movement.length))
    return {
        "targetFaces": sorted(target_faces),
        "movedVertices": len(movements),
        "fullWeightVertices": sum(weight >= 0.999 for _index, weight, _length in movements),
        "maximumDeltaMm": max((length for _index, _weight, length in movements), default=0.0) * 1000.0,
        "minimumWeight": min((weight for _index, weight, _length in movements), default=0.0),
    }


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, label, expression=None):
    body = bpy.data.objects[BODY]
    keys = body.data.shape_keys.key_blocks
    keys["Aevrynd_MouthOpenTest_R1030"].value = 1.0 if expression == "open" else 0.0
    keys["Aevrynd_SmileTest_R1030"].value = 1.0 if expression == "smile" else 0.0
    camera = scene.camera
    camera.location = (0.0, -0.43, 1.388)
    camera.data.lens = 135
    look_at(camera, (0.0, -0.105, 1.386))
    scene.render.resolution_x, scene.render.resolution_y = 1200, 700
    scene.render.resolution_percentage = 100
    path = RENDER_DIR / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    keys["Aevrynd_MouthOpenTest_R1030"].value = 0.0
    keys["Aevrynd_SmileTest_R1030"].value = 0.0
    return str(path)


isolation = json.loads(ISOLATION.read_text(encoding="utf-8"))
target_faces = {
    item["face"] for item in isolation["faces"]
    if item["group"] == "mid" and item["center"][2] > 1.38
}
if len(target_faces) != 8:
    raise RuntimeError(f"Expected eight isolated bright-strip faces, got {len(target_faces)}")

RENDER_DIR.mkdir(parents=True, exist_ok=True)
variants = []
for label, depth in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    body = bpy.data.objects[BODY]
    edit = make_turn_key(body, target_faces, depth)
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")):
                obj.hide_render = True
    renders = [
        render(scene, f"{label}-neutral"),
        render(scene, f"{label}-mouth-open", "open"),
        render(scene, f"{label}-smile", "smile"),
    ]
    variants.append({"label": label, "depthM": depth, "edit": edit, "renders": renders, "status": "VISUAL_DIAGNOSTIC"})

report = {
    "revision": "v249r1047-inner-boundary-turn-sweep",
    "source": str(SOURCE),
    "isolationEvidence": str(ISOLATION),
    "method": "topology-weighted inward turn of only eight measured pale inner-lip faces; outer lower lip and side shell excluded",
    "variants": variants,
    "websitePromotionApproved": False,
    "status": "PENDING_STRICT_VISUAL_SELECTION_AND_COLLISION_GATE",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1047_INNER_TURN=" + json.dumps({"targetFaces": len(target_faces), "variants": len(variants)}, sort_keys=True))
