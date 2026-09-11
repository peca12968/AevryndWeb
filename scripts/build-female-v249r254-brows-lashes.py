import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-iris-uv-catchlight-r253.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-brows-lashes-r254.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-brows-lashes-r254.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r254-brows-lashes"
BODY = "AevryndFemaleBody_CC0_R249"
RIG = "AevryndFemaleRig"
HEAD_BONE = "head"


def fiber_material(name, color, roughness):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Specular IOR Level"].default_value = 0.22
    material["aevrynd_layer"] = "material.keratin.fiber"
    return material


def curve_object(name, splines, radii, material, layer, bevel_depth, rig):
    curve = bpy.data.curves.new(name + "Geometry", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 2
    curve.resolution_u = 2
    for points, point_radii in zip(splines, radii):
        spline = curve.splines.new("POLY")
        spline.points.add(len(points) - 1)
        for point, coordinate, radius in zip(spline.points, points, point_radii):
            point.co = (*coordinate, 1.0)
            point.radius = radius
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    obj["aevrynd_layer"] = layer
    obj["aevrynd_revision"] = "v249r254"
    obj["aevrynd_binding"] = "rig.head"
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = HEAD_BONE
    obj.matrix_world = world
    return obj


def front_surface_y(points, x, z, radius=0.0018):
    candidates = [point.y for point in points if (point.x - x) ** 2 + (point.z - z) ** 2 <= radius * radius]
    if candidates:
        return min(candidates)
    nearest = min(points, key=lambda point: (point.x - x) ** 2 + (point.z - z) ** 2)
    return nearest.y


def build_brow(side, body_points, material, rig):
    sign = 1.0 if side == "L" else -1.0
    splines = []
    radii = []
    root_clearances = []
    rows = 3
    columns = 34
    for row in range(rows):
        for column in range(columns):
            t = (column + 0.18 * row) / (columns - 1 + 0.36)
            x = sign * (0.0148 + 0.0385 * t)
            arch = math.sin(math.pi * min(1.0, max(0.0, t)))
            z = 1.6288 + 0.0108 * arch - 0.0023 * t + (row - 1) * 0.00055
            surface_y = front_surface_y(body_points, x, z)
            y = surface_y - (0.00042 + 0.00010 * row)
            length = 0.0030 + 0.0019 * arch
            tangent_x = sign * length * (0.48 - 0.62 * t)
            lift = length * (0.76 - 0.32 * t)
            forward = -length * 0.16
            phase = math.sin(column * 2.37 + row * 1.71)
            points = (
                (x, y, z),
                (x + tangent_x * 0.52, y + forward * 0.45, z + lift * 0.58 + phase * 0.00016),
                (x + tangent_x, y + forward, z + lift + phase * 0.00022),
            )
            splines.append(points)
            radii.append((0.80, 0.48, 0.12))
            root_clearances.append(surface_y - y)
    obj = curve_object(
        f"AevryndFemaleBrow_{side}_R254", splines, radii, material,
        f"face.{side.lower()}.eyebrow_fibers", 0.000105, rig,
    )
    return obj, root_clearances


def build_lashes(side, kind, center, sclera_front, material, rig):
    sign = 1.0 if side == "L" else -1.0
    upper = kind == "Upper"
    count = 30 if upper else 16
    splines = []
    radii = []
    for index in range(count):
        u = -0.93 + 1.86 * index / (count - 1)
        edge = math.sqrt(max(0.0, 1.0 - u * u))
        x = center.x + 0.01025 * u
        z = center.z + (0.00545 * edge if upper else -0.00465 * edge)
        y = sclera_front - (0.00044 if upper else 0.00034)
        corner = max(0.18, edge)
        length = (0.0038 if upper else 0.00175) * corner
        lateral = sign * 0.0006 * u * corner
        points = (
            (x, y, z),
            (x + lateral * 0.45, y - length * 0.48, z + (length * 0.38 if upper else -length * 0.10)),
            (x + lateral, y - length, z + (length * 0.78 if upper else -length * 0.20)),
        )
        splines.append(points)
        radii.append((0.72, 0.40, 0.08))
    obj = curve_object(
        f"AevryndFemale{kind}Lashes_{side}_R254", splines, radii, material,
        f"face.{side.lower()}.{kind.lower()}_eyelashes", 0.000075 if upper else 0.000055, rig,
    )
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, frame, name, location, target, lens, size):
    scene = bpy.context.scene
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY]
rig = bpy.data.objects[RIG]
evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
mesh = evaluated.to_mesh()
body_points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]

brow_material = fiber_material("Aevrynd_BrowFiber_R254", (0.018, 0.0065, 0.0032, 1.0), 0.52)
lash_material = fiber_material("Aevrynd_LashFiber_R254", (0.004, 0.0015, 0.0007, 1.0), 0.40)
created = []
metrics = {"brows": {}, "lashes": {}}
for side in ("L", "R"):
    brow, clearances = build_brow(side, body_points, brow_material, rig)
    created.append(brow.name)
    metrics["brows"][side] = {
        "fibers": len(brow.data.splines),
        "minimumAuthoredRootClearanceM": min(clearances),
        "maximumAuthoredRootClearanceM": max(clearances),
    }
    sclera = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
    points = [sclera.matrix_world @ vertex.co for vertex in sclera.data.vertices]
    center = Vector((
        sum(point.x for point in points) / len(points),
        sum(point.y for point in points) / len(points),
        sum(point.z for point in points) / len(points),
    ))
    sclera_front = min(point.y for point in points)
    for kind in ("Upper", "Lower"):
        lashes = build_lashes(side, kind, center, sclera_front, lash_material, rig)
        created.append(lashes.name)
        metrics["lashes"][f"{side}.{kind}"] = len(lashes.data.splines)
evaluated.to_mesh_clear()

scene["aevrynd_mainline_revision"] = "v249r254-brows-lashes"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "BROW_LASH_VISUAL_AND_COLLISION_REVIEW_PENDING"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    (1, "01-face-front", (0.0, -1.02, 1.66), (0.0, 0.0, 1.625), 92, (1100, 1100)),
    (1, "02-face-three-quarter", (0.56, -0.89, 1.65), (0.0, 0.0, 1.615), 92, (1100, 1100)),
    (1, "03-eye-front", (0.0, -0.55, 1.616), (0.0, -0.13, 1.608), 105, (1200, 700)),
    (1, "04-eye-profile", (0.36, -0.49, 1.616), (0.034, -0.13, 1.608), 105, (1000, 800)),
    (20, "05-pose-face", (0.56, -0.89, 1.65), (0.0, 0.0, 1.615), 92, (1100, 1100)),
)
for values in views:
    render(camera, *values)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "createdLayers": created,
    "metrics": metrics,
    "renderDirectory": str(RENDER_DIR),
    "limitations": ["tear meniscus and lid wetline pending", "identity sculpt pending", "hair pending"],
    "status": "BROW_LASH_VISUAL_AND_COLLISION_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R254_BROWS_LASHES=" + json.dumps(report, sort_keys=True))
