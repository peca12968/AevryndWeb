import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-recessed-natural-eyes-r301.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r303-upper-eyelid-layer-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-upper-eyelid-layer-r303.study.json"
BODY = "AevryndFemaleBody_CC0_R249"
RIG = "AevryndFemaleRig"
EYES = {"L": (0.034528, 1.607765, 1.0), "R": (-0.034443, 1.607765, -1.0)}
VARIANTS = (
    ("a-current", None),
    ("b-open", 0.0027),
    ("c-natural", 0.0017),
    ("d-relaxed", 0.0008),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def make_lid(side, aperture_height, material, rig):
    cx, cz, anatomical_sign = EYES[side]
    count = 31
    vertices = []
    for row in range(2):
        for index in range(count):
            u = -0.98 + 1.96 * index / (count - 1)
            edge = math.sqrt(max(0.0, 1.0 - u * u))
            outer = anatomical_sign * u
            inner_z = cz + aperture_height * edge - 0.00032 * outer * edge
            if row == 0:
                z = inner_z
                y = -0.14058 - 0.00016 * edge
            else:
                z = inner_z + 0.0049 * edge + 0.00045
                y = -0.14015 - 0.00135 * edge
            vertices.append((cx + 0.01035 * u, y, z))
    faces = []
    for index in range(count - 1):
        faces.append((index, index + 1, count + index + 1, count + index))
    mesh = bpy.data.meshes.new(f"AevryndEye_{side}_UpperLidSurface_R303Geometry")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(f"AevryndEye_{side}_UpperLidSurface_R303", mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world
    obj["aevrynd_layer"] = f"eye.{side.lower()}.upper_lid_surface"
    obj["aevrynd_binding"] = "rig.head"
    obj["aevrynd_revision"] = "v249r303-study"
    return obj


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
OUT.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
body = bpy.data.objects[BODY]
skin_material = body.data.materials[0]
rig = bpy.data.objects[RIG]
metrics = {}
created = []
for name, aperture_height in VARIANTS:
    for obj in created:
        bpy.data.objects.remove(obj, do_unlink=True)
    created = []
    if aperture_height is not None:
        created = [make_lid(side, aperture_height, skin_material, rig) for side in EYES]
    scene.frame_set(1)
    bpy.context.view_layer.update()
    camera.location = (0.0, -0.68, 1.605)
    camera.data.lens = 92
    look_at(camera, (0.0, -0.035, 1.606))
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.filepath = str(OUT / f"{name}-face-close.png")
    bpy.ops.render.render(write_still=True)
    camera.location = (0.45, -0.62, 1.62)
    camera.data.lens = 90
    look_at(camera, (0.0, -0.02, 1.605))
    scene.render.filepath = str(OUT / f"{name}-three-quarter.png")
    bpy.ops.render.render(write_still=True)
    metrics[name] = {"apertureHeightM": aperture_height, "surfaceVerticesPerEye": 62 if aperture_height is not None else 0, "surfaceFacesPerEye": 30 if aperture_height is not None else 0}

report = {"source": str(SOURCE), "renderDirectory": str(OUT), "variants": metrics, "status": "STRICT_VISUAL_SELECTION_REQUIRED"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R303_UPPER_LID_SWEEP=" + json.dumps(report, sort_keys=True))
