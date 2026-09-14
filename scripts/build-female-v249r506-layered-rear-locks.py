import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-sorted-tear-film-r499.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-layered-rear-locks-r506.blend"
REPORT = ASSETS / "female-v249-mainline-layered-rear-locks-r506.build-report.json"
RENDER_DIR = ASSETS / "reviews" / "v249r506-layered-rear-locks-build"
BODY = "AevryndFemaleBodyBaseV118"
SOLIDS = (BODY, "Clothing_Bandeau_v160", "Clothing_BandeauBinding_v162", "Clothing_BodyFitShorts_v135")
POINTS = 24
STRIDE = POINTS * 2
SLOTS = 4
PENETRATION_LIMIT = -0.0005
VARIANTS = (
    ("r506-layered-rear-locks", {"rear": (280, 1.85, 0.0020, 0.0075, 0.58)}),
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


def build_replacement(region, count, width_factor, outward, curve_amplitude, minimum_length_scale, rig):
    source = bpy.data.objects[f"AevryndFemaleRuntimeCards_{region}_R467"]
    selected = farthest_cards(source, count)
    vertices, faces, source_vertex_indices = [], [], []
    for output_card, source_card in enumerate(selected):
        centers = [center(source, source_card, row) for row in range(POINTS)]
        root = centers[0]
        lock_group = int(round(root.x / 0.014))
        group_wave = 0.5 + 0.5 * math.sin(lock_group * 1.731 + root.y * 19.0)
        centers = resample_centers(centers, minimum_length_scale + (0.98 - minimum_length_scale) * group_wave)
        for row in range(POINTS):
            t = row / (POINTS - 1)
            base = source_card * STRIDE + row * 2
            left = source.data.vertices[base].co.copy()
            right = source.data.vertices[base + 1].co.copy()
            card_center = centers[row]
            half = (right - left) * 0.5
            grow = smoothstep(t / 0.16)
            taper = 1.0 - 0.76 * smoothstep((t - 0.70) / 0.30)
            width = (0.72 + (width_factor - 0.72) * grow) * taper
            radial = Vector((card_center.x, card_center.y + 0.012, 0.0))
            if radial.length < 1e-8:
                radial = Vector((0.0, -1.0, 0.0))
            radial.normalize()
            lateral = Vector((-radial.y, radial.x, 0.0))
            phase = lock_group * 1.319 + (source_card % 7) * 0.11
            surface_profile = math.sin(math.pi * t) ** 2
            lock_curve = math.sin(math.pi * t) * math.sin(math.pi * 1.15 * t + phase)
            tail_break = smoothstep((t - 0.55) / 0.45) * math.sin(lock_group * 2.17 + 0.4)
            offset = radial * outward * surface_profile + lateral * (curve_amplitude * lock_curve + 0.0035 * tail_break)
            vertices.extend((card_center - half * width + offset, card_center + half * width + offset))
            source_vertex_indices.extend((base, base + 1))
        output_base = output_card * STRIDE
        for row in range(POINTS - 1):
            a = output_base + row * 2
            faces.append((a, a + 1, a + 3, a + 2))
    mesh = bpy.data.meshes.new(f"AevryndFemaleRuntimeLayeredLocks_{region}_R506_Data")
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
            u = (slot + (0.02 if side == 0 else 0.98)) / SLOTS
            uv.data[loop_index].uv = (u, row / (POINTS - 1))
    uv.active_render = True
    obj = bpy.data.objects.new(f"AevryndFemaleRuntimeLayeredLocks_{region}_R506", mesh)
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
    obj["aevrynd_layer"] = f"hair.runtime_layered_locks.{region}.dynamic.alpha"
    obj["aevrynd_revision"] = "v249r506-layered-rear-locks"
    obj["aevrynd_source"] = source.name
    obj["aevrynd_card_count"] = len(selected)
    obj["aevrynd_width_factor"] = width_factor
    obj["aevrynd_outward_m"] = outward
    obj["aevrynd_curve_amplitude_m"] = curve_amplitude
    obj["aevrynd_minimum_length_scale"] = minimum_length_scale
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
    layers = [build_replacement(region, *values, rig) for region, values in configuration.items()]
    source_rear = bpy.data.objects["AevryndFemaleRuntimeCards_rear_R467"]
    if layers:
        source_rear.hide_render = True
        source_rear.hide_viewport = True
        source_rear["aevrynd_replaced_by"] = layers[0].name
    snapshot = collision_snapshot(scene, layers) if layers else {}
    camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
    scene.camera = camera
    for values in (
        (1, label + "-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        (1, label + "-three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
        (1, label + "-back", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
        (1, label + "-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
        (33, label + "-motion-back", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
    ):
        render(scene, camera, *values)
    report["variants"][label] = {
        "configuration": configuration,
        "layers": {layer.name: {"cards": int(layer["aevrynd_card_count"]), "vertices": len(layer.data.vertices), "polygons": len(layer.data.polygons)} for layer in layers},
        "collision": snapshot,
        "collisionStatus": "NOT_APPLICABLE_BASELINE" if not layers else ("PASS" if collision_pass(snapshot) else "FAIL"),
    }
scene["aevrynd_mainline_revision"] = "v249r506-layered-rear-locks"
scene["aevrynd_release_state"] = "OFFLINE_TECHNICAL_CANDIDATE_REQUIRES_FORMAL_GATES"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report["output"] = str(OUTPUT)
report["selectedStudy"] = "r505 d-280-layered-locks"
report["rearCardCountBefore"] = 480
report["rearCardCountAfter"] = 280
report["rearCardReductionPercent"] = 41.66666666666667
report["ownedAssetOnly"] = True
report["websitePromotionApproved"] = False
report["status"] = "BUILD_COMPLETE_FORMAL_GATES_REQUIRED"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R506_LAYERED_REAR_LOCKS=" + json.dumps({"output": str(OUTPUT), "collision": {label: value["collisionStatus"] for label, value in report["variants"].items()}}, sort_keys=True))
