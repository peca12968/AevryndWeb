import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCRIPT = ROOT / "scripts/build-female-v249-mainline-orbital-r70.py"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-lashes-r72.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-lashes-r72"
BODY = "AevryndFemaleBodyBaseV118"
RIG = "AevryndFemaleRig"
EYES = {"L": (0.034528, -0.10087, 1.607765), "R": (-0.034443, -0.10077, 1.607765)}


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    lower = obj.name.lower()
    return layer.startswith("hair.") or any(token in lower for token in ("hair", "groom", "scalp"))


def body_tree(body):
    points = [vertex.co.copy() for vertex in body.data.vertices]
    faces = [tuple(poly.vertices) for poly in body.data.polygons]
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def surface_root(tree, x, z, fallback_y=-0.121):
    hit, normal, face, distance = tree.ray_cast(Vector((x, -0.20, z)), Vector((0.0, 1.0, 0.0)), 0.20)
    if hit is None:
        return Vector((x, fallback_y, z)), False
    return Vector((x, hit.y - 0.00016, z)), True


def append_tube(vertices, faces, points):
    sides = 5
    radii = (0.000044, 0.000039, 0.000025, 0.000006)
    first = len(vertices)
    for index, point in enumerate(points):
        if index == 0:
            tangent = (points[1] - point).normalized()
        elif index == len(points) - 1:
            tangent = (point - points[index - 1]).normalized()
        else:
            tangent = (points[index + 1] - points[index - 1]).normalized()
        axis_a = Vector((1.0, 0.0, 0.0))
        axis_a = (axis_a - tangent * axis_a.dot(tangent)).normalized()
        axis_b = tangent.cross(axis_a).normalized()
        for side in range(sides):
            angle = 2.0 * math.pi * side / sides
            vertices.append(point + radii[index] * (math.cos(angle) * axis_a + math.sin(angle) * axis_b))
    for ring in range(len(points) - 1):
        current = first + ring * sides
        following = current + sides
        for side in range(sides):
            nxt = (side + 1) % sides
            faces.append((current + side, current + nxt, following + nxt, following + side))
    faces.append(tuple(reversed(tuple(first + side for side in range(sides)))))
    tip = first + (len(points) - 1) * sides
    faces.append(tuple(tip + side for side in range(sides)))


def strand_points(root, length, lateral, upper, phase):
    lateral_tip = length * (0.38 * lateral + 0.08 * phase)
    if upper:
        tip_z = length * (0.38 + 0.16 * (1.0 - abs(lateral)) + 0.05 * phase)
        offsets = (
            (0.0, 0.0, 0.0),
            (0.14 * lateral_tip, -0.20 * length, 0.18 * tip_z),
            (0.52 * lateral_tip, -0.50 * length, 0.58 * tip_z),
            (lateral_tip, -0.78 * length, tip_z),
        )
    else:
        offsets = (
            (0.0, 0.0, 0.0),
            (0.18 * lateral_tip, -0.18 * length, -0.10 * length),
            (0.58 * lateral_tip, -0.42 * length, -0.25 * length),
            (lateral_tip, -0.60 * length, -0.38 * length),
        )
    return [root + Vector(offset) for offset in offsets]


def build_layer(side, upper, tree, material, rig):
    cx, cy, cz = EYES[side]
    count = 24 if upper else 14
    width = 0.01045
    height = 0.00382 if upper else 0.00282
    tilt = (1.0 if side == "L" else -1.0) * 0.023
    vertices = []
    faces = []
    ray_hits = 0
    rng = random.Random(7200 + (0 if side == "L" else 100) + (0 if upper else 50))
    for index in range(count):
        t = (index + 0.65 + rng.uniform(-0.20, 0.20)) / (count + 0.30)
        t = max(0.035, min(0.965, t))
        theta = math.pi * t if upper else math.pi * (1.0 + t)
        x = cx + width * math.cos(theta)
        z = cz + height * math.sin(theta) + tilt * (x - cx)
        z += 0.00016 if upper else -0.00013
        root, hit = surface_root(tree, x, z)
        ray_hits += int(hit)
        lateral = (x - cx) / width
        phase = rng.uniform(-1.0, 1.0)
        if upper:
            length = 0.0031 + 0.00145 * (math.sin(theta) ** 0.70) + 0.00035 * max(0.0, -lateral)
            length *= 0.84 + 0.24 * rng.random()
        else:
            length = 0.00135 + 0.00070 * ((-math.sin(theta)) ** 0.8)
        append_tube(vertices, faces, strand_points(root, length, lateral, upper, phase))
    layer_name = "UpperLashes" if upper else "LowerLashes"
    mesh = bpy.data.meshes.new(f"Eye_{side}_{layer_name}_r72_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(f"Eye_{side}_{layer_name}", mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = rig
    if material is not None:
        obj.data.materials.append(material)
    obj["aevrynd_layer"] = "face.eyelash.upper" if upper else "face.eyelash.lower"
    obj["aevrynd_revision"] = "v249-mainline-lashes-r72"
    obj["aevrynd_root_method"] = "body BVH front-surface raycast plus 0.16mm clearance"
    return obj, {"strands": count, "vertices": len(vertices), "faces": len(faces), "ray_hits": ray_hits}


# Build the collision-safe orbital parent, then replace only the four obsolete
# lash meshes.  Keeping this dependency explicit preserves the v249 lineage.
parent_namespace = {"__file__": str(SOURCE_SCRIPT), "__name__": "__main__"}
exec(compile(SOURCE_SCRIPT.read_text(encoding="utf-8"), str(SOURCE_SCRIPT), "exec"), parent_namespace)
OUT.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects[BODY]
tree = body_tree(body)
rig = bpy.data.objects[RIG]
old_material = None
for name in ("Eye_L_UpperLashes", "Eye_R_UpperLashes", "Eye_L_LowerLashes", "Eye_R_LowerLashes"):
    old = bpy.data.objects.get(name)
    if old is None:
        continue
    if old_material is None and old.type == "MESH" and old.data.materials:
        old_material = old.data.materials[0]
    bpy.data.objects.remove(old, do_unlink=True)

lash_report = {}
for side in ("L", "R"):
    for upper in (True,):
        obj, values = build_layer(side, upper, tree, old_material, rig)
        lash_report[obj.name] = values

body["aevrynd_face_revision"] = "v249-mainline-lashes-r72"
scene = bpy.context.scene
scene["aevrynd_mainline_parent"] = "aevrynd-female-authoring-v249-mainline-orbital-r70.blend"
scene["aevrynd_mainline_revision"] = "lashes-r72"
scene["aevrynd_release_state"] = "R72_STRICT_VISUAL_AND_COLLISION_REVIEW_REQUIRED"
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
hair_objects = [obj for obj in bpy.data.objects if is_hair(obj)]
for obj in hair_objects:
    obj.hide_render = True
for name, location, target, lens in (
    ("01-eye-close-face-only", (0.0, -0.47, 1.610), (0.0, -0.065, 1.608), 112),
    ("02-face-front-face-only", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108),
    ("03-face-three-quarter-face-only", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)
for obj in hair_objects:
    obj.hide_render = False
camera.location = (0.0, -0.72, 1.60)
camera.data.lens = 88
look_at(camera, (0.0, -0.025, 1.595))
scene.render.filepath = str(OUT / "04-face-front-with-hair.png")
bpy.ops.render.render(write_still=True)
report = {"source": str(SOURCE_SCRIPT), "output": str(OUTPUT), "lashes": lash_report, "lower_lash_meshes": "removed pending independently raycast short-fiber rebuild"}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_LASHES_R72=" + json.dumps(report, sort_keys=True))
