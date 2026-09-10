import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-dual-layer-root-flow-r150.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r150-root-flow-radius-r151-sweep"
ROOT_FLOW = "AevryndFemaleOwnedHairRootFlow_v249r150"
VARIANTS = (30, 45, 60)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def set_radius(obj, root_microns, tip_microns=2):
    radius = obj.data.attributes["radius"]
    for curve in obj.data.curves:
        for local_index in range(curve.points_length):
            t = local_index / max(1, curve.points_length - 1)
            radius.data[curve.first_point_index + local_index].value = (root_microns * (1.0 - t) + tip_microns * t) * 1e-6


def render(camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
root_flow = bpy.data.objects[ROOT_FLOW]
for obj in bpy.data.objects:
    if obj.type == "CURVES":
        obj.visible_shadow = False

report = {"source": str(SOURCE), "rootFlow": ROOT_FLOW, "variants": [], "status": "STRICT_VISUAL_REVIEW_REQUIRED"}
for root_microns in VARIANTS:
    set_radius(root_flow, root_microns)
    prefix = f"root-{root_microns:02d}um"
    render(camera, f"{prefix}-top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78)
    render(camera, f"{prefix}-face", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88)
    report["variants"].append({"rootMicrons": root_microns, "tipMicrons": 2})

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R150_ROOT_FLOW_RADIUS_R151=" + json.dumps(report, sort_keys=True))
