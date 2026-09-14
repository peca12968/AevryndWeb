import hashlib
import json
import math
import struct
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v249-mainline-natural-sclera-r496.blend"
REPORT = ROOT / "assets-source" / "aevrynd-character" / "female-v249-mainline-lash-stack-r496.inspection.json"
PARTS = ("UpperLashes", "LowerLashes", "TearMeniscus", "Caruncle", "Cornea", "Sclera")
BODY_NAME = "AevryndFemaleBodyBaseV118"


def evaluated_mesh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    return evaluated, mesh, points, faces


def geometry_digest(points, faces):
    digest = hashlib.sha256()
    digest.update(struct.pack("<II", len(points), len(faces)))
    for point in points:
        digest.update(struct.pack("<fff", *point))
    for face in faces:
        digest.update(struct.pack("<I", len(face)))
        for index in face:
            digest.update(struct.pack("<I", index))
    return digest.hexdigest()


def components(obj):
    adjacency = [[] for _ in obj.data.vertices]
    for edge in obj.data.edges:
        a, b = edge.vertices
        adjacency[a].append(b)
        adjacency[b].append(a)
    seen = set()
    sizes = []
    for start in range(len(adjacency)):
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        count = 0
        while stack:
            current = stack.pop()
            count += 1
            for neighbor in adjacency[current]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        sizes.append(count)
    return sorted(sizes)


def bounds(points):
    if not points:
        return None
    return {
        "minimum": [min(point[axis] for point in points) for axis in range(3)],
        "maximum": [max(point[axis] for point in points) for axis in range(3)],
    }


def material_report(obj):
    values = []
    for material in obj.data.materials:
        if material is None:
            continue
        entry = {"name": material.name, "useNodes": material.use_nodes}
        if material.use_nodes:
            shader = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
            if shader:
                entry["principled"] = {
                    "baseColor": list(shader.inputs["Base Color"].default_value),
                    "roughness": float(shader.inputs["Roughness"].default_value),
                    "specularIorLevel": float(shader.inputs["Specular IOR Level"].default_value),
                }
        values.append(entry)
    return values


def nearest_distance(points, tree):
    distance = math.inf
    for point in points:
        location, _, _, value = tree.find_nearest(point)
        if location is not None:
            distance = min(distance, value)
    return None if not math.isfinite(distance) else distance


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
report = {
    "source": str(SOURCE),
    "sceneEyeRevision": scene.get("aevrynd_eye_revision"),
    "objects": {},
    "frames": {},
}

for side in ("L", "R"):
    for part in PARTS:
        name = f"Eye_{side}_{part}"
        obj = bpy.data.objects.get(name)
        if obj is None:
            report["objects"][name] = {"exists": False}
            continue
        entry = {
            "exists": True,
            "type": obj.type,
            "hideRender": obj.hide_render,
            "hideViewport": obj.hide_viewport,
            "aevryndExport": obj.get("aevrynd_export"),
            "aevryndRole": obj.get("aevrynd_role"),
            "parent": obj.parent.name if obj.parent else None,
            "parentType": obj.parent_type,
            "parentBone": obj.parent_bone,
            "matrixWorld": [list(row) for row in obj.matrix_world],
            "modifiers": [
                {
                    "name": modifier.name,
                    "type": modifier.type,
                    "object": modifier.object.name if getattr(modifier, "object", None) else None,
                }
                for modifier in obj.modifiers
            ],
            "vertexGroups": [group.name for group in obj.vertex_groups],
            "materials": material_report(obj) if obj.type == "MESH" else [],
        }
        if obj.type == "MESH":
            entry.update({
                "vertices": len(obj.data.vertices),
                "edges": len(obj.data.edges),
                "polygons": len(obj.data.polygons),
                "connectedComponentVertexCounts": components(obj),
                "fiberCountProperty": obj.get("aevrynd_fiber_count"),
                "lengthRangeM": [obj.get("aevrynd_length_min_m"), obj.get("aevrynd_length_max_m")],
                "rootClearanceM": obj.get("aevrynd_root_clearance_m"),
            })
        report["objects"][name] = entry

body = bpy.data.objects[BODY_NAME]
boundary_edges = [edge for edge in body.data.edges if len(edge.link_faces) == 1] if hasattr(body.data.edges[0], "link_faces") else []
# MeshEdge has no link_faces in object mode, so count polygon ownership explicitly.
edge_uses = {}
for polygon in body.data.polygons:
    indices = list(polygon.vertices)
    for index, a in enumerate(indices):
        b = indices[(index + 1) % len(indices)]
        key = tuple(sorted((a, b)))
        edge_uses[key] = edge_uses.get(key, 0) + 1
boundary_pairs = [edge for edge, count in edge_uses.items() if count == 1]
boundary_adjacency = {}
for a, b in boundary_pairs:
    boundary_adjacency.setdefault(a, []).append(b)
    boundary_adjacency.setdefault(b, []).append(a)
boundary_components = []
seen_boundary = set()
for start in boundary_adjacency:
    if start in seen_boundary:
        continue
    stack = [start]
    seen_boundary.add(start)
    component = []
    while stack:
        current = stack.pop()
        component.append(current)
        for neighbor in boundary_adjacency[current]:
            if neighbor not in seen_boundary:
                seen_boundary.add(neighbor)
                stack.append(neighbor)
    boundary_components.append(component)
report["bodyBoundaryComponents"] = []
scene.frame_set(1)
bpy.context.view_layer.update()
boundary_depsgraph = bpy.context.evaluated_depsgraph_get()
boundary_evaluated = body.evaluated_get(boundary_depsgraph)
boundary_mesh = boundary_evaluated.to_mesh()
boundary_world_points = [boundary_evaluated.matrix_world @ vertex.co for vertex in boundary_mesh.vertices]
for component in boundary_components:
    points = [boundary_world_points[index] for index in component]
    report["bodyBoundaryComponents"].append({
        "vertexCount": len(component),
        "indices": component,
        "bounds": bounds(points),
        "centroid": [sum(point[axis] for point in points) / len(points) for axis in range(3)],
    })
boundary_evaluated.to_mesh_clear()

for frame in (1, 20):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body = bpy.data.objects[BODY_NAME]
    body_eval, body_mesh, body_points, body_faces = evaluated_mesh(body, depsgraph)
    body_tree = BVHTree.FromPolygons(body_points, body_faces, all_triangles=False)
    frame_report = {}
    for side in ("L", "R"):
        collider_trees = {"body": body_tree}
        collider_meshes = []
        for part in ("Cornea", "Sclera", "TearMeniscus"):
            obj = bpy.data.objects.get(f"Eye_{side}_{part}")
            if obj is None:
                continue
            evaluated, mesh, points, faces = evaluated_mesh(obj, depsgraph)
            collider_trees[part] = BVHTree.FromPolygons(points, faces, all_triangles=False)
            collider_meshes.append((evaluated, mesh))
        for kind in ("Upper", "Lower"):
            name = f"Eye_{side}_{kind}Lashes"
            obj = bpy.data.objects.get(name)
            if obj is None:
                frame_report[name] = {"exists": False}
                continue
            evaluated, mesh, points, faces = evaluated_mesh(obj, depsgraph)
            lash_tree = BVHTree.FromPolygons(points, faces, all_triangles=False)
            frame_report[name] = {
                "exists": True,
                "bounds": bounds(points),
                "digest": geometry_digest(points, faces),
                "nearestVertexDistanceM": {
                    label: nearest_distance(points, tree) for label, tree in collider_trees.items()
                },
                "triangleOverlapPairs": {
                    label: len(lash_tree.overlap(tree)) for label, tree in collider_trees.items()
                },
            }
            evaluated.to_mesh_clear()
        for evaluated, mesh in collider_meshes:
            evaluated.to_mesh_clear()
    body_eval.to_mesh_clear()
    report["frames"][str(frame)] = frame_report

REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R496_LASH_STACK=" + json.dumps(report))
