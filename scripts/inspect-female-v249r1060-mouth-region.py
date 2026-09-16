"""Measure the r1060 mouth boundary, materials and expression deltas."""

import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-smooth-mouth-transfer-r1060-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1060-mouth-region.inspect.json"
BODY = "AevryndFemaleCC0SmoothMouth_R1060"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
mesh = body.data
blocks = mesh.shape_keys.key_blocks
basis = blocks[0]

edge_faces = {edge.index: [] for edge in mesh.edges}
for polygon in mesh.polygons:
    for edge_index in polygon.edge_keys:
        pass
edge_lookup = {tuple(sorted(edge.vertices)): edge.index for edge in mesh.edges}
for polygon in mesh.polygons:
    for edge_key in polygon.edge_keys:
        edge_faces[edge_lookup[tuple(sorted(edge_key))]].append(polygon.index)

boundary = []
for edge in mesh.edges:
    if len(edge_faces[edge.index]) != 1:
        continue
    points = [body.matrix_world @ basis.data[index].co for index in edge.vertices]
    center = (points[0] + points[1]) * 0.5
    if abs(center.x) > 0.06 or not (1.35 < center.z < 1.42):
        continue
    polygon = mesh.polygons[edge_faces[edge.index][0]]
    boundary.append({
        "edge": edge.index,
        "vertices": list(edge.vertices),
        "center": [round(value, 7) for value in center],
        "materialIndex": polygon.material_index,
    })

def key_metrics(name):
    block = blocks[name]
    rows = []
    for index, item in enumerate(block.data):
        point = body.matrix_world @ basis.data[index].co
        if abs(point.x) > 0.06 or not (1.35 < point.z < 1.42):
            continue
        delta = body.matrix_world.to_3x3() @ (item.co - block.relative_key.data[index].co)
        if delta.length > 1e-7:
            rows.append((index, point, delta))
    return {
        "affectedVertices": len(rows),
        "maximumDeltaMm": max((row[2].length for row in rows), default=0.0) * 1000.0,
        "maximumVerticalMm": max((abs(row[2].z) for row in rows), default=0.0) * 1000.0,
        "meanVerticalMm": (sum(abs(row[2].z) for row in rows) / len(rows) if rows else 0.0) * 1000.0,
    }

report = {
    "revision": "v249r1060-mouth-region-inspection",
    "source": str(SOURCE),
    "body": BODY,
    "topology": {"vertices": len(mesh.vertices), "edges": len(mesh.edges), "faces": len(mesh.polygons)},
    "activeShapeKeys": {block.name: block.value for block in blocks if abs(block.value) > 1e-8},
    "materialSlots": [slot.material.name if slot.material else None for slot in body.material_slots],
    "mouthNamedVertexGroups": [
        group.name for group in body.vertex_groups
        if any(token in group.name.lower() for token in ("mouth", "lip", "jaw", "chin"))
    ],
    "mouthVertexGroupMetrics": {
        group.name: {
            "weightedVertices": sum(
                1 for vertex in mesh.vertices
                if any(item.group == group.index and item.weight > 1e-8 for item in vertex.groups)
            ),
            "maximumWeight": max((
                item.weight for vertex in mesh.vertices for item in vertex.groups
                if item.group == group.index
            ), default=0.0),
        }
        for group in body.vertex_groups
        if any(token in group.name.lower() for token in ("mouth", "lip"))
    },
    "mouthNamedColorAttributes": [
        attribute.name for attribute in mesh.color_attributes
        if any(token in attribute.name.lower() for token in ("mouth", "lip", "vermilion"))
    ],
    "materialPolygonCounts": {
        str(index): sum(1 for polygon in mesh.polygons if polygon.material_index == index)
        for index in range(len(body.material_slots))
    },
    "mouthRegionMaterialPolygonCounts": {
        str(index): sum(
            1 for polygon in mesh.polygons
            if polygon.material_index == index
            and abs((body.matrix_world @ polygon.center).x) < 0.055
            and 1.35 < (body.matrix_world @ polygon.center).z < 1.42
        )
        for index in range(len(body.material_slots))
    },
    "materialNodes": {
        material.name: {
            node.name: {
                socket.name: socket.default_value[:]
                if hasattr(socket.default_value, "__len__") else socket.default_value
                for socket in node.inputs if hasattr(socket, "default_value")
            }
            for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"
        }
        for material in (slot.material for slot in body.material_slots)
        if material and material.use_nodes and material.node_tree
    },
    "skinMaterialGraph": {
        "nodes": [
            {"name": node.name, "type": node.bl_idname, "label": node.label}
            for node in body.material_slots[0].material.node_tree.nodes
        ],
        "links": [
            {"from": link.from_node.name + "." + link.from_socket.name, "to": link.to_node.name + "." + link.to_socket.name}
            for link in body.material_slots[0].material.node_tree.links
        ],
        "lipControls": {
            node.name: {
                "operation": getattr(node, "operation", None),
                "attributeName": getattr(node, "attribute_name", None),
                "blendType": getattr(node, "blend_type", None),
                "inputs": {
                    socket.name: socket.default_value[:]
                    if hasattr(socket.default_value, "__len__") else socket.default_value
                    for socket in node.inputs if hasattr(socket, "default_value")
                },
                "indexedInputs": [
                    {
                        "index": index,
                        "name": socket.name,
                        "value": socket.default_value[:]
                        if hasattr(socket.default_value, "__len__") else socket.default_value,
                    }
                    for index, socket in enumerate(node.inputs) if hasattr(socket, "default_value")
                ],
            }
            for node in body.material_slots[0].material.node_tree.nodes
            if "Lip" in node.name or node.type in ("ATTRIBUTE", "MIX_RGB")
        },
    },
    "mouthBoundaryEdges": len(boundary),
    "mouthBoundary": boundary,
    "expressionMetrics": {OPEN_KEY: key_metrics(OPEN_KEY), SMILE_KEY: key_metrics(SMILE_KEY)},
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1060_MOUTH_INSPECT=" + json.dumps({
    "activeShapeKeys": report["activeShapeKeys"],
    "mouthBoundaryEdges": report["mouthBoundaryEdges"],
    "expressionMetrics": report["expressionMetrics"],
}, sort_keys=True))
