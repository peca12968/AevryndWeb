import json
import math
from collections import deque
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r212-natural-brow-flow-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-natural-brow-flow-r212.sweep-report.json"
BROWS = ("Brow_L", "Brow_R")
VARIANTS = (("a-control", 0.0), ("b-flow", 0.55), ("c-clustered", 0.80), ("d-authored", 1.0))


def components(mesh):
    adjacency = [set() for _ in mesh.vertices]
    for edge in mesh.edges:
        first, second = edge.vertices
        adjacency[first].add(second)
        adjacency[second].add(first)
    unseen = set(range(len(mesh.vertices)))
    result = []
    while unseen:
        seed = min(unseen)
        queue = deque([seed])
        unseen.remove(seed)
        group = []
        while queue:
            current = queue.popleft()
            group.append(current)
            for neighbor in adjacency[current]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    queue.append(neighbor)
        result.append(sorted(group))
    return result


def root_tip(obj, indices):
    points = [obj.matrix_world @ obj.data.vertices[index].co for index in indices]
    ordered = sorted(points, key=lambda point: point.y, reverse=True)
    root = sum(ordered[:3], Vector()) / 3.0
    tip = sum(ordered[-3:], Vector()) / 3.0
    return root, tip


def hash_signed(value):
    raw = math.sin(value * 12.9898 + 78.233) * 43758.5453
    return 2.0 * (raw - math.floor(raw)) - 1.0


def desired_direction(side_sign, t, group_index, member_index):
    # Medial hairs rise, body hairs sweep laterally, and the tail settles.
    x = 0.18 + 0.82 * t
    z = 0.92 * (1.0 - t) - 0.12 * t
    group_jitter = 0.10 * hash_signed(group_index + (17 if side_sign < 0 else 0))
    member_jitter = (-0.045, 0.020, -0.018, 0.042)[member_index % 4]
    z += group_jitter + member_jitter
    y = -0.34 - 0.20 * math.sin(math.pi * t)
    return Vector((side_sign * x, y, z)).normalized()


def target_length_mm(t, group_index):
    base = 4.7 + 0.8 * math.sin(math.pi * min(1.0, t * 1.10)) - 1.2 * max(0.0, (t - 0.72) / 0.28)
    return base + 0.22 * hash_signed(group_index + 31)


def reshape_brow(obj, strength):
    obj.data = obj.data.copy()
    inverse = obj.matrix_world.inverted()
    groups = components(obj.data)
    records = []
    for indices in groups:
        root, tip = root_tip(obj, indices)
        records.append({"indices": indices, "root": root, "tip": tip})
    records.sort(key=lambda item: abs(item["root"].x))
    x_values = [abs(item["root"].x) for item in records]
    x_min, x_max = min(x_values), max(x_values)
    side_sign = 1.0 if sum(item["root"].x for item in records) > 0.0 else -1.0
    changed = 0
    before_lengths = []
    after_lengths = []
    for rank, item in enumerate(records):
        root, tip = item["root"], item["tip"]
        current = tip - root
        length = current.length
        if length <= 1e-8:
            continue
        current_direction = current.normalized()
        t = (abs(root.x) - x_min) / max(1e-8, x_max - x_min)
        group_index, member_index = divmod(rank, 4)
        authored = desired_direction(side_sign, t, group_index, member_index)
        blended = current_direction.lerp(authored, strength).normalized()
        quaternion = current_direction.rotation_difference(blended)
        target_length = target_length_mm(t, group_index) / 1000.0
        axial_scale = (1.0 - strength) + strength * (target_length / length)
        before_lengths.append(length * 1000.0)
        after_lengths.append(length * axial_scale * 1000.0)
        for index in item["indices"]:
            world = obj.matrix_world @ obj.data.vertices[index].co
            relative = world - root
            axial = current_direction * relative.dot(current_direction)
            radial = relative - axial
            world = root + quaternion @ (axial * axial_scale + radial)
            obj.data.vertices[index].co = inverse @ world
            changed += 1
    obj.data.update()
    return {
        "fibers": len(records),
        "verticesChanged": changed,
        "beforeLengthMm": {"min": min(before_lengths), "mean": sum(before_lengths) / len(before_lengths), "max": max(before_lengths)},
        "afterLengthMm": {"min": min(after_lengths), "mean": sum(after_lengths) / len(after_lengths), "max": max(after_lengths)},
        "clusterSize": 4,
        "rootAnchorsMoved": 0,
    }


def set_brow_alpha(value):
    changed = []
    for name in ("Aevrynd_Brow_Hair_v39_Dark", "Aevrynd_Brow_Hair_v39_Warm"):
        material = bpy.data.materials.get(name)
        if not material or not material.use_nodes:
            continue
        for node in material.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED" and "Alpha" in node.inputs:
                node.inputs["Alpha"].default_value = value
                changed.append(name)
                break
    return sorted(set(changed))


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, filename, location, target, lens, size):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "variants": {}, "status": "VISUAL_SELECTION_PENDING"}
for label, strength in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    metrics = {"strength": strength}
    if strength:
        metrics["brows"] = {name: reshape_brow(bpy.data.objects[name], strength) for name in BROWS}
        metrics["fiberMaterialAlpha"] = 0.68
        metrics["materialsChanged"] = set_brow_alpha(0.68)
    camera = bpy.data.objects["Aevrynd Review Camera"]
    views = (
        ("01-brows-front", (0.0, -0.445, 1.638), (0.0, -0.076, 1.638), 132, (1280, 760)),
        ("02-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000)),
        ("03-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88, (1000, 1000)),
        ("04-brow-three-quarter", (0.225, -0.390, 1.650), (0.018, -0.080, 1.638), 138, (1100, 900)),
    )
    for view_name, location, target, lens, size in views:
        render(camera, f"{label}-{view_name}.png", location, target, lens, size)
    report["variants"][label] = metrics
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R212_NATURAL_BROW_FLOW=" + json.dumps(report, sort_keys=True))
