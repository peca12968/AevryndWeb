"""Add owned lower-lid wetline layers on the current target face."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-target-native-lashes-r995.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-lower-wetline-r996.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-lower-wetline-r996.build-report.json"
AUDIT = ASSETS / "female-v249-mainline-cc0-lower-wetline-r996.triangle-collision-audit.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r996-lower-wetline"
BODY = "AevryndFemaleCC0Baseline_v259"
RIG = "AevryndFemaleRig"
FRAMES = (1, 20, 33, 61)


def world_tree(obj, depsgraph=None):
    depsgraph = depsgraph or bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    verts = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polys = [tuple(poly.vertices) for poly in mesh.polygons]
    tree = BVHTree.FromPolygons(verts, polys, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def front_surface(tree, x, z, clearance):
    hit = tree.ray_cast(Vector((x, -0.20, z)), Vector((0.0, 1.0, 0.0)), 0.30)
    if hit[0] is None or hit[1] is None:
        raise RuntimeError(f"wetline ray miss x={x:.5f} z={z:.5f}")
    normal = hit[1].normalized()
    if normal.y > 0.0:
        normal.negate()
    return hit[0] + normal * clearance


def make_tube(name, points, material, radius=0.00016, sides=5):
    vertices, faces = [], []
    for row, point in enumerate(points):
        previous = points[max(0, row - 1)]
        following = points[min(len(points) - 1, row + 1)]
        tangent = (following - previous).normalized()
        axis_a = tangent.cross(Vector((0.0, 0.0, 1.0)))
        if axis_a.length < 1e-8:
            axis_a = tangent.cross(Vector((0.0, 1.0, 0.0)))
        axis_a.normalize()
        axis_b = tangent.cross(axis_a).normalized()
        taper = min(1.0, row / 3.0, (len(points) - 1 - row) / 3.0)
        width = radius * (0.35 + 0.65 * taper)
        for side in range(sides):
            angle = math.tau * side / sides
            vertices.append(tuple(point + axis_a * math.cos(angle) * width + axis_b * math.sin(angle) * width))
    for row in range(len(points) - 1):
        for side in range(sides):
            a = row * sides + side
            b = row * sides + (side + 1) % sides
            c = (row + 1) * sides + (side + 1) % sides
            d = (row + 1) * sides + side
            faces.append((a, b, c, d))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def wetline_material():
    mat = bpy.data.materials.new("Aevrynd_LowerWetline_R996")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.115, 0.018, 0.012, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.20
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.48
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.34
        bsdf.inputs["Coat Roughness"].default_value = 0.12
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return mat


def build_wetline(body_tree, rig, side, center_x, material):
    points = []
    count = 29
    for index in range(count):
        t = -1.0 + 2.0 * index / (count - 1)
        x = center_x + t * 0.0096
        arc = math.sqrt(max(0.0, 1.0 - t * t))
        z = 1.4515 - 0.00405 * arc
        points.append(front_surface(body_tree, x, z, 0.00042))
    name = f"Eye_{side}_LowerWetline_R996"
    obj = make_tube(name, points, material)
    obj["aevrynd_layer"] = "eyes.lower_wetline"
    obj["aevrynd_revision"] = "v249r996"
    obj["aevrynd_source"] = "Aevrynd deterministic target-surface generation"
    obj["aevrynd_centerline_clearance_m"] = 0.00042
    obj["aevrynd_tube_radius_m"] = 0.00016
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = Matrix.Identity(4)
    return obj


def audit(scene, wetlines):
    frames, failures = {}, []
    for frame in FRAMES:
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        body = world_tree(bpy.data.objects[BODY], depsgraph)
        frame_data = {}
        for side in ("L", "R"):
            wetline = world_tree(wetlines[side], depsgraph)
            sclera = world_tree(bpy.data.objects[f"Eye_{side}_Sclera"], depsgraph)
            cornea = world_tree(bpy.data.objects[f"Eye_{side}_Cornea"], depsgraph)
            lower_lash = world_tree(bpy.data.objects[f"Eye_{side}_LowerLashes"], depsgraph)
            values = {"body": len(wetline.overlap(body)), "sclera": len(wetline.overlap(sclera)),
                      "cornea": len(wetline.overlap(cornea)), "lowerLashes": len(wetline.overlap(lower_lash))}
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
material = wetline_material()
wetlines = {side: build_wetline(body_tree, rig, side, center_x, material)
            for side, center_x in (("L", 0.02815), ("R", -0.02815))}
frames, failures = audit(scene, wetlines)
status = "PASS" if not failures else "FAIL"
AUDIT.write_text(json.dumps({"source": str(SOURCE), "model": str(OUTPUT), "frames": frames,
                             "failures": failures, "status": status}, indent=2), encoding="utf-8")
scene["aevrynd_mainline_revision"] = "v249r996-lower-wetline"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "DYNAMIC_EYE_LAYER_COLLISION_PASS_VISUAL_REVIEW_PENDING" if not failures else "EYE_LAYER_REJECTED"
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
          "layers": {side: {"object": obj.name, "vertices": len(obj.data.vertices), "polygons": len(obj.data.polygons)} for side, obj in wetlines.items()},
          "auditStatus": status, "websitePromotionApproved": False,
          "status": "DYNAMIC_COLLISION_PASS_VISUAL_REVIEW_REQUIRED" if not failures else "REJECTED"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R996_LOWER_WETLINE=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
