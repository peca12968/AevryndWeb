"""Inspect the retained r1033 mesh for a minimal, continuous inner-lip cut."""

import json
from collections import Counter, deque
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-lower-lip-rim-turn-r1033-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1044-local-lip-band-inspection.json"
BODY = "AevryndFemaleCC0Baseline_v259"


def components(indices, adjacency):
    pending = set(indices)
    result = []
    while pending:
        root = pending.pop()
        queue = deque([root])
        found = {root}
        while queue:
            current = queue.popleft()
            for neighbor in adjacency[current]:
                if neighbor in pending:
                    pending.remove(neighbor)
                    found.add(neighbor)
                    queue.append(neighbor)
        result.append(found)
    return sorted(result, key=len, reverse=True)


def face_components(indices, face_edges, edge_faces):
    pending = set(indices)
    result = []
    while pending:
        root = pending.pop()
        queue = deque([root])
        found = {root}
        while queue:
            current = queue.popleft()
            neighbors = set()
            for edge in face_edges[current]:
                neighbors.update(edge_faces[edge])
            fresh = neighbors & pending
            pending.difference_update(fresh)
            found.update(fresh)
            queue.extend(fresh)
        result.append(found)
    return sorted(result, key=len, reverse=True)


def mixed_world_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    coordinates = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or block.value == 0.0:
            continue
        relative = block.relative_key
        for index, item in enumerate(block.data):
            coordinates[index] += block.value * (item.co - relative.data[index].co)
    return [body.matrix_world @ point for point in coordinates]


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
mesh = body.data
world = mixed_world_coordinates(body)

adjacency = [set() for _ in mesh.vertices]
edge_faces = {}
face_edges = {}
for polygon in mesh.polygons:
    vertices = list(polygon.vertices)
    polygon_edges = set()
    for index, vertex in enumerate(vertices):
        other = vertices[(index + 1) % len(vertices)]
        edge = tuple(sorted((vertex, other)))
        adjacency[vertex].add(other)
        adjacency[other].add(vertex)
        edge_faces.setdefault(edge, []).append(polygon.index)
        polygon_edges.add(edge)
    face_edges[polygon.index] = polygon_edges

group = body.vertex_groups.get("lips")
weighted = {}
for vertex in mesh.vertices:
    try:
        weight = group.weight(vertex.index)
    except RuntimeError:
        continue
    if weight > 0.0:
        weighted[vertex.index] = weight

weighted_components = components(weighted, adjacency)
mesh_components = components(range(len(mesh.vertices)), adjacency)
weighted_faces = [
    polygon.index
    for polygon in mesh.polygons
    if sum(vertex in weighted for vertex in polygon.vertices) >= 2
]

# Restrict candidate seam vertices to the front-facing, central lip band. The
# ranges are measured on the evaluated r1033 neutral shape, not inherited from
# an older character revision.
band = {
    index
    for index in weighted
    if abs(world[index].x) <= 0.036
    and world[index].y <= -0.083
    and 1.378 <= world[index].z <= 1.394
}
band_components = components(band, adjacency)
boundary_edges = []
for edge, faces in edge_faces.items():
    inside = sum(vertex in band for vertex in edge)
    if inside == 1:
        boundary_edges.append(edge)

main_component = set(mesh_components[0])
cut_sweep = []
for radius_x in (0.020, 0.024, 0.028, 0.032):
    for radius_z in (0.0008, 0.0012, 0.0016, 0.0020):
        candidates = set()
        for polygon in mesh.polygons:
            if polygon.vertices[0] not in main_component:
                continue
            center = sum((world[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
            ellipse = (center.x / radius_x) ** 2 + ((center.z - 1.3862) / radius_z) ** 2
            if center.y < -0.105 and ellipse < 1.0:
                candidates.add(polygon.index)
        candidate_components = face_components(candidates, face_edges, edge_faces)
        cut = candidate_components[0] if candidate_components else set()
        cut_boundary = {
            edge
            for face in cut
            for edge in face_edges[face]
            if any(neighbor not in cut for neighbor in edge_faces[edge])
        }
        boundary_adjacency = {}
        for first, second in cut_boundary:
            boundary_adjacency.setdefault(first, set()).add(second)
            boundary_adjacency.setdefault(second, set()).add(first)
        boundary_components = components(boundary_adjacency, boundary_adjacency) if boundary_adjacency else []
        cut_sweep.append({
            "radiusXmm": radius_x * 1000.0,
            "radiusZmm": radius_z * 1000.0,
            "candidateFaces": len(candidates),
            "candidateComponentSizes": [len(component) for component in candidate_components],
            "selectedCutFaces": len(cut),
            "boundaryEdges": len(cut_boundary),
            "boundaryComponentSizes": [len(component) for component in boundary_components],
            "closedDegreeTwoBoundary": bool(boundary_adjacency) and all(len(neighbors) == 2 for neighbors in boundary_adjacency.values()),
        })

def bounds(indices):
    points = [world[index] for index in indices]
    if not points:
        return None
    return {
        "minimum": [min(point[axis] for point in points) for axis in range(3)],
        "maximum": [max(point[axis] for point in points) for axis in range(3)],
    }


report = {
    "revision": "v249r1044-inspection",
    "source": str(SOURCE),
    "body": BODY,
    "mixedBaseVertices": len(world),
    "polygons": len(mesh.polygons),
    "shapeKeys": len(mesh.shape_keys.key_blocks),
    "lipWeight": {
        "vertices": len(weighted),
        "weightHistogramTenths": dict(sorted(Counter(round(value, 1) for value in weighted.values()).items())),
        "componentSizes": [len(component) for component in weighted_components],
        "bounds": bounds(weighted),
        "facesWithAtLeastTwoWeightedVertices": len(weighted_faces),
    },
    "meshComponents": [
        {
            "vertices": len(component),
            "lipWeightedVertices": sum(index in weighted for index in component),
            "bounds": bounds(component),
        }
        for component in mesh_components[:16]
    ],
    "minimalInnerBand": {
        "selectionRule": "abs(x)<=36mm, front y<=-83mm, z=1.378..1.394m, lips weight > 0",
        "vertices": len(band),
        "componentSizes": [len(component) for component in band_components],
        "bounds": bounds(band),
        "crossingBoundaryEdges": len(boundary_edges),
    },
    "minimalCutSweep": cut_sweep,
    "decisionGate": {
        "singleConnectedBand": len(band_components) == 1,
        "candidateMustAvoidFullPerioralReplacement": True,
        "requiredNextEvidence": "identify one closed upper and one closed lower inner-lip path on the main visible component, then render the proposed cut before adding oral layers",
    },
    "mouthRigBones": [
        bone.name for bone in bpy.data.objects["AevryndFemaleRig"].data.bones
        if any(token in bone.name.lower() for token in ("jaw", "mouth", "lip", "chin"))
    ],
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1044_LOCAL_LIP_INSPECTION=" + json.dumps(report["minimalInnerBand"], sort_keys=True))
