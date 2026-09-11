import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-iris-uv-catchlight-r253.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-natural-brows-lashes-r255.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-natural-brows-lashes-r255.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r255-natural-brows-lashes"
BODY = "AevryndFemaleBody_CC0_R249"
RIG = "AevryndFemaleRig"


def material(name, color, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = next(node for node in mat.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Specular IOR Level"].default_value = 0.20
    mat["aevrynd_layer"] = "material.keratin.fiber"
    return mat


def make_curves(name, fibers, mat, layer, depth, rig):
    data = bpy.data.curves.new(name + "Geometry", "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 2
    data.bevel_depth = depth
    data.bevel_resolution = 2
    for coords, radii in fibers:
        spline = data.splines.new("POLY")
        spline.points.add(len(coords) - 1)
        for point, co, radius in zip(spline.points, coords, radii):
            point.co = (*co, 1.0)
            point.radius = radius
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    data.materials.append(mat)
    obj["aevrynd_layer"] = layer
    obj["aevrynd_revision"] = "v249r255"
    obj["aevrynd_binding"] = "rig.head"
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world
    return obj


def front_y(points, x, z, radius=0.0017):
    values = [p.y for p in points if (p.x - x) ** 2 + (p.z - z) ** 2 <= radius * radius]
    return min(values) if values else min(points, key=lambda p: (p.x - x) ** 2 + (p.z - z) ** 2).y


def brow_fibers(side, body_points):
    sign = 1.0 if side == "L" else -1.0
    fibers = []
    roots = []
    rows, columns = 5, 44
    for row in range(rows):
        band = (row - (rows - 1) / 2.0) * 0.00052
        for column in range(columns):
            jitter = 0.31 * math.sin(column * 1.83 + row * 2.71)
            t = (column + 0.22 * row + jitter) / (columns - 1 + 0.88)
            t = min(1.0, max(0.0, t))
            x = sign * (0.0152 + 0.0382 * t)
            arch = math.sin(math.pi * (t ** 0.92))
            z_path = 1.6272 + 0.0064 * arch - 0.0012 * t
            z = z_path + band
            surface = front_y(body_points, x, z)
            clearance = 0.00038 + row * 0.000045
            y = surface - clearance
            taper = max(0.24, math.sin(math.pi * min(0.98, max(0.02, t))))
            length = (0.0022 + 0.0010 * taper) * (0.92 + 0.12 * math.sin(column * 2.19 + row))
            dx = sign * length * (0.84 - 0.18 * t)
            dz = length * (0.30 - 0.52 * t)
            dy = -length * (0.09 + 0.04 * math.sin(column * 1.27))
            coords = (
                (x, y, z),
                (x + dx * 0.52, y + dy * 0.42, z + dz * 0.55),
                (x + dx, y + dy, z + dz),
            )
            fibers.append((coords, (0.72, 0.42, 0.08)))
            roots.append(clearance)
    return fibers, roots


def lash_fibers(side, upper, center, sclera_front):
    count = 38 if upper else 11
    fibers = []
    for index in range(count):
        base_t = index / (count - 1)
        u = -0.91 + 1.82 * base_t + 0.010 * math.sin(index * 2.41)
        edge = math.sqrt(max(0.0, 1.0 - u * u))
        x = center.x + 0.0102 * u
        z = center.z + ((0.00525 * edge + 0.00008 * math.sin(index * 1.9)) if upper else (-0.00448 * edge))
        y = sclera_front - (0.00040 if upper else 0.00030)
        envelope = max(0.16, edge)
        cluster = 0.82 + 0.22 * math.sin(index * 2.07 + (0.3 if side == "L" else 1.1))
        length = (0.00315 if upper else 0.00125) * envelope * cluster
        lateral = (1.0 if side == "L" else -1.0) * 0.00025 * u
        lift = length * ((0.62 + 0.10 * math.sin(index * 1.37)) if upper else -0.10)
        coords = (
            (x, y, z),
            (x + lateral * 0.45, y - length * 0.50, z + lift * 0.50),
            (x + lateral, y - length, z + lift),
        )
        fibers.append((coords, (0.66, 0.34, 0.05)))
    return fibers


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
brow_mat = material("Aevrynd_BrowFiber_Natural_R255", (0.013, 0.0045, 0.0022, 1.0), 0.56)
lash_mat = material("Aevrynd_LashFiber_Clustered_R255", (0.0025, 0.0008, 0.00035, 1.0), 0.43)
created = []
metrics = {"brows": {}, "lashes": {}}
for side in ("L", "R"):
    brow, roots = brow_fibers(side, body_points)
    obj = make_curves(f"AevryndFemaleBrow_{side}_R255", brow, brow_mat, f"face.{side.lower()}.eyebrow_fibers", 0.000068, rig)
    created.append(obj.name)
    metrics["brows"][side] = {"fibers": len(brow), "minimumRootClearanceM": min(roots), "maximumRootClearanceM": max(roots)}
    sclera = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
    points = [sclera.matrix_world @ vertex.co for vertex in sclera.data.vertices]
    center = Vector((sum(p.x for p in points) / len(points), sum(p.y for p in points) / len(points), sum(p.z for p in points) / len(points)))
    front = min(p.y for p in points)
    for upper in (True, False):
        fibers = lash_fibers(side, upper, center, front)
        kind = "Upper" if upper else "Lower"
        obj = make_curves(f"AevryndFemale{kind}Lashes_{side}_R255", fibers, lash_mat, f"face.{side.lower()}.{kind.lower()}_eyelashes", 0.000055 if upper else 0.000040, rig)
        created.append(obj.name)
        metrics["lashes"][f"{side}.{kind}"] = len(fibers)
evaluated.to_mesh_clear()

scene["aevrynd_mainline_revision"] = "v249r255-natural-brows-lashes"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "NATURAL_BROW_LASH_VISUAL_AND_COLLISION_REVIEW_PENDING"
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
report = {"source": str(SOURCE), "output": str(OUTPUT), "createdLayers": created, "metrics": metrics, "renderDirectory": str(RENDER_DIR), "limitations": ["tear meniscus and lid wetline pending", "identity sculpt pending", "hair pending"], "status": "NATURAL_BROW_LASH_VISUAL_AND_COLLISION_REVIEW_PENDING"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R255_NATURAL_BROWS_LASHES=" + json.dumps(report, sort_keys=True))
