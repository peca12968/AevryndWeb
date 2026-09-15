"""Compare existing traceable character sources for reusable oral topology."""

import json
from collections import defaultdict, deque
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
REPORT = ASSETS / "female-v249-mainline-r1045-source-topology-inspection.json"
SOURCES = (
    ASSETS / "aevrynd-female-authoring-v249-mainline-cc0-foundation-r249.blend",
    ASSETS / "aevrynd-female-authoring-v249-mainline-open-topology-physical-skin-r446.blend",
    ASSETS / "aevrynd-female-cc0-fitted-eye-skin-foundation-r602.blend",
    ASSETS / "aevrynd-female-cc0-lower-lip-rim-turn-r1033-study.blend",
)


def mesh_components(mesh):
    adjacency = [set() for _ in mesh.vertices]
    for edge in mesh.edges:
        first, second = edge.vertices
        adjacency[first].add(second)
        adjacency[second].add(first)
    pending = set(range(len(mesh.vertices)))
    result = []
    while pending:
        root = pending.pop()
        found = {root}
        queue = deque([root])
        while queue:
            fresh = adjacency[queue.popleft()] & pending
            pending.difference_update(fresh)
            found.update(fresh)
            queue.extend(fresh)
        result.append(found)
    return sorted(result, key=len, reverse=True)


def boundary_components(obj):
    mesh = obj.data
    coordinates = [obj.matrix_world @ vertex.co for vertex in mesh.vertices]
    edge_users = defaultdict(int)
    for polygon in mesh.polygons:
        vertices = list(polygon.vertices)
        for index, first in enumerate(vertices):
            edge_users[tuple(sorted((first, vertices[(index + 1) % len(vertices)])))] += 1
    mouth_edges = set()
    for edge, users in edge_users.items():
        if users != 1:
            continue
        midpoint = (coordinates[edge[0]] + coordinates[edge[1]]) * 0.5
        if abs(midpoint.x) < 0.060 and midpoint.y < -0.030 and 1.33 < midpoint.z < 1.43:
            mouth_edges.add(edge)
    vertex_edges = defaultdict(set)
    for edge in mouth_edges:
        for vertex in edge:
            vertex_edges[vertex].add(edge)
    pending = set(mouth_edges)
    components = []
    while pending:
        root = pending.pop()
        found = {root}
        queue = [root]
        while queue:
            fresh = set().union(*(vertex_edges[vertex] for vertex in queue.pop())) & pending
            pending.difference_update(fresh)
            found.update(fresh)
            queue.extend(fresh)
        components.append(found)
    return sorted((len(component) for component in components), reverse=True)


results = []
for source in SOURCES:
    if not source.exists():
        results.append({"source": str(source), "status": "MISSING"})
        continue
    bpy.ops.wm.open_mainfile(filepath=str(source))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    body_candidates = [
        obj
        for obj in meshes
        if any(token in obj.name.lower() for token in ("body", "female", "baseline", "skin"))
        and not any(token in obj.name.lower() for token in ("hair", "lash", "brow"))
    ]
    body = max(body_candidates or meshes, key=lambda obj: len(obj.data.polygons))
    components = mesh_components(body.data)
    relevant_groups = []
    for group in body.vertex_groups:
        if not any(token in group.name.lower() for token in ("mouth", "lip", "jaw", "chin")):
            continue
        members = []
        for vertex in body.data.vertices:
            if any(link.group == group.index and link.weight > 0.0 for link in vertex.groups):
                members.append(body.matrix_world @ vertex.co)
        relevant_groups.append({
            "name": group.name,
            "vertices": len(members),
            "bounds": {
                axis: [
                    round(min(getattr(point, axis) for point in members), 6),
                    round(max(getattr(point, axis) for point in members), 6),
                ]
                for axis in ("x", "y", "z")
            } if members else None,
        })
    oral_named = []
    for obj in bpy.context.scene.objects:
        if not any(token in obj.name.lower() for token in ("mouth", "oral", "lip", "teeth", "tooth", "tongue", "gum")):
            continue
        detail = {"name": obj.name, "type": obj.type}
        if obj.type == "MESH":
            world_points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
            detail.update({
                "vertices": len(obj.data.vertices),
                "polygons": len(obj.data.polygons),
                "bounds": {
                    axis: [
                        round(min(getattr(point, axis) for point in world_points), 6),
                        round(max(getattr(point, axis) for point in world_points), 6),
                    ]
                    for axis in ("x", "y", "z")
                } if world_points else None,
            })
        oral_named.append(detail)
    results.append({
        "source": str(source),
        "status": "INSPECTED",
        "largestMesh": body.name,
        "vertices": len(body.data.vertices),
        "polygons": len(body.data.polygons),
        "shapeKeys": len(body.data.shape_keys.key_blocks) if body.data.shape_keys else 0,
        "componentSizes": [len(component) for component in components[:12]],
        "mouthAreaOpenBoundaryComponentEdges": boundary_components(body),
        "mouthVertexGroups": relevant_groups,
        "oralNamedObjects": oral_named,
        "materialNames": [material.name if material else None for material in body.data.materials],
    })

usable = [
    item for item in results
    if item.get("mouthAreaOpenBoundaryComponentEdges") and item["mouthAreaOpenBoundaryComponentEdges"][0] >= 24
]
report = {
    "revision": "v249r1045-source-topology-inspection",
    "licenseEvidence": "blender-human-base-meshes-v141.source.json; CC0-1.0",
    "sources": results,
    "reusableOpenMouthSources": [Path(item["source"]).name for item in usable],
    "status": "SOURCE_FOUND" if usable else "NO_CLEAN_OPEN_MOUTH_SOURCE_FOUND",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1045_SOURCE_TOPOLOGY=" + json.dumps({"status": report["status"], "usable": report["reusableOpenMouthSources"]}, sort_keys=True))
