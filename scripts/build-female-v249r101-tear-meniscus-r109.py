import json
import math
import runpy
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-scalp-foundation-r101.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-tear-meniscus-r109.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-tear-meniscus-r109"
BODY = "AevryndFemaleBodyBaseV118"
RIG = "AevryndFemaleRig"
EYES = {"L": (0.034528, -0.10087, 1.607765), "R": (-0.034443, -0.10077, 1.607765)}
RADIUS = 0.000060

helpers = runpy.run_path(str(ROOT / "scripts/sweep-female-v249r101-tear-meniscus-r109.py"))
body_tree = helpers["body_tree"]
lower_lid_edge = helpers["lower_lid_edge"]
tear_material = helpers["tear_material"]
look_at = helpers["look_at"]
is_hair = helpers["is_hair"]


def append_tube(vertices, faces, points, radius):
    sides = 6
    for index, point in enumerate(points):
        tangent = (
            points[1] - point if index == 0
            else point - points[index - 1] if index == len(points) - 1
            else points[index + 1] - points[index - 1]
        ).normalized()
        axis_a = Vector((0.0, 1.0, 0.0))
        axis_a = (axis_a - tangent * axis_a.dot(tangent)).normalized()
        axis_b = tangent.cross(axis_a).normalized()
        for side in range(sides):
            angle = 2.0 * math.pi * side / sides
            vertices.append(point + radius * (math.cos(angle) * axis_a + math.sin(angle) * axis_b))
    for ring in range(len(points) - 1):
        current = ring * sides
        following = current + sides
        for side in range(sides):
            nxt = (side + 1) % sides
            faces.append((current + side, current + nxt, following + nxt, following + side))
    faces.append(tuple(reversed(range(sides))))
    last = (len(points) - 1) * sides
    faces.append(tuple(last + side for side in range(sides)))


def bone_parent(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


def evaluated_body_tree(body):
    return body_tree(body)


def project_mesh_clear(obj, tree, target=0.00022):
    inverse = obj.matrix_world.inverted()
    corrected = 0
    maximum = 0.0
    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        hit = tree.find_nearest(world)
        if hit is None or hit[1] is None or hit[3] > 0.004:
            continue
        normal = hit[1].normalized()
        signed = (world - hit[0]).dot(normal)
        if signed >= target:
            continue
        delta = normal * (target - signed)
        vertex.co = inverse @ (world + delta)
        corrected += 1
        maximum = max(maximum, delta.length)
    obj.data.update()
    return {"correctedVertices": corrected, "maximumCorrectionM": maximum}


def build(side, center, tree, material, rig):
    cx, _cy, cz = center
    lateral = 1.0 if side == "L" else -1.0
    points = []
    for index in range(37):
        u = -0.88 + 1.76 * index / 36.0
        arc = math.sqrt(max(0.0, 1.0 - u * u))
        x = cx + 0.01045 * u
        tilt = lateral * 0.023 * (x - cx)
        aperture_z = cz - 0.00282 * arc + tilt
        point = lower_lid_edge(tree, x, aperture_z)
        if point is None:
            raise RuntimeError(f"missing evaluated lower-lid hit: {side} u={u:.4f}")
        points.append(point)

    vertices, faces = [], []
    append_tube(vertices, faces, points, RADIUS)
    mesh = bpy.data.meshes.new(f"Eye_{side}_TearMeniscus_R109_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(f"Eye_{side}_TearMeniscus", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(material)
    bone_parent(obj, rig)
    obj["aevrynd_layer"] = "face.eye.tear-meniscus"
    obj["aevrynd_revision"] = "v249-mainline-tear-meniscus-r109"
    obj["aevrynd_source"] = "evaluated lower-lid edge; 60um clear wet arc"
    return {"points": len(points), "vertices": len(vertices), "faces": len(faces), "radius_um": RADIUS * 1_000_000.0}


def render(camera, name, location, target, lens, size):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects[BODY]
rig = bpy.data.objects[RIG]
tree = body_tree(body)
material = tear_material()
material.name = "Aevrynd_TearMeniscus_Clear_R109"
legacy = []
for side in ("L", "R"):
    old = bpy.data.objects.get(f"Eye_{side}_TearMeniscus")
    if old is not None:
        legacy.append(old.name)
        bpy.data.objects.remove(old, do_unlink=True)
geometry = {side: build(side, EYES[side], tree, material, rig) for side in ("L", "R")}

projection_passes = []
for pass_index in range(5):
    for frame in (1, 20):
        scene = bpy.context.scene
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        frame_tree = evaluated_body_tree(body)
        for side in ("L", "R"):
            result = project_mesh_clear(bpy.data.objects[f"Eye_{side}_TearMeniscus"], frame_tree)
            projection_passes.append({"pass": pass_index + 1, "frame": frame, "side": side, **result})

scene = bpy.context.scene
scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "tear-meniscus-r109"
scene["aevrynd_release_state"] = "R109_VISUAL_AND_COLLISION_REVIEW_REQUIRED"
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
hair_state = {obj.name: obj.hide_render for obj in bpy.data.objects if is_hair(obj)}
for name in hair_state:
    bpy.data.objects[name].hide_render = True
render(camera, "01-eyes-front-face-only", (0.0, -0.445, 1.611), (0.0, -0.076, 1.608), 132, (1280, 760))
render(camera, "02-left-eye-three-quarter-face-only", (0.225, -0.390, 1.628), (0.018, -0.080, 1.607), 138, (1100, 900))
for name, hidden in hair_state.items():
    bpy.data.objects[name].hide_render = hidden
render(camera, "03-face-front-with-hair", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000))

report = {
    "source": str(SOURCE), "output": str(OUTPUT), "legacyRemoved": legacy,
    "geometry": geometry, "projectionTargetM": 0.00022, "projectionPasses": projection_passes,
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_R101_TEAR_MENISCUS_R109_BUILD=" + json.dumps(report, sort_keys=True))
