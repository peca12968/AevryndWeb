"""Symmetrically relax the four r1075 commissure curvature outlier pairs."""
import hashlib
import json
import math
import struct
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-commissure-falloff-r1074-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-commissure-curvature-r1076-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1076-commissure-curvature.study.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1076-commissure-curvature"
BODY = "AevryndFemaleCC0CommissureFalloff_R1074"
ATTRIBUTE = "aevrynd_inner_rim_r1074"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
PAIRS = ((13523, 13686), (13524, 13688), (13558, 13722), (13559, 13723))
VARIANTS = (("a-control", 0.0), ("b-relax-0.15", 0.15), ("c-relax-0.30", 0.30), ("d-relax-0.45", 0.45))
SELECTED = "b-relax-0.15"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def geometry_digest(body):
    digest = hashlib.sha256()
    for block in body.data.shape_keys.key_blocks:
        digest.update(block.name.encode("utf-8"))
        for item in block.data:
            digest.update(struct.pack("<3f", item.co.x, item.co.y, item.co.z))
    return digest.hexdigest()


def weight_digest(body):
    digest = hashlib.sha256()
    for vertex in body.data.vertices:
        for group in sorted(vertex.groups, key=lambda item: item.group):
            digest.update(struct.pack("<If", group.group, group.weight))
    return digest.hexdigest()


def active_coordinates(body, smile=False):
    blocks = body.data.shape_keys.key_blocks
    coords = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute:
            continue
        value = 1.0 if block.name == SMILE_KEY and smile else (0.0 if block.name in (SMILE_KEY, OPEN_KEY) else block.value)
        if abs(value) < 1e-8:
            continue
        for index, item in enumerate(block.data):
            coords[index] += value * (item.co - block.relative_key.data[index].co)
    return coords


def adjacency(mesh):
    result = {vertex.index: set() for vertex in mesh.vertices}
    for polygon in mesh.polygons:
        vertices = list(polygon.vertices)
        for index, vertex in enumerate(vertices):
            result[vertex].update((vertices[(index - 1) % len(vertices)], vertices[(index + 1) % len(vertices)]))
    return result


def paired_deltas(body, neighbors):
    coords = active_coordinates(body)
    deltas = {}
    evidence = []
    for left, right in PAIRS:
        def surface_delta(index):
            usable = [neighbor for neighbor in neighbors[index] if (coords[neighbor] - coords[index]).length > 0.0001]
            average = sum((coords[neighbor] for neighbor in usable), Vector()) / len(usable)
            return average - coords[index], usable
        left_delta, left_neighbors = surface_delta(left)
        right_delta, right_neighbors = surface_delta(right)
        mirrored_right = Vector((-right_delta.x, right_delta.y, right_delta.z))
        shared_left = (left_delta + mirrored_right) * 0.5
        deltas[left] = shared_left
        deltas[right] = Vector((-shared_left.x, shared_left.y, shared_left.z))
        evidence.append({
            "pair": [left, right],
            "leftSurfaceNeighbors": left_neighbors, "rightSurfaceNeighbors": right_neighbors,
            "leftRawDeltaMm": [float(value * 1000.0) for value in left_delta],
            "rightRawDeltaMm": [float(value * 1000.0) for value in right_delta],
            "sharedSymmetricDeltaMm": [float(value * 1000.0) for value in shared_left],
        })
    return deltas, evidence


def curvature_metrics(body, smile):
    coords = active_coordinates(body, smile)
    vertex_faces = [[] for _ in body.data.vertices]
    normals = []
    for polygon in body.data.polygons:
        vertices = list(polygon.vertices)
        origin, normal = coords[vertices[0]], Vector()
        for index in range(1, len(vertices) - 1):
            normal += (coords[vertices[index]] - origin).cross(coords[vertices[index + 1]] - origin)
        if normal.length_squared > 1e-20:
            normal.normalize()
        normals.append(normal)
        for vertex in vertices:
            vertex_faces[vertex].append(polygon.index)
    mask = body.data.attributes[ATTRIBUTE].data
    regions = {"central": [], "commissure": []}
    for vertex in body.data.vertices:
        if mask[vertex.index].value <= 0.05:
            continue
        world = body.matrix_world @ coords[vertex.index]
        region = "commissure" if abs(world.x) > 0.014 else "central"
        adjacent = [normals[index] for index in vertex_faces[vertex.index] if normals[index].length_squared > 0.5]
        if len(adjacent) < 2:
            continue
        mean = sum(adjacent, Vector()).normalized()
        regions[region].append(max(math.degrees(mean.angle(normal)) for normal in adjacent))
    result = {}
    for name, values in regions.items():
        ordered = sorted(values)
        result[name] = {
            "vertices": len(values), "meanDeg": sum(values) / len(values),
            "p95Deg": ordered[min(len(ordered) - 1, int(round((len(ordered) - 1) * 0.95)))],
            "maximumDeg": max(values),
        }
    return result


def set_factor(body, originals, deltas, factor):
    for block in body.data.shape_keys.key_blocks:
        for vertex in deltas:
            block.data[vertex].co = originals[block.name][vertex] + deltas[vertex] * factor
    body.data.update()


def set_pose(body, pose):
    keys = body.data.shape_keys.key_blocks
    keys[OPEN_KEY].value = 1.0 if pose == "open" else 0.0
    keys[SMILE_KEY].value = 1.0 if pose == "smile" else 0.0


def render(scene, label, oblique=False):
    camera = scene.camera
    camera.data.lens = 135
    camera.location = ((-0.105 if oblique else 0.0), -0.43, 1.391)
    look_at(camera, (0.0, -0.115, 1.386))
    scene.render.resolution_x, scene.render.resolution_y = 1100, 720
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
OUT.mkdir(parents=True, exist_ok=True)
for obj in scene.objects:
    name = obj.name.lower()
    if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
        if not any(token in name for token in ("brow", "lash")):
            obj.hide_render = True

neighbors = adjacency(body.data)
deltas, delta_evidence = paired_deltas(body, neighbors)
originals = {
    block.name: {vertex: block.data[vertex].co.copy() for vertex in deltas}
    for block in body.data.shape_keys.key_blocks
}
geometry_before, weights_before = geometry_digest(body), weight_digest(body)
lights = {obj.name: obj for obj in scene.objects if obj.type == "LIGHT"}
key, fill, rim = lights["Aevrynd Key"], lights["Aevrynd Fill"], lights["Aevrynd Rim"]
base_energy = {name: light.data.energy for name, light in lights.items()}
results = []
for label, factor in VARIANTS:
    set_factor(body, originals, deltas, factor)
    set_pose(body, "neutral")
    key.data.energy, fill.data.energy, rim.data.energy = base_energy[key.name], base_energy[fill.name], base_energy[rim.name]
    renders = {
        "neutralFront": render(scene, f"{label}-neutral-front"),
        "neutralOblique": render(scene, f"{label}-neutral-oblique", oblique=True),
    }
    set_pose(body, "open")
    renders["openFront"] = render(scene, f"{label}-open-front")
    set_pose(body, "smile")
    renders["smileFront"] = render(scene, f"{label}-smile-front")
    set_pose(body, "neutral")
    rim.data.energy = 0.0
    key.data.energy, fill.data.energy = 1350.0, 90.0
    renders["leftKeyFront"] = render(scene, f"{label}-left-key-front")
    key.data.energy, fill.data.energy = 90.0, 1350.0
    renders["rightKeyFront"] = render(scene, f"{label}-right-key-front")
    results.append({
        "label": label, "factor": factor, "renders": renders,
        "curvature": {"neutral": curvature_metrics(body, False), "smile": curvature_metrics(body, True)},
        "geometryDigest": geometry_digest(body), "weightDigest": weight_digest(body),
    })

selected_factor = next(factor for label, factor in VARIANTS if label == SELECTED)
set_factor(body, originals, deltas, selected_factor)
set_pose(body, "neutral")
key.data.energy, fill.data.energy, rim.data.energy = base_energy[key.name], base_energy[fill.name], base_energy[rim.name]
body.name = "AevryndFemaleCC0CommissureCurvature_R1076"
body["aevrynd_revision"] = "v249r1076-commissure-curvature"
body["aevrynd_source"] = SOURCE.name
body["aevrynd_curvature_pairs"] = json.dumps(PAIRS)
scene["aevrynd_release_state"] = "VISUAL_COLLISION_REVIEW_PENDING"
scene["aevrynd_website_promotion"] = "forbidden"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "revision": "v249r1076-commissure-curvature", "source": str(SOURCE), "output": str(OUTPUT),
    "method": "symmetrized far-neighbor Laplacian relaxation on four topology-matched commissure pairs, with identical deltas added to every shape key",
    "pairs": [list(pair) for pair in PAIRS], "deltaEvidence": delta_evidence,
    "variants": results, "selectedVariant": SELECTED,
    "geometryDigestBefore": geometry_before, "selectedGeometryDigest": next(item["geometryDigest"] for item in results if item["label"] == SELECTED),
    "weightDigestBefore": weights_before, "selectedWeightDigest": next(item["weightDigest"] for item in results if item["label"] == SELECTED),
    "topologyChanged": False, "materialChanged": False, "shapeKeysEdited": len(body.data.shape_keys.key_blocks),
    "websitePromotionApproved": False, "candidateStatus": "VISUAL_COLLISION_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1076_CURVATURE=" + json.dumps({"pairs": PAIRS, "variants": {item["label"]: item["curvature"] for item in results}}, sort_keys=True))
