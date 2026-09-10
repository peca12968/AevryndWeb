import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = ROOT / "assets-source/reference/blender-official-hair/hair_nodes-female_hair_styles.blend"
AEVRYND = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-tear-meniscus-r109.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/female-v249r109-official-hair-material-radius-r125.json"


def scalar_values(attribute):
    if attribute is None:
        return []
    values = []
    for item in attribute.data:
        if hasattr(item, "value"):
            try:
                values.append(float(item.value))
            except TypeError:
                pass
    return values


def input_value(socket):
    if not hasattr(socket, "default_value"):
        return None
    value = socket.default_value
    try:
        return list(value)
    except TypeError:
        try:
            return float(value)
        except (TypeError, ValueError):
            return str(value)


def material_report(material):
    nodes = []
    if material and material.node_tree:
        for node in material.node_tree.nodes:
            nodes.append({
                "name": node.name,
                "type": node.bl_idname,
                "inputs": {
                    socket.name: input_value(socket)
                    for socket in node.inputs
                    if not socket.is_linked and input_value(socket) is not None
                },
                "nodeTree": node.node_tree.name if hasattr(node, "node_tree") and node.node_tree else None,
            })
    links = []
    if material and material.node_tree:
        links = [{
            "fromNode": link.from_node.name,
            "fromSocket": link.from_socket.name,
            "toNode": link.to_node.name,
            "toSocket": link.to_socket.name,
        } for link in material.node_tree.links]
    return {"name": material.name if material else None, "nodes": nodes, "links": links}


def object_report(path, object_name):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    obj = bpy.data.objects[object_name]
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    raw_radius = obj.data.attributes.get("radius")
    evaluated_radius = evaluated.data.attributes.get("radius")
    raw_values = scalar_values(raw_radius)
    evaluated_values = scalar_values(evaluated_radius)
    return {
        "path": str(path),
        "object": object_name,
        "rawCurves": len(obj.data.curves),
        "rawPoints": len(obj.data.points),
        "evaluatedCurves": len(evaluated.data.curves),
        "evaluatedPoints": len(evaluated.data.points),
        "rawRadiusDomain": raw_radius.domain if raw_radius else None,
        "rawRadiusMinimumM": min(raw_values) if raw_values else None,
        "rawRadiusMaximumM": max(raw_values) if raw_values else None,
        "evaluatedRadiusDomain": evaluated_radius.domain if evaluated_radius else None,
        "evaluatedRadiusMinimumM": min(evaluated_values) if evaluated_values else None,
        "evaluatedRadiusMaximumM": max(evaluated_values) if evaluated_values else None,
        "materials": [material_report(material) for material in obj.data.materials],
    }


report = {
    "officialMain": object_report(OFFICIAL, "long hair main"),
    "officialFlyaway": object_report(OFFICIAL, "long hair strands"),
    "aevryndMain": object_report(AEVRYND, "AevryndFemaleCC0LongHairStudyMain_v249r85"),
    "aevryndFlyaway": object_report(AEVRYND, "AevryndFemaleCC0LongHairStudyFlyaway_v249r85"),
}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_OFFICIAL_HAIR_MATERIAL_RADIUS_R125=" + json.dumps(report, sort_keys=True))
