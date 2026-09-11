import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-hairline-layer-isolation-r347.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r347-hairline-layer-isolation"
FLY = "AevryndFemaleFlyaways_R264"; CARDS = "AevryndFemaleHairlineTransitionCards_R285"; SCALP = "AevryndFemaleScalpUnderlayer_R280"
VARIANTS = (("a-current", True, True, True), ("b-no-flyaways", False, True, True), ("c-no-transition-cards", True, False, True), ("d-no-flyaways-or-cards", False, False, True))

def look_at(obj, target): obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); scene = bpy.context.scene; scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"; scene.render.resolution_percentage = 100; scene.render.image_settings.file_format = "PNG"; scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True); camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (("face", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92), ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.02, 1.605), 90), ("hairline-high", (0.0, -0.57, 1.76), (0.0, -0.02, 1.64), 92))
metrics = {}
for label, fly, cards, scalp in VARIANTS:
    bpy.data.objects[FLY].hide_render = not fly; bpy.data.objects[CARDS].hide_render = not cards; bpy.data.objects[SCALP].hide_render = not scalp
    for view_name, location, target, lens in views:
        camera.location = location; camera.data.lens = lens; look_at(camera, target); scene.render.resolution_x = scene.render.resolution_y = 1000
        scene.render.filepath = str(RENDER_DIR / f"{label}-{view_name}.png"); bpy.ops.render.render(write_still=True)
    metrics[label] = {"flyawaysVisible": fly, "transitionCardsVisible": cards, "scalpUnderlayerVisible": scalp}
report = {"source": str(SOURCE), "renderDirectory": str(RENDER_DIR), "variants": metrics, "method": "Render-isolate the three hairline support layers under fixed camera and lighting to identify forehead guide lines and the pale part seam.", "status": "VISUAL_REVIEW_PENDING"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8"); print("AEVRYND_R347_HAIRLINE_ISOLATION=" + json.dumps(report, sort_keys=True))
