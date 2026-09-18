"""Turn only the 234 baked r1068 support vertices inward."""
import json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-exact-edge-support-r1068-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-support-band-turn-r1069-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1069-support-band-turn.study.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1069-support-band-turn"
BODY = "AevryndFemaleCC0ExactEdgeSupport_R1068"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
ORIGINAL_VERTEX_COUNT = 13583
VARIANTS = (("a-control", 0.0), ("b-0.05mm", 0.00005), ("c-0.10mm", 0.00010), ("d-0.20mm", 0.00020), ("e-0.35mm", 0.00035))
SELECTED = "c-0.10mm"

def apply_turn(body, depth):
    indices = range(ORIGINAL_VERTEX_COUNT, len(body.data.vertices))
    local = body.matrix_world.inverted().to_3x3() @ Vector((0.0, depth, 0.0))
    for block in body.data.shape_keys.key_blocks:
        for index in indices:
            block.data[index].co += local
    body.data.update()
    return {"movedVertices": len(body.data.vertices) - ORIGINAL_VERTEX_COUNT, "depthMm": depth * 1000.0, "shapeKeysMovedTogether": len(body.data.shape_keys.key_blocks)}

def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()

def hide_hair(scene):
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")):
                obj.hide_render = True

def render(scene, label, oblique=False):
    camera = scene.camera
    camera.data.lens = 135
    camera.location = ((-0.105 if oblique else 0.0), -0.43, 1.391)
    look_at(camera, (0.0, -0.115, 1.386))
    scene.render.resolution_x, scene.render.resolution_y = 1100, 720
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)

OUT.mkdir(parents=True, exist_ok=True)
results = []
for label, depth in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    body = bpy.data.objects[BODY]
    body.name = "AevryndFemaleCC0SupportBandTurn_R1069"
    hide_hair(scene)
    metrics = apply_turn(body, depth)
    keys = body.data.shape_keys.key_blocks
    keys[OPEN_KEY].value = keys[SMILE_KEY].value = 0.0
    renders = [render(scene, f"{label}-neutral-front"), render(scene, f"{label}-neutral-oblique", True)]
    keys[OPEN_KEY].value = 1.0
    renders.append(render(scene, f"{label}-open"))
    keys[OPEN_KEY].value = 0.0
    result = {"label": label, "metrics": metrics, "renders": renders}
    results.append(result)
    if label == SELECTED:
        body["aevrynd_revision"] = "v249r1069-support-band-turn"
        body["aevrynd_source"] = SOURCE.name
        body["aevrynd_support_band_depth_mm"] = depth * 1000.0
        scene["aevrynd_release_state"] = "VISUAL_AND_COLLISION_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {"revision": "v249r1069-support-band-turn", "source": str(SOURCE), "output": str(OUTPUT), "method": "translate only the 234 baked r1068 support-band vertices inward across all 35 shape keys", "variants": results, "selectedVariant": SELECTED, "topologyChanged": False, "websitePromotionApproved": False, "candidateStatus": "VISUAL_AND_COLLISION_REVIEW_PENDING"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1069_SUPPORT_TURN=" + json.dumps({"selected": SELECTED, "variants": [item["metrics"] for item in results]}, sort_keys=True))
