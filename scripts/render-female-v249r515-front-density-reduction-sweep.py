import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-lighter-neutral-skin-r510.blend"
REPORT = ASSETS / "female-v249-mainline-front-density-reduction-r515.study.json"
RENDER_DIR = ASSETS / "reviews" / "v249r515-front-density-reduction-sweep"
BODY = "AevryndFemaleBodyBaseV118"
SOLIDS = (BODY, "Clothing_Bandeau_v160", "Clothing_BandeauBinding_v162", "Clothing_BodyFitShorts_v135")
POINTS = 24
STRIDE = POINTS * 2
SLOTS = 4
PENETRATION_LIMIT = -0.0005
VARIANTS = (
    ("a-r510-current", None),
    ("b-280-exact-subset", (280, 1.00, 0.0000, 0.0000, 1.00, 1.00, 0.0000)),
    ("c-320-exact-subset", (320, 1.00, 0.0000, 0.0000, 1.00, 1.00, 0.0000)),
    ("d-360-exact-subset", (360, 1.00, 0.0000, 0.0000, 1.00, 1.00, 0.0000)),
)


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def center(source, card, row):
    base = card * STRIDE + row * 2
    return (source.data.vertices[base].co + source.data.vertices[base + 1].co) * 0.5


def feature(source, card):
    root = center(source, card, 0)
    middle = center(source, card, POINTS // 2)
    tail = center(source, card, POINTS - 1)
    return (root.x * 5.0, root.y * 5.0, middle.x * 2.0, middle.y * 2.0, tail.x, tail.y, tail.z)


def farthest_cards(source, count):
    cards = int(source.get("aevrynd_card_count", 0))
    if count >= cards:
        return list(range(cards))
    features = [feature(source, card) for card in range(cards)]
    chosen = [min(range(cards), key=lambda card: features[card][0])]
    distances = [sum((a - b) ** 2 for a, b in zip(value, features[chosen[0]])) for value in features]
    while len(chosen) < count:
        candidate = max(range(cards), key=lambda card: distances[card] if card not in chosen else -1.0)
        chosen.append(candidate)
        selected = features[candidate]
        for card, value in enumerate(features):
            distance = sum((a - b) ** 2 for a, b in zip(value, selected))
            if distance < distances[card]:
                distances[card] = distance
    return chosen


def resample_centers(centers, scale):
    result = []
    for row in range(POINTS):
        position = (POINTS - 1) * (row / (POINTS - 1)) * scale
        low = int(math.floor(position))
        high = min(POINTS - 1, low + 1)
        result.append(centers[low].lerp(centers[high], position - low))
    return result


def build_replacement(count, width_factor, outward, curve_amplitude, minimum_length_scale, center_root_floor, root_cross, rig):
    source = bpy.data.objects["AevryndFemaleRuntimeCards_front_R467"]
    selected = farthest_cards(source, count)
    vertices, faces, source_vertex_indices = [], [], []
    for output_card, source_card in enumerate(selected):
        centers = [center(source, source_card, row) for row in range(POINTS)]
        root = centers[0]
        lock_group = int(round(root.x / 0.012))
        group_wave = 0.5 + 0.5 * math.sin(lock_group * 1.731 + root.y * 23.0)
        centers = centers
        for row in range(POINTS):
            t = row / (POINTS - 1)
            base = source_card * STRIDE + row * 2
            left = source.data.vertices[base].co.copy()
            right = source.data.vertices[base + 1].co.copy()
            card_center = centers[row]
            half = (right - left) * 0.5
            grow = smoothstep(t / 0.18)
            taper = 1.0 - 0.78 * smoothstep((t - 0.68) / 0.32)
            near_part = smoothstep((0.028 - abs(root.x)) / 0.018)
            root_floor = 0.72 + (center_root_floor - 0.72) * near_part
            width = 1.0
            radial = Vector((card_center.x, card_center.y + 0.012, 0.0))
            if radial.length < 1e-8:
                radial = Vector((0.0, -1.0, 0.0))
            radial.normalize()
            lateral = Vector((-radial.y, radial.x, 0.0))
            phase = lock_group * 1.319 + (source_card % 7) * 0.37
            surface_profile = math.sin(math.pi * t) ** 2
            lock_curve = math.sin(math.pi * t) * math.sin(math.pi * 1.20 * t + phase)
            tail_break = smoothstep((t - 0.50) / 0.50) * math.sin(lock_group * 2.17 + 0.4)
            alternating = -1.0 if ((source_card + lock_group) & 1) else 1.0
            cross_profile = near_part * alternating * root_cross * math.sin(math.pi * min(1.0, t / 0.34))
            offset = Vector((0.0, 0.0, 0.0))
            vertices.extend((card_center - half * width + offset, card_center + half * width + offset))
            source_vertex_indices.extend((base, base + 1))
        output_base = output_card * STRIDE
        for row in range(POINTS - 1):
            a = output_base + row * 2
            faces.append((a, a + 1, a + 3, a + 2))
    mesh = bpy.data.meshes.new("AevryndFemaleRuntimeReducedCards_front_R515_Data")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(source.active_material)
    uv = mesh.uv_layers.new(name="AevryndRuntimeHairLayeredLockUV")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            vertex_index = mesh.loops[loop_index].vertex_index
            local = vertex_index % STRIDE
            row = local // 2
            side = local % 2
            slot = 2 + ((vertex_index // STRIDE) % 2)
            uv.data[loop_index].uv = ((slot + (0.02 if side == 0 else 0.98)) / SLOTS, row / (POINTS - 1))
    uv.active_render = True
    obj = bpy.data.objects.new("AevryndFemaleRuntimeReducedCards_front_R515", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = source.parent
    obj.matrix_parent_inverse = source.matrix_parent_inverse.copy()
    for source_group in source.vertex_groups:
        obj.vertex_groups.new(name=source_group.name)
    for output_index, source_index in enumerate(source_vertex_indices):
        for membership in source.data.vertices[source_index].groups:
            group_name = source.vertex_groups[membership.group].name
            obj.vertex_groups[group_name].add([output_index], membership.weight, "REPLACE")
    modifier = obj.modifiers.new("Aevrynd Runtime Hair Layered Lock Armature", "ARMATURE")
    modifier.object = rig
    obj["aevrynd_layer"] = "hair.runtime_reduced_cards.front.dynamic.alpha"
    obj["aevrynd_revision"] = "v249r515-front-density-reduction-study"
    obj["aevrynd_source"] = source.name
    obj["aevrynd_card_count"] = len(selected)
    obj["aevrynd_width_factor"] = width_factor
    obj["aevrynd_outward_m"] = outward
    obj["aevrynd_curve_amplitude_m"] = curve_amplitude
    obj["aevrynd_minimum_length_scale"] = minimum_length_scale
    obj["aevrynd_center_root_floor"] = center_root_floor
    obj["aevrynd_root_cross_m"] = root_cross
    obj["aevrynd_ownership"] = "Aevrynd derived from owned runtime cards and owned atlas"
    return obj


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


def collision_snapshot(scene, layers):
    result = {}
    for frame in (1, 20, 33, 61):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        solid_trees = {name: tree(bpy.data.objects[name], depsgraph) for name in SOLIDS}
        result[str(frame)] = {}
        for layer in layers:
            evaluated = layer.evaluated_get(depsgraph)
            points = [evaluated.matrix_world @ vertex.co for vertex in evaluated.data.vertices]
            layer_report = {}
            for solid, solid_tree in solid_trees.items():
                signed = []
                for point in points:
                    hit = solid_tree.find_nearest(point, 0.025)
                    if hit is not None and hit[1] is not None:
                        signed.append((point - hit[0]).dot(hit[1].normalized()))
                layer_report[solid] = {
                    "nearSamples": len(signed),
                    "minimumSignedM": min(signed) if signed else None,
                    "penetratingVertices": sum(value < PENETRATION_LIMIT for value in signed),
                }
            result[str(frame)][layer.name] = layer_report
    return result


def collision_pass(snapshot):
    return all(
        value["penetratingVertices"] == 0
        for frame in snapshot.values()
        for layer in frame.values()
        for value in layer.values()
    )


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, frame, name, location, target, lens):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


RENDER_DIR.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "variants": {}, "renderDirectory": str(RENDER_DIR)}
for label, configuration in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.render.image_settings.file_format = "PNG"
    rig = bpy.data.objects["AevryndFemaleRig"]
    layers = [build_replacement(*configuration, rig)] if configuration else []
    source_front = bpy.data.objects["AevryndFemaleRuntimeCards_front_R467"]
    if layers:
        source_front.hide_render = True
        source_front.hide_viewport = True
    snapshot = collision_snapshot(scene, layers) if layers else {}
    camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
    scene.camera = camera
    for values in (
        (1, label + "-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        (1, label + "-three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
        (1, label + "-profile", (0.72, -0.03, 1.61), (0.0, 0.0, 1.58), 88),
        (1, label + "-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
        (33, label + "-motion-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ):
        render(scene, camera, *values)
    report["variants"][label] = {
        "configuration": configuration,
        "layers": {layer.name: {"cards": int(layer["aevrynd_card_count"]), "vertices": len(layer.data.vertices), "polygons": len(layer.data.polygons)} for layer in layers},
        "collision": snapshot,
        "collisionStatus": "NOT_APPLICABLE_BASELINE" if not layers else ("PASS" if collision_pass(snapshot) else "FAIL"),
    }
report["visualAssessment"] = {
    "status": "PENDING_STRICT_CONTACT_SHEET_REVIEW",
    "requirements": [
        "front silhouette must become grouped and uneven",
        "front and side must show broad readable locks instead of a continuous curtain",
        "face and skin exposure must not become darker",
        "no hooks, loops, bald gaps or collision failures",
    ],
}
report["status"] = "STUDY_COMPLETE_PENDING_VISUAL_SELECTION"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R515_FRONT_DENSITY_REDUCTION=" + json.dumps({label: value["collisionStatus"] for label, value in report["variants"].items()}, sort_keys=True))


