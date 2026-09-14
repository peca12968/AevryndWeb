import json
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-sorted-tear-film-r499.blend"
REPORT = ASSETS / "female-v249-mainline-upper-lash-tip-grouping-r501.study.json"
RENDER_DIR = ASSETS / "reviews" / "v249r501-upper-lash-tip-grouping-sweep"
BODY = "AevryndFemaleBodyBaseV118"
VARIANTS = (
    ("a-r499-current", None),
    ("b-paired", {"minimumGroup": 2, "maximumGroup": 3, "convergence": 0.50, "jitterM": 0.00010}),
    ("c-natural-macro", {"minimumGroup": 2, "maximumGroup": 4, "convergence": 0.70, "jitterM": 0.00017}),
    ("d-strong-macro", {"minimumGroup": 3, "maximumGroup": 4, "convergence": 0.86, "jitterM": 0.00025}),
)


def geometry(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return points, faces


def tree(obj, depsgraph):
    points, faces = geometry(obj, depsgraph)
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def centroid(obj, fiber, row):
    return sum((obj.data.vertices[fiber * 20 + row * 4 + side].co for side in range(4)), Vector()) / 4.0


def groups(indices, rng, minimum, maximum):
    result = []
    cursor = 0
    while cursor < len(indices):
        remaining = len(indices) - cursor
        size = min(remaining, rng.randint(minimum, maximum))
        if remaining - size == 1 and size < maximum:
            size += 1
        result.append(indices[cursor:cursor + size])
        cursor += size
    return result


def regroup(obj, side, settings, seed):
    if len(obj.data.vertices) != 760 or len(obj.data.polygons) != 646:
        raise RuntimeError(f"Unexpected inherited upper-lash topology on {obj.name}")
    rng = random.Random(seed)
    ordered = sorted(range(38), key=lambda fiber: centroid(obj, fiber, 0).x)
    clusters = groups(ordered, rng, settings["minimumGroup"], settings["maximumGroup"])
    movements = []
    for cluster_index, cluster in enumerate(clusters):
        shared_tip = sum((centroid(obj, fiber, 4) for fiber in cluster), Vector()) / len(cluster)
        alternating = -1.0 if cluster_index % 2 == 0 else 1.0
        shared_tip += Vector((
            alternating * rng.uniform(0.25, 1.0) * settings["jitterM"],
            rng.uniform(-0.45, 0.45) * settings["jitterM"],
            alternating * rng.uniform(0.30, 1.0) * settings["jitterM"],
        ))
        for local_index, fiber in enumerate(cluster):
            old_tip = centroid(obj, fiber, 4)
            centered = local_index - (len(cluster) - 1) * 0.5
            dispersion = Vector((
                centered * rng.uniform(0.08, 0.20) * settings["jitterM"],
                rng.uniform(-0.08, 0.08) * settings["jitterM"],
                centered * rng.uniform(-0.10, 0.10) * settings["jitterM"],
            ))
            desired_tip = old_tip.lerp(shared_tip, settings["convergence"]) + dispersion
            delta = desired_tip - old_tip
            movements.append(delta.length)
            for row in range(1, 5):
                progress = (row / 4.0) ** 1.55
                for vertex_side in range(4):
                    obj.data.vertices[fiber * 20 + row * 4 + vertex_side].co += delta * progress
    obj.data.update()
    obj["aevrynd_revision"] = "v249r501-upper-lash-tip-grouping"
    obj["aevrynd_group_count"] = len(clusters)
    obj["aevrynd_group_sizes"] = [len(cluster) for cluster in clusters]
    obj["aevrynd_tip_convergence"] = settings["convergence"]
    obj["aevrynd_tip_max_movement_m"] = max(movements)
    obj["aevrynd_tip_mean_movement_m"] = sum(movements) / len(movements)
    obj["aevrynd_ownership"] = "Aevrynd deterministic regrouping of owned geometry"
    return {
        "groups": len(clusters),
        "groupSizes": [len(cluster) for cluster in clusters],
        "maximumTipMovementM": max(movements),
        "meanTipMovementM": sum(movements) / len(movements),
    }


def collision_snapshot(scene):
    result = {}
    for frame in (1, 20):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        body_tree = tree(bpy.data.objects[BODY], depsgraph)
        frame_report = {}
        for side in ("L", "R"):
            upper = tree(bpy.data.objects[f"Eye_{side}_UpperLashes"], depsgraph)
            colliders = {
                "body": body_tree,
                "cornea": tree(bpy.data.objects[f"Eye_{side}_Cornea"], depsgraph),
                "sclera": tree(bpy.data.objects[f"Eye_{side}_Sclera"], depsgraph),
                "tear": tree(bpy.data.objects[f"Eye_{side}_TearMeniscus"], depsgraph),
                "caruncle": tree(bpy.data.objects[f"Eye_{side}_Caruncle"], depsgraph),
                "lower": tree(bpy.data.objects[f"Eye_{side}_LowerLashes"], depsgraph),
            }
            frame_report[side] = {label: len(upper.overlap(value)) for label, value in colliders.items()}
        result[str(frame)] = frame_report
    return result


def collision_pass(snapshot):
    return all(count == 0 for frame in snapshot.values() for side in frame.values() for count in side.values())


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, name, location, target, lens, size):
    scene.frame_set(1)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


RENDER_DIR.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "variants": {}, "renderDirectory": str(RENDER_DIR)}
for variant_index, (label, settings) in enumerate(VARIANTS):
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.render.image_settings.file_format = "PNG"
    layer_report, snapshot = {}, None
    if settings is not None:
        for side_index, side in enumerate(("L", "R")):
            layer_report[side] = regroup(bpy.data.objects[f"Eye_{side}_UpperLashes"], side, settings, 50100 + variant_index * 100 + side_index * 10)
        snapshot = collision_snapshot(scene)
    camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
    scene.camera = camera
    render(scene, camera, label + "-eye-close", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700))
    render(scene, camera, label + "-lash-oblique", (0.18, -0.34, 1.616), (0.033, -0.113, 1.609), 125, (1200, 900))
    render(scene, camera, label + "-three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84, (1000, 1000))
    report["variants"][label] = {
        "settings": settings,
        "layers": layer_report,
        "collision": snapshot,
        "collisionStatus": "NOT_APPLICABLE_BASELINE" if snapshot is None else ("PASS" if collision_pass(snapshot) else "FAIL"),
    }
report["visualAssessment"] = {"status": "REJECTED", "reason": "Tip grouping produces black loops, stitches and hooks along the lid margin.", "promotion": None}
report["status"] = "REJECTED_VISUAL_GATE"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R501_UPPER_LASH_GROUPING=" + json.dumps({label: value["collisionStatus"] for label, value in report["variants"].items()}, sort_keys=True))
