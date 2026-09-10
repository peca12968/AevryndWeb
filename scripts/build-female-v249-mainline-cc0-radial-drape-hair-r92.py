import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-root-density-r90.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-radial-drape-hair-r92.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-cc0-radial-drape-hair-r92"
MAIN = "AevryndFemaleCC0LongHairFitMain_v249r86"
FLY = "AevryndFemaleCC0LongHairFitFlyaway_v249r86"


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def noise(index):
    value = math.sin(index * 12.9898 + 78.233) * 43758.5453
    return (value - math.floor(value)) * 2.0 - 1.0


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def reshape(obj, flyaway=False):
    tip_deltas = []
    for curve_index, curve in enumerate(obj.data.curves):
        first = curve.first_point_index
        root = obj.data.points[first].position.copy()
        tip = obj.data.points[first + curve.points_length - 1].position.copy()
        front_center = root.y < -0.055 and abs(root.x) < 0.085
        radial = Vector((root.x, root.y, 0.0))
        if radial.length_squared < 1.0e-8:
            radial = Vector((tip.x, tip.y, 0.0))
        if radial.length_squared < 1.0e-8:
            radial = Vector((1.0, 0.0, 0.0))
        radial.normalize()
        random_value = noise(curve_index)
        factor = (1.08 + 0.05 * random_value) if front_center else (1.45 + 0.22 * random_value)
        outward = 0.006 if front_center else (0.038 + 0.010 * noise(curve_index + 17003))
        if flyaway:
            factor = 1.22 + 0.16 * random_value
            outward = 0.012 + 0.010 * noise(curve_index + 4009)
        before_z = tip.z
        for local_index in range(1, curve.points_length):
            point = obj.data.points[first + local_index]
            t = local_index / max(1, curve.points_length - 1)
            blend = smoothstep((t - 0.10) / 0.90)
            relative = point.position - root
            point.position.z = root.z + relative.z * (1.0 + (factor - 1.0) * blend)
            point.position += radial * outward * blend * blend
        after_z = obj.data.points[first + curve.points_length - 1].position.z
        tip_deltas.append(after_z - before_z)
    radius = obj.data.attributes.get("radius")
    if radius:
        for curve in obj.data.curves:
            for local_index in range(curve.points_length):
                t = local_index / max(1, curve.points_length - 1)
                if t > 0.70:
                    index = curve.first_point_index + local_index
                    radius.data[index].value *= max(0.16, (1.0 - t) / 0.30)
    obj.data.update_tag()
    return {
        "curves": len(tip_deltas),
        "averageTipDeltaM": sum(tip_deltas) / len(tip_deltas),
        "minimumTipDeltaM": min(tip_deltas),
        "maximumTipDeltaM": max(tip_deltas),
    }


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
records = {
    MAIN: reshape(bpy.data.objects[MAIN]),
    FLY: reshape(bpy.data.objects[FLY], True),
}
for name in (MAIN, FLY):
    obj = bpy.data.objects[name]
    obj["aevrynd_revision"] = "v249-mainline-cc0-radial-drape-hair-r92"
    obj["aevrynd_layer"] = "hair.cc0-baked.main" if name == MAIN else "hair.cc0-baked.flyaway"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "cc0-radial-drape-hair-r92"
scene["aevrynd_release_state"] = "R92_STATIC_COLLISION_AND_STRICT_VISUAL_REVIEW_REQUIRED"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
for args in (
    ("01-front", (0.0, -2.15, 1.55), (0.0, 0.0, 1.55), 82),
    ("02-three-quarter", (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82),
    ("03-profile", (2.15, 0.0, 1.57), (0.0, 0.0, 1.55), 86),
    ("04-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82),
    ("05-top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78),
    ("06-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
):
    render(camera, *args)

report = {"source": str(SOURCE), "output": str(OUTPUT), "reshape": records,
          "status": "STATIC_COLLISION_AND_STRICT_VISUAL_REVIEW_REQUIRED"}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_CC0_RADIAL_DRAPE_R92=" + json.dumps(report, sort_keys=True))
