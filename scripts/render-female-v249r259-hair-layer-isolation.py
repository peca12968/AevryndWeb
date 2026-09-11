import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-guide-hair-r259.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-cc0-guide-hair-r259.layer-isolation-report.json"
OUT = ROOT.parent / "Temp/female-realism/v249r259-hair-layer-isolation"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
scalp = bpy.data.objects["AevryndFemaleScalpCoverage_R259"]
hair = bpy.data.objects["AevryndFemaleGuideFollowHair_R259"]
OUT.mkdir(parents=True, exist_ok=True)

scalp.hide_render = False
hair.hide_render = False
render("01-all-front", (0.0, -0.82, 1.62), (0.0, -0.02, 1.60), 88)
scalp.hide_render = True
render("02-hair-only-front", (0.0, -0.82, 1.62), (0.0, -0.02, 1.60), 88)
render("03-hair-only-top", (0.0, -0.25, 2.17), (0.0, 0.01, 1.67), 78)
hair.hide_render = True
scalp.hide_render = False
render("04-scalp-only-front", (0.0, -0.82, 1.62), (0.0, -0.02, 1.60), 88)
render("05-scalp-only-top", (0.0, -0.25, 2.17), (0.0, 0.01, 1.67), 78)

report = {
    "source": str(SOURCE),
    "renders": [str(path) for path in sorted(OUT.glob("*.png"))],
    "status": "DIAGNOSTIC_COMPLETE",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R259_HAIR_LAYER_ISOLATION=" + json.dumps(report, sort_keys=True))
