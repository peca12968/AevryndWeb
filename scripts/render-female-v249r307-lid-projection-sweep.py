import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-recessed-natural-eyes-r301.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r307-lid-projection-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-lid-projection-r307.study.json"
BODY = "AevryndFemaleBody_CC0_R249"
RIG = "AevryndFemaleRig"
EYES = {"L": (0.034528, 1.607765, 1.0), "R": (-0.034443, 1.607765, -1.0)}
APERTURE = 0.0027
CORNER_RECEDE = 0.0035
VARIANTS = (("a-current", None), ("b-fast", 0.65), ("c-linear", 1.0), ("d-slow", 1.5))


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def lid_z(side, u):
    _cx, cz, sign = EYES[side]
    edge = math.sqrt(max(0.0, 1.0 - u * u))
    return cz + APERTURE * edge - 0.00032 * sign * u * edge


def shift_curves(side):
    cx, cz, _ = EYES[side]
    for name in (f"AevryndEye_{side}_UpperLidMargin_R258", f"AevryndFemaleUpperLashes_{side}_R256"):
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        obj.data = obj.data.copy()
        for spline in obj.data.splines:
            for point in spline.points:
                u = max(-1.0, min(1.0, (point.co.x - cx) / 0.01035))
                edge = math.sqrt(max(0.0, 1.0 - u * u))
                point.co.z += lid_z(side, u) - (cz + 0.00525 * edge)


def make_lid(side, projection_power, material, rig, body_bvh):
    cx, _cz, _sign = EYES[side]
    count, rows = 41, 5
    verts = []
    for row in range(rows):
        v = row / (rows - 1)
        for index in range(count):
            u = -0.985 + 1.97 * index / (count - 1)
            edge = math.sqrt(max(0.0, 1.0 - u * u))
            inner_z = lid_z(side, u)
            inner_y = -0.14072 + CORNER_RECEDE * (abs(u) ** 2.15)
            point = Vector((cx + 0.01035 * u, inner_y - 0.00024 * math.sin(v * math.pi), inner_z + (0.0048 * edge + 0.00035) * v))
            nearest, normal, _index, _distance = body_bvh.find_nearest(point)
            if nearest is not None:
                surface = nearest + normal.normalized() * 0.00010
                blend = v ** projection_power
                point = point.lerp(surface, blend)
            verts.append(tuple(point))
    faces = []
    for row in range(rows - 1):
        for index in range(count - 1):
            a = row * count + index
            faces.append((a, a + 1, a + count + 1, a + count))
    mesh = bpy.data.meshes.new(f"Lid{side}")
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj = bpy.data.objects.new(f"AevryndEye_{side}_UpperLidSurface_R306", mesh)
    bpy.context.scene.collection.objects.link(obj)
    world = obj.matrix_world.copy()
    obj.parent, obj.parent_type, obj.parent_bone = rig, "BONE", "head"
    obj.matrix_world = world


OUT.mkdir(parents=True, exist_ok=True)
metrics = {}
for name, projection_power in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.frame_set(1)
    bpy.context.view_layer.update()
    body = bpy.data.objects[BODY]
    rig = bpy.data.objects[RIG]
    if projection_power is not None:
        body_bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
        for side in EYES:
            shift_curves(side)
            make_lid(side, projection_power, body.data.materials[0], rig, body_bvh)
    camera = bpy.data.objects["Aevrynd R249 Review Camera"]
    for suffix, location in (("front", (0.0, -0.68, 1.605)), ("three-quarter", (0.45, -0.62, 1.62)), ("profile", (0.67, -0.36, 1.61))):
        camera.location = location
        camera.data.lens = 92
        look_at(camera, (0.0, -0.02, 1.605))
        scene.render.resolution_x = scene.render.resolution_y = 1000
        scene.render.filepath = str(OUT / f"{name}-{suffix}.png")
        bpy.ops.render.render(write_still=True)
    metrics[name] = {"cornerRecedeM": CORNER_RECEDE if projection_power is not None else None, "projectionPower": projection_power, "apertureHeightM": APERTURE}

report = {"source": str(SOURCE), "renderDirectory": str(OUT), "variants": metrics, "status": "STRICT_VISUAL_SELECTION_REQUIRED"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R307_LID_PROJECTION_SWEEP=" + json.dumps(report, sort_keys=True))
