"""Refit buried r987/r988 brow and lash meshes to the evaluated target face."""

import json
from collections import deque
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-face-fiber-contrast-r988.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-face-feature-surface-refit-r989.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-face-feature-surface-refit-r989.build-report.json"
AUDIT = ASSETS / "female-v249-mainline-cc0-face-feature-surface-refit-r989.clearance-audit.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r989-face-feature-surface-refit"
BODY = "AevryndFemaleCC0Baseline_v259"
BROWS = ("Brow_L", "Brow_R")
DENSITY = ("Brow_L_Density", "Brow_R_Density")
LASHES = ("Eye_L_LowerLashes", "Eye_L_UpperLashes", "Eye_R_LowerLashes", "Eye_R_UpperLashes")


def surface_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


def nearest(tree, point):
    hit = tree.find_nearest(point, 0.05)
    if hit is None or hit[1] is None:
        raise RuntimeError("No target face hit within 50mm")
    return hit[0], hit[1].normalized(), (point - hit[0]).dot(hit[1].normalized())


def components(mesh):
    adjacency = [[] for _ in mesh.vertices]
    for edge in mesh.edges:
        a, b = edge.vertices
        adjacency[a].append(b)
        adjacency[b].append(a)
    unseen = set(range(len(mesh.vertices)))
    result = []
    while unseen:
        seed = unseen.pop()
        queue = deque([seed])
        group = [seed]
        while queue:
            current = queue.popleft()
            for linked in adjacency[current]:
                if linked in unseen:
                    unseen.remove(linked)
                    queue.append(linked)
                    group.append(linked)
        result.append(group)
    return result


def refit_components(obj, tree, clearance):
    inverse = obj.matrix_world.inverted()
    groups = components(obj.data)
    moved = 0
    maximum = 0.0
    for group in groups:
        samples = []
        for index in group:
            world = obj.matrix_world @ obj.data.vertices[index].co
            target, normal, signed = nearest(tree, world)
            samples.append((world, target, normal, signed))
        minimum = min(sample[3] for sample in samples)
        if minimum >= clearance:
            continue
        # Translate the whole fibre, preserving its authored length and taper.
        normal = sum((sample[2] for sample in samples), Vector()).normalized()
        amount = clearance - minimum + 0.00005
        delta = normal * amount
        for index in group:
            world = obj.matrix_world @ obj.data.vertices[index].co
            obj.data.vertices[index].co = inverse @ (world + delta)
        moved += 1
        maximum = max(maximum, delta.length)
    obj.data.update()
    return len(groups), moved, maximum


def refit_surface(obj, tree, clearance):
    inverse = obj.matrix_world.inverted()
    moved = 0
    maximum = 0.0
    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        target, normal, signed = nearest(tree, world)
        if signed < clearance:
            corrected = target + normal * clearance
            delta = corrected - world
            vertex.co = inverse @ corrected
            moved += 1
            maximum = max(maximum, delta.length)
    obj.data.update()
    return moved, maximum


def measure(obj, tree):
    values = []
    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        _target, _normal, signed = nearest(tree, world)
        values.append(signed)
    ordered = sorted(values)
    return {
        "sampleCount": len(values), "minimumSignedM": min(values),
        "medianSignedM": ordered[len(ordered) // 2], "maximumSignedM": max(values),
        "penetratingVertexCount": sum(value < -1e-7 for value in values),
    }


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
tree = surface_tree(bpy.data.objects[BODY])
operations = {}
for name in BROWS:
    count, moved, maximum = refit_components(bpy.data.objects[name], tree, 0.00035)
    operations[name] = {"componentCount": count, "movedComponentCount": moved, "maximumTranslationM": maximum}
for name in DENSITY:
    moved, maximum = refit_surface(bpy.data.objects[name], tree, 0.00022)
    operations[name] = {"movedVertexCount": moved, "maximumTranslationM": maximum}
for name in LASHES:
    count, moved, maximum = refit_components(bpy.data.objects[name], tree, 0.00018)
    operations[name] = {"componentCount": count, "movedComponentCount": moved, "maximumTranslationM": maximum}

# Rebuild the tree only when body changes; feature edits do not affect it.
audit_objects = {name: measure(bpy.data.objects[name], tree) for name in (*BROWS, *DENSITY, *LASHES)}
failures = {name: data["penetratingVertexCount"] for name, data in audit_objects.items() if data["penetratingVertexCount"]}
status = "PASS" if not failures else "FAIL"
AUDIT.write_text(json.dumps({"source": str(SOURCE), "model": str(OUTPUT), "frame": 1,
                             "objects": audit_objects, "failures": failures, "status": status}, indent=2), encoding="utf-8")
scene["aevrynd_mainline_revision"] = "v249r989-face-feature-surface-refit"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "STATIC_FACE_FEATURE_PASS_VISUAL_REVIEW_PENDING" if not failures else "STATIC_FACE_FEATURE_REJECTED"
scene["aevrynd_website_promotion"] = "forbidden pending visual, dynamic and runtime gates"
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
          "operations": operations, "auditStatus": status, "websitePromotionApproved": False,
          "status": "STATIC_PASS_VISUAL_REVIEW_REQUIRED" if not failures else "REJECTED"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R989_FACE_FEATURE_REFIT=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
