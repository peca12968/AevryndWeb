"""Measure whether the retained CC0 donor can be merged into the active face topology."""
from pathlib import Path
import hashlib
import json
import math

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-lip-surface-balance-r1106-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1109-mouth-topology-inspection.json"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
DONOR = "AevryndFemaleCC0Baseline_v259"


def topology_digest(obj):
    payload = ";".join(
        ",".join(str(index) for index in polygon.vertices)
        for polygon in obj.data.polygons
    )
    return hashlib.sha256(payload.encode("ascii")).hexdigest()


def group_weights(obj, name):
    group = obj.vertex_groups.get(name)
    if group is None:
        return {}
    result = {}
    for vertex in obj.data.vertices:
        for assignment in vertex.groups:
            if assignment.group == group.index:
                result[vertex.index] = assignment.weight
                break
    return result


def donor_upper_lip_indices(donor):
    weights = group_weights(donor, "lips")
    keys = donor.data.shape_keys.key_blocks
    points = [item.co.copy() for item in keys[0].data]
    for block in keys[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        for index, item in enumerate(block.data):
            points[index] += block.value * (item.co - block.relative_key.data[index].co)
    faces = []
    for polygon in donor.data.polygons:
        if not all(weights.get(index, 0.0) >= 0.60 for index in polygon.vertices):
            continue
        centre = sum((points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
        if centre.z >= 1.3885 and centre.y <= -0.1300:
            faces.append(tuple(polygon.vertices))
    return sorted({index for face in faces for index in face}), faces


def active_coordinates(obj):
    keys = obj.data.shape_keys.key_blocks
    points = [item.co.copy() for item in keys[0].data]
    for block in keys[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        for index, item in enumerate(block.data):
            points[index] += block.value * (item.co - block.relative_key.data[index].co)
    return points


def spatial_mapping(body, donor, donor_indices, donor_faces):
    body_points = active_coordinates(body)
    donor_points = active_coordinates(donor)
    tree = KDTree(len(body_points))
    for index, point in enumerate(body_points):
        tree.insert(point, index)
    tree.balance()
    mapping = {}
    distances = {}
    for donor_index in donor_indices:
        _point, body_index, distance = tree.find(donor_points[donor_index])
        mapping[donor_index] = body_index
        distances[donor_index] = distance
    body_faces = {frozenset(polygon.vertices) for polygon in body.data.polygons}
    mapped_faces = [tuple(mapping[index] for index in face) for face in donor_faces]
    existing_faces = sum(frozenset(face) in body_faces for face in mapped_faces)
    values = list(distances.values())
    return {
        "mappedVertices": len(mapping),
        "uniqueBodyVertices": len(set(mapping.values())),
        "minimumDistanceMm": min(values) * 1000.0,
        "maximumDistanceMm": max(values) * 1000.0,
        "meanDistanceMm": sum(values) / len(values) * 1000.0,
        "withinPointZeroOneMm": sum(value <= 0.0001 for value in values),
        "withinPointFiveMm": sum(value <= 0.0005 for value in values),
        "mappedFaces": len(mapped_faces),
        "mappedFacesExistingInBody": existing_faces,
    }


def describe_delta(body, donor, indices):
    body_basis = body.data.shape_keys.key_blocks[0]
    donor_basis = donor.data.shape_keys.key_blocks[0]
    distances = []
    components = []
    for index in indices:
        delta = donor_basis.data[index].co - body_basis.data[index].co
        distances.append(delta.length)
        components.append((delta.x, delta.y, delta.z))
    return {
        "count": len(indices),
        "minimumMm": min(distances) * 1000.0,
        "maximumMm": max(distances) * 1000.0,
        "meanMm": sum(distances) / len(distances) * 1000.0,
        "rmsMm": math.sqrt(sum(value * value for value in distances) / len(distances)) * 1000.0,
        "meanComponentMm": [sum(value[axis] for value in components) / len(components) * 1000.0 for axis in range(3)],
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
donor = bpy.data.objects[DONOR]
indices, faces = donor_upper_lip_indices(donor)
mapping = spatial_mapping(body, donor, indices, faces)
body_groups = {group.name for group in body.vertex_groups}
donor_groups = {group.name for group in donor.vertex_groups}
body_keys = [key.name for key in body.data.shape_keys.key_blocks]
donor_keys = [key.name for key in donor.data.shape_keys.key_blocks]
same_faces = len(body.data.polygons) == len(donor.data.polygons) and all(
    tuple(a.vertices) == tuple(b.vertices)
    for a, b in zip(body.data.polygons, donor.data.polygons)
)
same_edges = len(body.data.edges) == len(donor.data.edges) and all(
    tuple(a.vertices) == tuple(b.vertices)
    for a, b in zip(body.data.edges, donor.data.edges)
)
body_lips = group_weights(body, "lips")
donor_lips = group_weights(donor, "lips")
common_lip_indices = sorted(set(body_lips) & set(donor_lips))
weight_errors = [abs(body_lips[index] - donor_lips[index]) for index in common_lip_indices]
report = {
    "revision": "v249r1109-mouth-topology-inspection",
    "source": str(SOURCE),
    "body": BODY,
    "donor": DONOR,
    "bodyMesh": {
        "vertices": len(body.data.vertices),
        "edges": len(body.data.edges),
        "polygons": len(body.data.polygons),
        "topologySha256": topology_digest(body),
    },
    "donorMesh": {
        "vertices": len(donor.data.vertices),
        "edges": len(donor.data.edges),
        "polygons": len(donor.data.polygons),
        "topologySha256": topology_digest(donor),
    },
    "topology": {
        "sameVertexCount": len(body.data.vertices) == len(donor.data.vertices),
        "sameEdgeConnectivityAndOrder": same_edges,
        "sameFaceConnectivityAndOrder": same_faces,
        "sameObjectMatrix": all(abs(a - b) < 1e-8 for row_a, row_b in zip(body.matrix_world, donor.matrix_world) for a, b in zip(row_a, row_b)),
    },
    "upperLipSelection": {
        "vertices": len(indices),
        "faces": len(faces),
        "minimumIndex": min(indices),
        "maximumIndex": max(indices),
    },
    "basisDelta": describe_delta(body, donor, indices),
    "rigCompatibility": {
        "commonVertexGroups": len(body_groups & donor_groups),
        "bodyOnlyVertexGroupCount": len(body_groups - donor_groups),
        "bodyOnlyVertexGroupSample": sorted(body_groups - donor_groups)[:20],
        "donorOnlyVertexGroupCount": len(donor_groups - body_groups),
        "donorOnlyVertexGroupSample": sorted(donor_groups - body_groups)[:20],
        "commonLipVertices": len(common_lip_indices),
        "maximumLipWeightDifference": max(weight_errors) if weight_errors else None,
    },
    "spatialMapping": mapping,
    "shapeKeyCompatibility": {
        "bodyCount": len(body_keys),
        "donorCount": len(donor_keys),
        "common": sorted(set(body_keys) & set(donor_keys)),
        "bodyOnly": sorted(set(body_keys) - set(donor_keys)),
        "donorOnly": sorted(set(donor_keys) - set(body_keys)),
    },
}
report["continuousMergeFeasible"] = all(report["topology"].values()) and report["rigCompatibility"]["maximumLipWeightDifference"] == 0.0
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1109_MOUTH_TOPOLOGY=" + json.dumps(report, sort_keys=True))
