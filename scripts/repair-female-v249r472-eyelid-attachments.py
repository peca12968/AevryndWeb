import json
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-integrated-eyelid-relief-r471.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-integrated-eyelid-clearance-r472.blend"
REPORT = ASSETS / "female-v249-mainline-integrated-eyelid-clearance-r472.build-report.json"
REVIEW_DIR = ASSETS / "reviews/v249r472-integrated-eyelid-clearance"
BODY = "AevryndFemaleBodyBaseV118"


def surface_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def outward(normal):
    normal = normal.normalized()
    if normal.y > 0.0:
        normal.negate()
    return normal


def components(obj):
    adjacency = defaultdict(set)
    for edge in obj.data.edges:
        first, second = edge.vertices
        adjacency[first].add(second)
        adjacency[second].add(first)
    result, unvisited = [], set(range(len(obj.data.vertices)))
    while unvisited:
        start = unvisited.pop()
        component, stack = {start}, [start]
        while stack:
            current = stack.pop()
            for neighbor in adjacency[current]:
                if neighbor not in component:
                    component.add(neighbor)
                    unvisited.discard(neighbor)
                    stack.append(neighbor)
        result.append(sorted(component))
    return result


def repair_lashes(obj, tree, clearance=0.00052, passes=5):
    inverse = obj.matrix_world.inverted()
    groups = components(obj)
    changes = []
    for pass_index in range(1, passes + 1):
        moved = 0
        maximum = 0.0
        for group in groups:
            worst = None
            for index in group:
                point = obj.matrix_world @ obj.data.vertices[index].co
                hit = tree.find_nearest(point, 0.006)
                if hit is None or hit[1] is None:
                    continue
                normal = outward(hit[1])
                signed = (point - hit[0]).dot(normal)
                if worst is None or signed < worst[0]:
                    worst = (signed, normal)
            if worst is None or worst[0] >= clearance:
                continue
            translation = worst[1] * (clearance - worst[0])
            local_translation = inverse.to_3x3() @ translation
            for index in group:
                obj.data.vertices[index].co += local_translation
            moved += 1
            maximum = max(maximum, translation.length)
        obj.data.update()
        changes.append({"pass": pass_index, "movedFibers": moved, "maximumTranslationM": maximum})
        if moved == 0:
            break
    obj["aevrynd_revision"] = "v249r472"
    obj["aevrynd_clearance_offset_mm"] = clearance * 1000.0
    obj["aevrynd_clearance_method"] = "whole-fiber translation against r471 evaluated body"
    return {"fibers": len(groups), "passes": changes}


def repair_surface(obj, tree, clearance=0.00018, passes=4):
    inverse = obj.matrix_world.inverted()
    changes = []
    for pass_index in range(1, passes + 1):
        moved = 0
        maximum = 0.0
        for vertex in obj.data.vertices:
            point = obj.matrix_world @ vertex.co
            hit = tree.find_nearest(point, 0.006)
            if hit is None or hit[1] is None:
                continue
            normal = outward(hit[1])
            signed = (point - hit[0]).dot(normal)
            if signed >= clearance:
                continue
            translation = normal * (clearance - signed)
            vertex.co += inverse.to_3x3() @ translation
            moved += 1
            maximum = max(maximum, translation.length)
        obj.data.update()
        changes.append({"pass": pass_index, "movedVertices": moved, "maximumTranslationM": maximum})
        if moved == 0:
            break
    obj["aevrynd_revision"] = "v249r472"
    obj["aevrynd_clearance_offset_mm"] = clearance * 1000.0
    obj["aevrynd_clearance_method"] = "per-vertex surface-normal projection against r471 evaluated body"
    return {"vertices": len(obj.data.vertices), "passes": changes}


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, frame, name, location, target, lens, size):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(REVIEW_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
tree = surface_tree(bpy.data.objects[BODY])
repairs = {}
for side in ("L", "R"):
    name = f"Eye_{side}_UpperLashes"
    repairs[name] = repair_lashes(bpy.data.objects[name], tree)
# R471's left tear layer already has zero body overlap. Reproject only the
# right layer that actually regressed; moving a passing wetline is unnecessary
# and can change which side of the thin lower-lid surface its vertices occupy.
name = "Eye_R_TearMeniscus"
repairs[name] = repair_surface(bpy.data.objects[name], tree)

scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
for values in (
    (1, "01-eye-close-f01", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700)),
    (1, "02-front-f01", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000)),
    (1, "03-three-quarter-f01", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84, (1000, 1000)),
    (20, "04-eye-close-f20", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700)),
):
    render(scene, camera, *values)

scene.frame_set(1)
scene["aevrynd_mainline_revision"] = "v249r472-integrated-eyelid-clearance"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "EYELID_ATTACHMENT_CLEARANCE_CANDIDATE_COLLISION_AUDIT_REQUIRED"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "repairs": repairs,
    "bodyGeometryChangedFromR471": False,
    "reviewDirectory": str(REVIEW_DIR),
    "status": "COLLISION_AUDIT_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R472_ATTACHMENT_REPAIR=" + json.dumps(report, sort_keys=True))
