import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r38.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r45.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-hair-r45"
OUT.mkdir(parents=True, exist_ok=True)
MAIN = "AevryndFemaleGuideBob_v249r25"
POINTS = 20


def smoothstep(edge0, edge1, value):
    t = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def decorrelate_followers(obj):
    data = obj.data
    radius = data.attributes.get("radius")
    maximum = 0.0
    moved = 0
    for curve_index in range(len(data.curves)):
        start = curve_index * POINTS
        root = data.points[start].position.copy()
        tip = data.points[start + POINTS - 1].position.copy()
        tangent = tip - root
        if tangent.length < 1e-8:
            continue
        tangent.normalize()
        side = tangent.cross(Vector((0.0, 0.0, 1.0)))
        if side.length < 1e-5:
            side = tangent.cross(Vector((1.0, 0.0, 0.0)))
        side.normalize()
        normal = tangent.cross(side).normalized()
        phase = (curve_index * 2.399963229728653) % (2.0 * math.pi)
        phase2 = (curve_index * 1.324717957244746) % (2.0 * math.pi)
        amplitude = 0.00035 + 0.00065 * (0.5 + 0.5 * math.sin(curve_index * 0.754877666))
        secondary = 0.00022 + 0.00040 * (0.5 + 0.5 * math.sin(curve_index * 1.220744085))
        for point_index in range(2, POINTS - 1):
            index = start + point_index
            t = point_index / (POINTS - 1)
            envelope = smoothstep(0.08, 0.22, t) * smoothstep(1.0, 0.78, t)
            wave_a = math.sin(phase + t * math.pi * 2.35)
            wave_b = math.sin(phase2 + t * math.pi * 3.10)
            delta = side * (amplitude * envelope * wave_a) + normal * (secondary * envelope * wave_b)
            data.points[index].position += delta
            maximum = max(maximum, delta.length)
            moved += 1
            if radius:
                radius.data[index].value *= 0.88 + 0.16 * (0.5 + 0.5 * math.sin(phase2 + t * 4.0))
    data.update_tag()
    obj.name = "AevryndFemaleGuideBob_v249r45"
    obj.data.name = "AevryndFemaleGuideBobData_v249r45"
    obj["aevrynd_candidate"] = "v249-mainline-hair-r45"
    obj["aevrynd_microvariation"] = "root-tip-locked per-strand tangent-frame waves"
    return {"curves": len(data.curves), "points_moved": moved, "maximum_displacement_mm": maximum * 1000.0}


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
report = decorrelate_followers(bpy.data.objects[MAIN])
scene = bpy.context.scene
scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_hair_candidate"] = "v249-mainline-hair-r45"
scene["aevrynd_release_state"] = "HAIR_R45_PENDING_STRICT_VISUAL_AND_COLLISION_REVIEW"
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("01-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000)),
    ("02-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88, (1000, 1000)),
    ("03-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82, (900, 900)),
    ("04-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78, (1000, 1000)),
)
for name, location, target, lens, resolution in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)

payload = {"source": str(SOURCE), "output": str(OUTPUT), "geometry": report}
(OUT / "report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_MAINLINE_HAIR_R45=" + json.dumps(payload, sort_keys=True))
