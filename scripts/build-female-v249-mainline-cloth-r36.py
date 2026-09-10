import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cloth-r35.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cloth-r36.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-cloth-r36"
OUT.mkdir(parents=True, exist_ok=True)


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def outward_wrinkles(obj, kind):
    maximum = 0.0
    moved = 0
    for vertex in obj.data.vertices:
        x, y, z = vertex.co
        ax = abs(x)
        if kind == "top":
            side_mask = gaussian(ax, 0.138, 0.027) * gaussian(z, 1.246, 0.052)
            underbust_mask = gaussian(ax, 0.082, 0.034) * gaussian(z, 1.205, 0.026) * gaussian(y, -0.115, 0.045)
            mask = max(side_mask, underbust_mask)
            phase = math.sin(z * 168.0 + ax * 41.0) * 0.62 + math.sin(z * 83.0 - ax * 67.0) * 0.38
            limit = 0.00105
        else:
            hip_mask = gaussian(ax, 0.185, 0.040) * gaussian(z, 0.982, 0.075)
            thigh_mask = gaussian(ax, 0.155, 0.050) * gaussian(z, 0.815, 0.030) * gaussian(y, -0.055, 0.080)
            mask = max(hip_mask, thigh_mask)
            phase = math.sin(z * 118.0 + ax * 54.0) * 0.58 + math.sin(z * 61.0 - ax * 91.0) * 0.42
            limit = 0.00085
        if mask < 0.025:
            continue
        # Every displacement is outward. The troughs retain the source surface,
        # so the wrinkle pass cannot create new body penetration by construction.
        amount = limit * mask * (0.12 + 0.88 * (0.5 + 0.5 * phase))
        vertex.co += vertex.normal.normalized() * amount
        moved += 1
        maximum = max(maximum, amount)
    obj.data.update()
    obj["aevrynd_cloth_shape_revision"] = "v249-mainline-cloth-r36"
    obj["aevrynd_wrinkle_constraint"] = "outward-only normal displacement"
    return {"vertices_moved": moved, "maximum_displacement_mm": maximum * 1000.0}


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
reports = {
    "top": outward_wrinkles(bpy.data.objects["Clothing_Bandeau_v160"], "top"),
    "shorts": outward_wrinkles(bpy.data.objects["Clothing_BodyFitShorts_v135"], "shorts"),
}
scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_clothing_candidate"] = "v249-mainline-cloth-r36"
scene["aevrynd_release_state"] = "CLOTH_TENSION_WRINKLES_PENDING_STRICT_VISUAL_AND_COLLISION_REVIEW"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("01-full-front", 1, (0.0, -4.0, 0.90), (0.0, 0.0, 0.86), 70, (900, 1200)),
    ("02-full-three-quarter", 1, (2.35, -3.30, 0.95), (0.0, 0.0, 0.86), 70, (900, 1200)),
    ("03-torso-front", 1, (0.0, -1.55, 1.16), (0.0, 0.0, 1.12), 78, (1000, 1000)),
    ("04-torso-three-quarter", 1, (0.92, -1.34, 1.17), (0.0, 0.0, 1.12), 78, (1000, 1000)),
    ("05-pose-front", 20, (0.0, -3.7, 0.98), (0.0, 0.0, 0.90), 70, (900, 1200)),
)
for name, frame, location, target, lens, resolution in views:
    scene.frame_set(frame)
    scene.render.resolution_x, scene.render.resolution_y = resolution
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)

report = {"source": str(SOURCE), "output": str(OUTPUT), "geometry": reports, "status": "STRICT_VISUAL_REVIEW_REQUIRED"}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_MAINLINE_CLOTH_R36=" + json.dumps(report, sort_keys=True))
