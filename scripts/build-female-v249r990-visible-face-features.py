"""Enable the refitted face fibres and finish residual lash clearance."""

import json
from collections import deque
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-face-feature-surface-refit-r989.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-visible-face-features-r990.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-visible-face-features-r990.build-report.json"
AUDIT = ASSETS / "female-v249-mainline-cc0-visible-face-features-r990.clearance-audit.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r990-visible-face-features"
BODY = "AevryndFemaleCC0Baseline_v259"
FEATURES = (
    "Brow_L", "Brow_L_Density", "Brow_R", "Brow_R_Density",
    "Eye_L_LowerLashes", "Eye_L_UpperLashes",
    "Eye_R_LowerLashes", "Eye_R_UpperLashes",
)
LASHES = ("Eye_L_LowerLashes", "Eye_L_UpperLashes", "Eye_R_LowerLashes", "Eye_R_UpperLashes")


def tree_for(obj):
    ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = ev.to_mesh()
    verts = [ev.matrix_world @ v.co for v in mesh.vertices]
    polys = [tuple(p.vertices) for p in mesh.polygons]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys, all_triangles=False)


def nearest(tree, point):
    hit = tree.find_nearest(point, 0.05)
    if hit is None or hit[1] is None:
        raise RuntimeError("No body hit")
    normal = hit[1].normalized()
    return normal, (point - hit[0]).dot(normal)


def groups(mesh):
    links = [[] for _ in mesh.vertices]
    for edge in mesh.edges:
        a, b = edge.vertices
        links[a].append(b)
        links[b].append(a)
    unseen = set(range(len(mesh.vertices)))
    result = []
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
        result.append(group)
    return result


def finish_components(obj, tree, clearance=0.00018):
    inv = obj.matrix_world.inverted()
    moved = 0
    maximum = 0.0
    for _pass in range(3):
        pass_moved = 0
        for group in groups(obj.data):
            samples = []
            for index in group:
                world = obj.matrix_world @ obj.data.vertices[index].co
                normal, signed = nearest(tree, world)
                samples.append((normal, signed))
            minimum = min(signed for _normal, signed in samples)
            if minimum >= clearance:
                continue
            normal = sum((normal for normal, _signed in samples), Vector()).normalized()
            delta = normal * (clearance - minimum + 0.00004)
            for index in group:
                world = obj.matrix_world @ obj.data.vertices[index].co
                obj.data.vertices[index].co = inv @ (world + delta)
            moved += 1
            pass_moved += 1
            maximum = max(maximum, delta.length)
        obj.data.update()
        if not pass_moved:
            break
    return moved, maximum


def measure(obj, tree):
    values = []
    for vertex in obj.data.vertices:
        _normal, signed = nearest(tree, obj.matrix_world @ vertex.co)
        values.append(signed)
    return {"sampleCount": len(values), "minimumSignedM": min(values),
            "maximumSignedM": max(values), "penetratingVertexCount": sum(v < -1e-7 for v in values)}


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
tree = tree_for(bpy.data.objects[BODY])
visibility = {}
for name in FEATURES:
    obj = bpy.data.objects[name]
    visibility[name] = {"wasHideRender": obj.hide_render, "wasHideViewport": obj.hide_viewport}
    obj.hide_render = False
    obj.hide_viewport = False

repairs = {}
for name in LASHES:
    moved, maximum = finish_components(bpy.data.objects[name], tree)
    repairs[name] = {"movedComponentOperations": moved, "maximumTranslationM": maximum}

objects = {name: measure(bpy.data.objects[name], tree) for name in FEATURES}
failures = {name: data["penetratingVertexCount"] for name, data in objects.items() if data["penetratingVertexCount"]}
status = "PASS" if not failures else "FAIL"
AUDIT.write_text(json.dumps({"source": str(SOURCE), "model": str(OUTPUT), "frame": 1,
                             "visibility": {name: {"hideRender": bpy.data.objects[name].hide_render,
                                                   "hideViewport": bpy.data.objects[name].hide_viewport} for name in FEATURES},
                             "objects": objects, "failures": failures, "status": status}, indent=2), encoding="utf-8")
scene["aevrynd_mainline_revision"] = "v249r990-visible-face-features"
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
          "previousVisibility": visibility, "lashRepairs": repairs, "auditStatus": status,
          "websitePromotionApproved": False,
          "status": "STATIC_PASS_VISUAL_REVIEW_REQUIRED" if not failures else "REJECTED"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R990_VISIBLE_FACE_FEATURES=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
