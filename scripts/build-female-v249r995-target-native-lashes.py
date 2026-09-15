"""Rebuild owned lashes directly on the current r962-derived eyelid surface."""

import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-natural-brow-lash-balance-r992.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-target-native-lashes-r995.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-target-native-lashes-r995.build-report.json"
AUDIT = ASSETS / "female-v249-mainline-cc0-target-native-lashes-r995.triangle-collision-audit.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r995-target-native-lashes"
BODY = "AevryndFemaleCC0Baseline_v259"
RIG = "AevryndFemaleRig"
FRAMES = (1, 20, 33, 61)


def world_tree(obj, depsgraph=None):
    depsgraph = depsgraph or bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def front_point(tree, x, z, clearance):
    hit = tree.ray_cast(Vector((x, -0.20, z)), Vector((0.0, 1.0, 0.0)), 0.30)
    if hit[0] is None or hit[1] is None:
        raise RuntimeError(f"lash root ray missed x={x:.5f} z={z:.5f}")
    normal = hit[1].normalized()
    if normal.y > 0.0:
        normal.negate()
    return hit[0] + normal * clearance


def keep_outside(tree, point, clearance):
    hit = tree.find_nearest(point, 0.04)
    if hit is None or hit[1] is None:
        return point
    normal = hit[1].normalized()
    signed = (point - hit[0]).dot(normal)
    return hit[0] + normal * clearance if signed < clearance else point


def add_fiber(vertices, faces, points, radius, sides=3):
    base = len(vertices)
    for row, point in enumerate(points):
        before = points[max(0, row - 1)]
        after = points[min(len(points) - 1, row + 1)]
        tangent = (after - before).normalized()
        axis_a = tangent.cross(Vector((1.0, 0.0, 0.0)))
        if axis_a.length < 1e-8:
            axis_a = tangent.cross(Vector((0.0, 0.0, 1.0)))
        axis_a.normalize()
        axis_b = tangent.cross(axis_a).normalized()
        t = row / (len(points) - 1)
        width = radius * max(0.05, (1.0 - t) ** 1.3)
        for side in range(sides):
            angle = math.tau * side / sides
            vertices.append(tuple(point + axis_a * math.cos(angle) * width + axis_b * math.sin(angle) * width))
    for row in range(len(points) - 1):
        for side in range(sides):
            a = base + row * sides + side
            b = base + row * sides + (side + 1) % sides
            c = base + (row + 1) * sides + (side + 1) % sides
            d = base + (row + 1) * sides + side
            faces.append((a, b, c, d))


def rebuild(body_tree, cornea_tree, rig, side, center_x, upper, material):
    kind = "Upper" if upper else "Lower"
    name = f"Eye_{side}_{kind}Lashes"
    old = bpy.data.objects.get(name)
    if old:
        old_mesh = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)
    rng = random.Random(995000 + (1 if side == "L" else 2) + (0 if upper else 10))
    count = 46 if upper else 22
    vertices, faces, lengths = [], [], []
    for index in range(count):
        fraction = (index + 0.5 + rng.uniform(-0.22, 0.22)) / count
        t = fraction * 2.0 - 1.0
        x = center_x + t * (0.0102 if upper else 0.0097)
        arc = math.sqrt(max(0.0, 1.0 - t * t))
        z = 1.4518 + ((0.0065 + 0.0010 * (1.0 - abs(t))) * arc if upper else -(0.0042 * arc))
        z += rng.uniform(-0.00007, 0.00007)
        root = front_point(body_tree, x, z, 0.00062 if upper else 0.00050)
        envelope = math.sin(math.pi * fraction) ** 0.70
        temple_sign = 1.0 if center_x > 0.0 else -1.0
        outer = t * temple_sign
        if upper:
            length = (0.0030 + 0.0028 * envelope) * (0.82 + 0.18 * (outer + 1.0) * 0.5) * rng.uniform(0.88, 1.10)
            rise = rng.uniform(0.26, 0.42)
            forward = rng.uniform(0.90, 1.04)
            radius = rng.uniform(0.000040, 0.000058)
        else:
            length = (0.0012 + 0.0013 * envelope) * rng.uniform(0.86, 1.08)
            rise = -rng.uniform(0.10, 0.22)
            forward = rng.uniform(0.94, 1.06)
            radius = rng.uniform(0.000024, 0.000036)
        lateral = temple_sign * (0.06 + 0.18 * max(0.0, outer))
        cluster = ((index % 3) - 1) * (0.025 if upper else 0.016)
        direction = Vector((lateral + cluster, -forward, rise)).normalized()
        points = [keep_outside(cornea_tree, root, 0.00012)]
        for row in range(1, 7):
            progress = row / 6
            curl = Vector((
                temple_sign * 0.00016 * progress * progress,
                0.00048 * progress * progress,
                (0.00062 if upper else -0.00012) * progress * progress,
            ))
            point = root + direction * length * progress + curl
            points.append(keep_outside(cornea_tree, point, 0.00012))
        add_fiber(vertices, faces, points, radius)
        lengths.append((points[-1] - points[0]).length)
    mesh = bpy.data.meshes.new(name + "MeshR995")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_role"] = "upper_lashes" if upper else "lower_lashes"
    obj["aevrynd_revision"] = "v249r995"
    obj["aevrynd_fiber_count"] = count
    obj["aevrynd_length_min_m"] = min(lengths)
    obj["aevrynd_length_max_m"] = max(lengths)
    obj["aevrynd_root_clearance_m"] = 0.00062 if upper else 0.00050
    obj["aevrynd_source"] = "Aevrynd deterministic target-surface generation"
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = Matrix.Identity(4)
    return obj


def audit(scene):
    failures, frames = [], {}
    for frame in FRAMES:
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        body = world_tree(bpy.data.objects[BODY], depsgraph)
        frame_data = {}
        for side in ("L", "R"):
            upper = world_tree(bpy.data.objects[f"Eye_{side}_UpperLashes"], depsgraph)
            lower = world_tree(bpy.data.objects[f"Eye_{side}_LowerLashes"], depsgraph)
            sclera = world_tree(bpy.data.objects[f"Eye_{side}_Sclera"], depsgraph)
            cornea = world_tree(bpy.data.objects[f"Eye_{side}_Cornea"], depsgraph)
            values = {"upperBody": len(upper.overlap(body)), "lowerBody": len(lower.overlap(body)),
                      "upperSclera": len(upper.overlap(sclera)), "lowerSclera": len(lower.overlap(sclera)),
                      "upperCornea": len(upper.overlap(cornea)), "lowerCornea": len(lower.overlap(cornea)),
                      "upperLower": len(upper.overlap(lower))}
            frame_data[side] = values
            for label, count in values.items():
                if count:
                    failures.append({"frame": frame, "side": side, "pair": label, "triangleOverlapCount": count})
        frames[str(frame)] = frame_data
    return frames, failures


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body_tree = world_tree(bpy.data.objects[BODY])
rig = bpy.data.objects[RIG]
material = bpy.data.materials["Aevrynd_Lash_Hair_v51"]
lashes = []
for side, center_x in (("L", 0.02815), ("R", -0.02815)):
    cornea_tree = world_tree(bpy.data.objects[f"Eye_{side}_Cornea"])
    lashes.append(rebuild(body_tree, cornea_tree, rig, side, center_x, True, material))
    lashes.append(rebuild(body_tree, cornea_tree, rig, side, center_x, False, material))
frames, failures = audit(scene)
status = "PASS" if not failures else "FAIL"
AUDIT.write_text(json.dumps({"source": str(SOURCE), "model": str(OUTPUT), "frames": frames,
                             "failures": failures, "status": status}, indent=2), encoding="utf-8")
scene["aevrynd_mainline_revision"] = "v249r995-target-native-lashes"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "DYNAMIC_FACE_FEATURE_COLLISION_PASS_VISUAL_REVIEW_PENDING" if not failures else "FACE_FEATURE_REJECTED"
scene["aevrynd_website_promotion"] = "forbidden pending visual and runtime gates"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
scene.render.resolution_x = scene.render.resolution_y = 900
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects.get("Aevrynd Review Camera") or scene.camera
scene.camera = camera
scene.frame_set(1)
bpy.context.view_layer.update()
for args in (
    ("01-face-front", (0.0, -0.68, 1.49), (0.0, -0.055, 1.48), 88),
    ("02-face-three-quarter", (0.42, -0.58, 1.51), (0.0, -0.045, 1.48), 88),
    ("03-face-profile", (0.68, -0.02, 1.50), (0.0, -0.035, 1.48), 90),
    ("04-eye-front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.485), 105),
    ("05-eye-three-quarter", (0.30, -0.40, 1.49), (0.0, -0.055, 1.485), 105),
    ("06-full-three-quarter", (1.10, -1.62, 1.22), (0.0, -0.01, 0.92), 58),
):
    render(scene, camera, *args)
report = {"source": str(SOURCE), "output": str(OUTPUT), "audit": str(AUDIT),
          "layers": {obj.name: {"fibers": obj["aevrynd_fiber_count"], "vertices": len(obj.data.vertices),
                                  "polygons": len(obj.data.polygons), "lengthRangeM": [obj["aevrynd_length_min_m"], obj["aevrynd_length_max_m"]]} for obj in lashes},
          "auditStatus": status, "websitePromotionApproved": False,
          "status": "DYNAMIC_COLLISION_PASS_VISUAL_REVIEW_REQUIRED" if not failures else "REJECTED"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R995_TARGET_NATIVE_LASHES=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
