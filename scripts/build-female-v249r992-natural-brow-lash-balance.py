"""Balance the r991 brow underlay and lengthen lashes from pinned roots."""

import json
from collections import deque
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-brow-density-material-r991.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-natural-brow-lash-balance-r992.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-natural-brow-lash-balance-r992.build-report.json"
AUDIT = ASSETS / "female-v249-mainline-cc0-natural-brow-lash-balance-r992.clearance-audit.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r992-natural-brow-lash-balance"
BODY = "AevryndFemaleCC0Baseline_v259"
FEATURES = (
    "Brow_L", "Brow_L_Density", "Brow_R", "Brow_R_Density",
    "Eye_L_LowerLashes", "Eye_L_UpperLashes", "Eye_R_LowerLashes", "Eye_R_UpperLashes",
)
LASH_SCALE = {"Eye_L_LowerLashes": 1.10, "Eye_L_UpperLashes": 1.35,
              "Eye_R_LowerLashes": 1.10, "Eye_R_UpperLashes": 1.35}


def surface_tree(obj):
    ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = ev.to_mesh()
    verts = [ev.matrix_world @ v.co for v in mesh.vertices]
    polys = [tuple(p.vertices) for p in mesh.polygons]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys, all_triangles=False)


def signed(tree, point):
    hit = tree.find_nearest(point, 0.05)
    if hit is None or hit[1] is None:
        raise RuntimeError("No body hit")
    normal = hit[1].normalized()
    return (point - hit[0]).dot(normal)


def components(mesh):
    links = [[] for _ in mesh.vertices]
    for edge in mesh.edges:
        a, b = edge.vertices
        links[a].append(b)
        links[b].append(a)
    unseen = set(range(len(mesh.vertices)))
    groups = []
    while unseen:
        seed = unseen.pop()
        queue = deque([seed])
        group = [seed]
        while queue:
            for linked in links[queue.popleft()]:
                if linked in unseen:
                    unseen.remove(linked)
                    queue.append(linked)
                    group.append(linked)
        groups.append(group)
    return groups


def scale_fibres(obj, tree, factor):
    inverse = obj.matrix_world.inverted()
    maximum_tip_delta = 0.0
    group_count = 0
    for group in components(obj.data):
        samples = [(index, obj.matrix_world @ obj.data.vertices[index].co) for index in group]
        ranked = sorted(samples, key=lambda item: signed(tree, item[1]))
        root_samples = ranked[:max(1, min(3, len(ranked)))]
        root = sum((point for _index, point in root_samples), Vector()) / len(root_samples)
        for index, world in samples:
            target = root + (world - root) * factor
            maximum_tip_delta = max(maximum_tip_delta, (target - world).length)
            obj.data.vertices[index].co = inverse @ target
        group_count += 1
    obj.data.update()
    return group_count, maximum_tip_delta


def measure(obj, tree):
    values = [signed(tree, obj.matrix_world @ vertex.co) for vertex in obj.data.vertices]
    return {"sampleCount": len(values), "minimumSignedM": min(values), "maximumSignedM": max(values),
            "penetratingVertexCount": sum(value < -1e-7 for value in values)}


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
density_material = bpy.data.materials["Aevrynd_Brow_Density_v39"]
density_bsdf = next(node for node in density_material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
density_bsdf.inputs["Base Color"].default_value = (0.012, 0.0025, 0.0009, 1.0)
density_bsdf.inputs["Alpha"].default_value = 0.18
tree = surface_tree(bpy.data.objects[BODY])
scaling = {}
for name, factor in LASH_SCALE.items():
    count, maximum = scale_fibres(bpy.data.objects[name], tree, factor)
    scaling[name] = {"componentCount": count, "lengthScale": factor, "maximumTipDeltaM": maximum}
objects = {name: measure(bpy.data.objects[name], tree) for name in FEATURES}
failures = {name: data["penetratingVertexCount"] for name, data in objects.items() if data["penetratingVertexCount"]}
status = "PASS" if not failures else "FAIL"
AUDIT.write_text(json.dumps({"source": str(SOURCE), "model": str(OUTPUT), "frame": 1,
                             "objects": objects, "failures": failures, "status": status}, indent=2), encoding="utf-8")
scene["aevrynd_mainline_revision"] = "v249r992-natural-brow-lash-balance"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "STATIC_FACE_FEATURE_PASS_VISUAL_REVIEW_PENDING" if not failures else "STATIC_FACE_FEATURE_REJECTED"
scene["aevrynd_website_promotion"] = "forbidden pending dynamic and runtime gates"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
scene.render.resolution_x = scene.render.resolution_y = 900
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects.get("Aevrynd Review Camera") or scene.camera
scene.camera = camera
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
          "browDensityAlpha": 0.18, "lashScaling": scaling, "auditStatus": status,
          "websitePromotionApproved": False,
          "status": "STATIC_PASS_VISUAL_REVIEW_REQUIRED" if not failures else "REJECTED"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R992_NATURAL_BROW_LASH_BALANCE=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
