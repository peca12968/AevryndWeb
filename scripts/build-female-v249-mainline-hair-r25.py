import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-eyelid-r23.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-r25.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-hair-r25"
OUT.mkdir(parents=True, exist_ok=True)
MAIN = "AevryndFemaleGuideBob_v249r12"
PART = "AevryndFemaleScalpPart_v249r16"
POINTS = 20
TEMPLE_CURVES = range(300, 350)


def clamp(value, lo=0.0, hi=1.0):
    return max(lo, min(hi, value))


def smooth(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def trim_scalp_part(part):
    old_mesh = part.data
    keep_faces = [polygon for polygon in old_mesh.polygons if polygon.index >= 4]
    used = sorted({index for polygon in keep_faces for index in polygon.vertices})
    remap = {old: new for new, old in enumerate(used)}
    vertices = [old_mesh.vertices[index].co.copy() for index in used]
    faces = [[remap[index] for index in polygon.vertices] for polygon in keep_faces]
    material_indices = [polygon.material_index for polygon in keep_faces]

    mesh = bpy.data.meshes.new("AevryndFemaleScalpPartData_v249r25")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for material in old_mesh.materials:
        mesh.materials.append(material)
    for polygon, material_index in zip(mesh.polygons, material_indices):
        polygon.material_index = material_index
    part.data = mesh
    part.name = "AevryndFemaleScalpPart_v249r25"
    part["aevrynd_candidate"] = "v249-mainline-hair-r25"
    part["aevrynd_removed_anterior_faces"] = 4
    return {
        "removed_faces": 4,
        "vertices_before": len(old_mesh.vertices),
        "vertices_after": len(mesh.vertices),
        "faces_before": len(old_mesh.polygons),
        "faces_after": len(mesh.polygons),
        "front_z_min": min(vertex.co.z for vertex in mesh.vertices),
    }


def tuck_light_temple(hair):
    data = hair.data
    radius = data.attributes.get("radius")
    maximum = 0.0
    for curve_index in TEMPLE_CURVES:
        follow_index = curve_index % 25
        phase = math.sin((follow_index + 1) * 1.731 + (curve_index // 25) * 0.63)
        for point_index in range(1, POINTS):
            index = curve_index * POINTS + point_index
            point = data.points[index]
            original = point.position.copy()
            t = point_index / (POINTS - 1)
            tuck = smooth((t - 0.04) / 0.48)
            settle = smooth((t - 0.62) / 0.38)
            point.position.x -= (0.0105 + 0.0018 * phase) * tuck * (1.0 - 0.30 * settle)
            point.position.y += (0.045 + 0.004 * phase) * tuck
            point.position.z += 0.0030 * phase * tuck * (1.0 - settle)
            maximum = max(maximum, (point.position - original).length)
            if radius:
                radius.data[index].value *= 0.58 + 0.08 * ((follow_index % 5) / 4.0)
    data.update_tag()
    hair.name = "AevryndFemaleGuideBob_v249r25"
    hair.data.name = "AevryndFemaleGuideBobData_v249r25"
    hair["aevrynd_candidate"] = "v249-mainline-hair-r25"
    hair["aevrynd_light_temple_tuck"] = "guides 12-13, 50 curves, root locked"
    return {
        "curves": len(TEMPLE_CURVES),
        "points_changed": len(TEMPLE_CURVES) * (POINTS - 1),
        "max_displacement_mm": maximum * 1000.0,
        "root_radius_scale": [0.58, 0.66],
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
part_report = trim_scalp_part(bpy.data.objects[PART])
hair_report = tuck_light_temple(bpy.data.objects[MAIN])
scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_hair_candidate"] = "v249-mainline-hair-r25"
scene["aevrynd_release_state"] = "MAINLINE_GROOM_VISUAL_AND_COLLISION_AUDIT_REQUIRED"

camera = bpy.data.objects.get("Camera") or next(obj for obj in bpy.data.objects if obj.type == "CAMERA")
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
views = (
    ("01-front", (0.0, -2.15, 1.55), (0.0, 0.0, 1.55), 82, (900, 900)),
    ("02-three-quarter", (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82, (900, 900)),
    ("03-profile", (2.15, 0.0, 1.57), (0.0, 0.0, 1.55), 86, (900, 900)),
    ("04-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82, (900, 900)),
    ("05-top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78, (900, 900)),
    ("06-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000)),
)
for name, location, target, lens, resolution in views:
    scene.frame_set(1)
    scene.render.resolution_x, scene.render.resolution_y = resolution
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)

report = {"source": str(SOURCE), "output": str(OUTPUT), "scalp_part": part_report, "temple_tuck": hair_report}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_MAINLINE_HAIR_R25=" + json.dumps(report, sort_keys=True))
