import json
import math
import random
import runpy
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-philtrum-r80.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-eye-aperture-r83.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-eye-aperture-r83"
BODY = "AevryndFemaleBodyBaseV118"
RIG = "AevryndFemaleRig"
EYES = {"L": (0.034528, -0.10087, 1.607765), "R": (-0.034443, -0.10077, 1.607765)}
UPPER_AMOUNT = 0.00075
LOWER_AMOUNT = 0.00055
LASH_HEIGHT = 0.00447


helpers = runpy.run_path(str(ROOT / "scripts/sweep-female-v249-mainline-eye-aperture-r83.py"))
look_at = helpers["look_at"]
is_hair = helpers["is_hair"]
sculpt_aperture = helpers["sculpt_aperture"]


def evaluated_body_tree(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [vertex.co.copy() for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def surface_root(tree, x, z):
    hit, _normal, _face, _distance = tree.ray_cast(Vector((x, -0.20, z)), Vector((0.0, 1.0, 0.0)), 0.20)
    if hit is None:
        return Vector((x, -0.121, z)), False
    return Vector((x, hit.y - 0.00016, z)), True


def append_tube(vertices, faces, points):
    sides = 5
    radii = (0.000029, 0.000025, 0.000014, 0.000004)
    first = len(vertices)
    for index, point in enumerate(points):
        tangent = (
            points[1] - point if index == 0
            else point - points[index - 1] if index == len(points) - 1
            else points[index + 1] - points[index - 1]
        ).normalized()
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


def strand_points(root, length, lateral, phase):
    lateral_tip = length * (0.45 * lateral + 0.15 * phase)
    tip_z = length * (0.17 + 0.10 * (1.0 - abs(lateral)) + 0.04 * phase)
    offsets = (
        (0.0, 0.0, 0.0),
        (0.14 * lateral_tip, -0.24 * length, 0.16 * tip_z),
        (0.52 * lateral_tip, -0.60 * length, 0.56 * tip_z),
        (lateral_tip, -0.92 * length, tip_z),
    )
    return [root + Vector(offset) for offset in offsets]


def build_upper_lashes(side, tree, material, rig):
    cx, _cy, cz = EYES[side]
    width = 0.01045
    tilt = (1.0 if side == "L" else -1.0) * 0.023
    vertices, faces = [], []
    hits = 0
    rng = random.Random(8300 + (0 if side == "L" else 100))
    for index in range(38):
        t = max(0.035, min(0.965, (index + 0.65 + rng.uniform(-0.20, 0.20)) / 38.30))
        theta = math.pi * t
        x = cx + width * math.cos(theta)
        z = cz + LASH_HEIGHT * math.sin(theta) + tilt * (x - cx) + 0.00012
        root, hit = surface_root(tree, x, z)
        hits += int(hit)
        lateral = (x - cx) / width
        phase = rng.uniform(-1.0, 1.0)
        length = (0.0029 + 0.00135 * (math.sin(theta) ** 0.70) + 0.00030 * max(0.0, -lateral))
        length *= 0.84 + 0.24 * rng.random()
        append_tube(vertices, faces, strand_points(root, length, lateral, phase))
    mesh = bpy.data.meshes.new(f"Eye_{side}_UpperLashes_r83_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(f"Eye_{side}_UpperLashes", mesh)
    bpy.context.collection.objects.link(obj)
    obj.parent = rig
    group = obj.vertex_groups.new(name="head")
    group.add(list(range(len(vertices))), 1.0, "REPLACE")
    modifier = obj.modifiers.new("Aevrynd Head Follow", "ARMATURE")
    modifier.object = rig
    if material:
        obj.data.materials.append(material)
    obj["aevrynd_layer"] = "face.eyelash.upper"
    obj["aevrynd_revision"] = "v249-mainline-eye-aperture-r83"
    obj["aevrynd_root_method"] = "evaluated-body BVH raycast after aperture shape keys"
    return {"strands": 38, "vertices": len(vertices), "faces": len(faces), "ray_hits": hits}


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects[BODY]
geometry = sculpt_aperture(body, UPPER_AMOUNT, LOWER_AMOUNT)
key = body.data.shape_keys.key_blocks[geometry["shape_key"]]
key.name = "Aevrynd_EyeAperture_Topology_R83"
geometry["shape_key"] = key.name
bpy.context.view_layer.update()
tree = evaluated_body_tree(body)
rig = bpy.data.objects[RIG]
material = None
for side in ("L", "R"):
    old = bpy.data.objects.get(f"Eye_{side}_UpperLashes")
    if old is not None:
        if material is None and old.data.materials:
            material = old.data.materials[0]
        bpy.data.objects.remove(old, do_unlink=True)
lash_report = {side: build_upper_lashes(side, tree, material, rig) for side in ("L", "R")}
removed_folds = 0
for side in ("L", "R"):
    fold = bpy.data.objects.get(f"Eye_{side}_UpperFold")
    if fold is not None and fold.hide_render:
        bpy.data.objects.remove(fold, do_unlink=True)
        removed_folds += 1
    for part in ("Sclera", "Cornea", "Iris", "Pupil", "Catchlight"):
        optical = bpy.data.objects.get(f"Eye_{side}_{part}")
        if optical is None or optical.type != "MESH":
            continue
        optical.data = optical.data.copy()
        for vertex in optical.data.vertices:
            vertex.co.y += 0.00008
        optical.data.update()
body["aevrynd_face_revision"] = "v249-mainline-eye-aperture-r83"
body["aevrynd_eye_aperture_method"] = "editable upper/lower lid topology shape key with evaluated-surface regenerated lashes"
scene = bpy.context.scene
scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "eye-aperture-r83"
scene["aevrynd_release_state"] = "R83_STRICT_VISUAL_COLLISION_AND_RUNTIME_REVIEW_REQUIRED"
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
hair_objects = [obj for obj in bpy.data.objects if is_hair(obj)]
for obj in hair_objects:
    obj.hide_render = True
render(camera, "01-eye-close-face-only", (0.0, -0.48, 1.610), (0.0, -0.065, 1.608), 122)
render(camera, "02-face-three-quarter-face-only", (0.38, -0.52, 1.625), (0.0, -0.025, 1.608), 108)
for obj in hair_objects:
    obj.hide_render = False
render(camera, "03-face-front-with-hair", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88)
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "geometry": geometry,
    "lashes": lash_report, "lash_height_mm": LASH_HEIGHT * 1000.0,
    "removed_hidden_legacy_upper_folds": removed_folds,
    "additional_optical_recess_mm": 0.08,
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_EYE_APERTURE_R83=" + json.dumps(report, sort_keys=True))
