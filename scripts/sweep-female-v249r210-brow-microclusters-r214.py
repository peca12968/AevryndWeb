import json
import math
from collections import deque
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r214-brow-microcluster-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-brow-microclusters-r214.sweep-report.json"
BROWS = ("Brow_L", "Brow_R")
VARIANTS = (
    ("a-control", ()),
    ("b-soft", ((0, 0.34),)),
    ("c-balanced", ((0, 0.48),)),
    ("d-layered", ((0, 0.34), (1, 0.28))),
)


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
    return sum(ordered[:3], Vector()) / 3.0, sum(ordered[-3:], Vector()) / 3.0


def hash_signed(value):
    raw = math.sin(value * 12.9898 + 78.233) * 43758.5453
    return 2.0 * (raw - math.floor(raw)) - 1.0


def micro_material(source, name, alpha):
    material = source.copy()
    material.name = name
    if material.use_nodes:
        for node in material.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED" and "Alpha" in node.inputs:
                node.inputs["Alpha"].default_value = alpha
                break
    return material


def make_micro_layer(source, layer_index, alpha):
    obj = source.copy()
    obj.data = source.data.copy()
    obj.name = f"{source.name}_MicroCluster_R214_{layer_index + 1}"
    for collection in source.users_collection:
        collection.objects.link(obj)
    obj["aevrynd_layer"] = "face.eyebrow.microcluster"
    obj["aevrynd_revision"] = "v249r214"
    obj["aevrynd_source_layer"] = source.name
    obj["aevrynd_microcluster_index"] = layer_index
    obj["aevrynd_runtime_dependency"] = "none"
    for slot_index, slot in enumerate(obj.material_slots):
        if slot.material:
            slot.material = micro_material(slot.material, f"{slot.material.name}_Micro_R214_{layer_index + 1}", alpha)

    inverse = obj.matrix_world.inverted()
    groups = components(obj.data)
    records = []
    for indices in groups:
        root, tip = root_tip(obj, indices)
        records.append((indices, root, tip))
    records.sort(key=lambda item: abs(item[1].x))
    side_sign = 1.0 if sum(item[1].x for item in records) > 0.0 else -1.0
    maximum_root_shift = 0.0
    for rank, (indices, root, tip) in enumerate(records):
        axis = tip - root
        if axis.length <= 1e-8:
            continue
        direction = axis.normalized()
        signed = hash_signed(rank + 101 * layer_index + (37 if side_sign < 0 else 0))
        signed_b = hash_signed(rank + 211 * layer_index + (53 if side_sign < 0 else 0))
        angle = math.radians((2.4 + 1.1 * signed) * (-1.0 if (rank + layer_index) % 2 else 1.0))
        rotation = Matrix.Rotation(angle, 4, "Y")
        axial_scale = 0.84 + 0.08 * (0.5 + 0.5 * signed_b)
        radial_scale = 0.64
        shift = Vector((
            side_sign * (0.00013 + 0.00010 * signed),
            -0.00010 - 0.00004 * layer_index,
            0.00010 * signed_b + (0.00008 if layer_index else -0.00004),
        ))
        maximum_root_shift = max(maximum_root_shift, shift.length)
        for index in indices:
            world = obj.matrix_world @ obj.data.vertices[index].co
            relative = world - root
            axial = direction * relative.dot(direction)
            radial = relative - axial
            world = root + shift + rotation @ (axial * axial_scale + radial * radial_scale)
            obj.data.vertices[index].co = inverse @ world
    obj.data.update()
    return obj, {
        "fibers": len(records),
        "vertices": len(obj.data.vertices),
        "polygons": len(obj.data.polygons),
        "materialAlpha": alpha,
        "radialScale": 0.64,
        "maximumRootShiftMm": maximum_root_shift * 1000.0,
    }


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
for label, layers in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    metrics = {"microLayersPerSide": len(layers), "layers": {}}
    for layer_index, alpha in layers:
        for name in BROWS:
            obj, detail = make_micro_layer(bpy.data.objects[name], layer_index, alpha)
            metrics["layers"][obj.name] = detail
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
print("AEVRYND_V249R214_BROW_MICROCLUSTERS=" + json.dumps(report, sort_keys=True))
