import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-recessed-natural-eyes-r301.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r304-integrated-upper-lid-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-integrated-upper-lid-r304.study.json"
BODY = "AevryndFemaleBody_CC0_R249"
RIG = "AevryndFemaleRig"
EYES = {"L": (0.034528, 1.607765, 1.0), "R": (-0.034443, 1.607765, -1.0)}
APERTURE = 0.0027
VARIANTS = (
    ("a-current", None),
    ("b-shallow", -0.1388),
    ("c-blended", -0.1377),
    ("d-deep", -0.1366),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def lid_height(side, x):
    cx, cz, anatomical_sign = EYES[side]
    u = max(-1.0, min(1.0, (x - cx) / 0.01035))
    edge = math.sqrt(max(0.0, 1.0 - u * u))
    outer = anatomical_sign * u
    return cz + APERTURE * edge - 0.00032 * outer * edge


def shift_attached_curves(side):
    cx, cz, _ = EYES[side]
    for name in (f"AevryndEye_{side}_UpperLidMargin_R258", f"AevryndFemaleUpperLashes_{side}_R256"):
        obj = bpy.data.objects.get(name)
        if obj is None or obj.type != "CURVE":
            continue
        obj.data = obj.data.copy()
        for spline in obj.data.splines:
            for point in spline.points:
                u = max(-1.0, min(1.0, (point.co.x - cx) / 0.01035))
                edge = math.sqrt(max(0.0, 1.0 - u * u))
                old = cz + 0.00525 * edge
                point.co.z += lid_height(side, point.co.x) - old


def make_lid(side, outer_y, material, rig):
    cx, cz, anatomical_sign = EYES[side]
    count = 37
    rows = 4
    vertices = []
    for row in range(rows):
        v = row / (rows - 1)
        for index in range(count):
            u = -0.985 + 1.97 * index / (count - 1)
            edge = math.sqrt(max(0.0, 1.0 - u * u))
            outer = anatomical_sign * u
            inner_z = cz + APERTURE * edge - 0.00032 * outer * edge
            z = inner_z + (0.0048 * edge + 0.00035) * v
            if v < 0.5:
                y = -0.14068 - 0.00030 * math.sin(v * math.pi)
            else:
                blend = (v - 0.5) / 0.5
                y = (-0.14098) * (1.0 - blend) + outer_y * blend
            vertices.append((cx + 0.01035 * u, y, z))
    faces = []
    for row in range(rows - 1):
        for index in range(count - 1):
            a = row * count + index
            b = a + 1
            c = a + count + 1
            d = a + count
            faces.append((a, b, c, d))
    mesh = bpy.data.meshes.new(f"AevryndEye_{side}_UpperLidSurface_R304Geometry")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(f"AevryndEye_{side}_UpperLidSurface_R304", mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world
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
for name, outer_y in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    camera = bpy.data.objects["Aevrynd R249 Review Camera"]
    body = bpy.data.objects[BODY]
    skin_material = body.data.materials[0]
    rig = bpy.data.objects[RIG]
    if outer_y is not None:
        for side in EYES:
            shift_attached_curves(side)
            make_lid(side, outer_y, skin_material, rig)
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
    metrics[name] = {"outerY": outer_y, "apertureHeightM": APERTURE, "rows": 4, "pointsPerRow": 37}

report = {"source": str(SOURCE), "renderDirectory": str(OUT), "variants": metrics, "status": "STRICT_VISUAL_SELECTION_REQUIRED"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R304_INTEGRATED_UPPER_LID_SWEEP=" + json.dumps(report, sort_keys=True))
