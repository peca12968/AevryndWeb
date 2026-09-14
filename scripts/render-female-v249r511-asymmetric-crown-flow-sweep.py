import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-lighter-neutral-skin-r510.blend"
REPORT = ASSETS / "female-v249-mainline-asymmetric-crown-flow-r511.study.json"
RENDER_DIR = ASSETS / "reviews" / "v249r511-asymmetric-crown-flow-sweep"
BODY = "AevryndFemaleBodyBaseV118"
SOLIDS = (BODY, "Clothing_Bandeau_v160", "Clothing_BandeauBinding_v162", "Clothing_BodyFitShorts_v135")
POINTS = 24
STRIDE = POINTS * 2
SLOTS = 4
PENETRATION_LIMIT = -0.0005
VARIANTS = (
    ("a-r510-current", None),
    ("b-420-subtle-families", (420, 0.0040, 0.0015, 0.0020, 0.0020)),
    ("c-420-natural-families", (420, 0.0070, 0.0025, 0.0035, 0.0032)),
    ("d-420-strong-families", (420, 0.0100, 0.0035, 0.0050, 0.0045)),
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


def build_replacement(count, lateral_amplitude, radial_outward, crown_lift, part_cross, rig):
    source = bpy.data.objects["AevryndFemaleRuntimeCards_crown_R467"]
    selected = farthest_cards(source, count)
    vertices, faces, source_vertex_indices = [], [], []
    for output_card, source_card in enumerate(selected):
        centers = [center(source, source_card, row) for row in range(POINTS)]
        root = centers[0]
        side = -1.0 if root.x < 0.0 else 1.0
        sector = int(math.floor((root.x + 0.09) / 0.028))
        depth_band = int(math.floor((root.y + 0.02) / 0.018))
        family = sector + depth_band * 7
        family_phase = family * 1.731 + side * 0.43
        family_strength = 0.55 + 0.45 * (0.5 + 0.5 * math.sin(family * 2.17 + 0.8))
        family_direction = 0.42 * side + 0.58 * math.sin(family_phase)
        near_part = smoothstep((0.030 - abs(root.x)) / 0.022)
        crown_weight = smoothstep((root.z - 1.655) / 0.055)
        for row in range(POINTS):
            t = row / (POINTS - 1)
            base = source_card * STRIDE + row * 2
            left = source.data.vertices[base].co.copy()
            right = source.data.vertices[base + 1].co.copy()
            card_center = centers[row]
            half = (right - left) * 0.5
            # Roots and tails remain fixed. All new volume and direction lives in
            # the upper/middle guide span, preserving the accepted collision ends.
            body_profile = math.sin(math.pi * t) ** 1.35
            tail_guard = 1.0 - smoothstep((t - 0.68) / 0.22)
            flow_profile = body_profile * tail_guard
            root_profile = math.sin(math.pi * min(1.0, t / 0.30)) * (1.0 - smoothstep((t - 0.28) / 0.16))
            radial3 = Vector((card_center.x, card_center.y + 0.002, card_center.z - 1.60))
            if radial3.length < 1e-8:
                radial3 = Vector((0.0, 0.0, 1.0))
            radial3.normalize()
            horizontal = Vector((radial3.x, radial3.y, 0.0))
            if horizontal.length < 1e-8:
                horizontal = Vector((side, 0.0, 0.0))
            horizontal.normalize()
            tangent = Vector((-horizontal.y, horizontal.x, 0.0))
            group_wave = math.sin(math.pi * 1.18 * t + family_phase) * flow_profile
            offset = (
                tangent * lateral_amplitude * family_strength * family_direction * group_wave
                + radial3 * radial_outward * flow_profile
                + Vector((0.0, 0.0, crown_lift * crown_weight * flow_profile))
                + Vector((-side * part_cross * near_part * root_profile, 0.0, 0.0))
            )
            vertices.extend((card_center - half + offset, card_center + half + offset))
            source_vertex_indices.extend((base, base + 1))
        output_base = output_card * STRIDE
        for row in range(POINTS - 1):
            a = output_base + row * 2
            faces.append((a, a + 1, a + 3, a + 2))
    # All r511 variants keep all 420 cards. Copying the authored object preserves
    # vertex-group storage, modifier settings, UVs and transforms byte-for-byte;
    # only the requested root vertices change.
    obj = source.copy()
    obj.data = source.data.copy()
    obj.name = "AevryndFemaleRuntimeAsymmetricLocks_crown_R511"
    obj.data.name = "AevryndFemaleRuntimeAsymmetricLocks_crown_R511_Data"
    bpy.context.scene.collection.objects.link(obj)
    for index, position in enumerate(vertices):
        obj.data.vertices[index].co = position
    obj["aevrynd_layer"] = "hair.runtime_asymmetric_locks.crown.dynamic.alpha"
    obj["aevrynd_revision"] = "v249r511-asymmetric-crown-flow-study"
    obj["aevrynd_source"] = source.name
    obj["aevrynd_card_count"] = len(selected)
    obj["aevrynd_lateral_amplitude_m"] = lateral_amplitude
    obj["aevrynd_radial_outward_m"] = radial_outward
    obj["aevrynd_crown_lift_m"] = crown_lift
    obj["aevrynd_part_cross_m"] = part_cross
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
    source_crown = bpy.data.objects["AevryndFemaleRuntimeCards_crown_R467"]
    if layers:
        source_crown.hide_render = True
        source_crown.hide_viewport = True
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
        "part line must become narrower and less ruler-straight",
        "large coherent lock families must replace the parallel-sheet rhythm",
        "roots and tails must remain fixed while the upper-middle span gains asymmetry and lift",
        "face and skin exposure must not become darker",
        "no hooks, loops, bald gaps or collision failures",
    ],
}
report["status"] = "STUDY_COMPLETE_PENDING_VISUAL_SELECTION"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R511_ASYMMETRIC_CROWN_FLOW=" + json.dumps({label: value["collisionStatus"] for label, value in report["variants"].items()}, sort_keys=True))


