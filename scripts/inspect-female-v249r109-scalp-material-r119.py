import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-tear-meniscus-r109.blend"
OUT = ROOT / "assets-source/aevrynd-character/female-v249r109-scalp-material-r119.json"


def plain_value(value):
    try:
        return list(value)
    except TypeError:
        try:
            return float(value)
        except (TypeError, ValueError):
            return str(value)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
rows = []
for obj in bpy.data.objects:
    layer = obj.get("aevrynd_layer", "")
    searchable = f"{obj.name} {layer}".lower()
    if "scalp" not in searchable and "root" not in searchable:
        continue
    materials = []
    if getattr(obj, "data", None) and hasattr(obj.data, "materials"):
        for material in obj.data.materials:
            if material is None:
                continue
            nodes = []
            if material.use_nodes and material.node_tree:
                for node in material.node_tree.nodes:
                    values = {}
                    for socket in node.inputs:
                        if hasattr(socket, "default_value") and not socket.is_linked:
                            values[socket.name] = plain_value(socket.default_value)
                    nodes.append({
                        "name": node.name,
                        "type": node.bl_idname,
                        "inputs": values,
                    })
                links = [{
                    "fromNode": link.from_node.name,
                    "fromSocket": link.from_socket.name,
                    "toNode": link.to_node.name,
                    "toSocket": link.to_socket.name,
                } for link in material.node_tree.links]
            else:
                links = []
            materials.append({
                "name": material.name,
                "surfaceRenderMethod": getattr(material, "surface_render_method", None),
                "diffuseColor": list(material.diffuse_color),
                "nodes": nodes,
                "links": links,
            })
    attributes = []
    if getattr(obj, "data", None) and hasattr(obj.data, "attributes"):
        for attribute in obj.data.attributes:
            values = []
            for item in attribute.data:
                if hasattr(item, "value"):
                    try:
                        values.append(float(item.value))
                    except TypeError:
                        values.extend(float(component) for component in item.value)
                elif hasattr(item, "color"):
                    values.extend(float(component) for component in item.color)
            attributes.append({
                "name": attribute.name,
                "domain": attribute.domain,
                "dataType": attribute.data_type,
                "count": len(attribute.data),
                "minimum": min(values) if values else None,
                "maximum": max(values) if values else None,
            })
    rows.append({
        "object": obj.name,
        "type": obj.type,
        "hideRender": obj.hide_render,
        "hideViewport": obj.hide_viewport,
        "layer": layer,
        "materials": materials,
        "attributes": attributes,
    })

report = {"source": str(SOURCE), "objects": rows}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_SCALP_MATERIAL_R119=" + json.dumps(report, sort_keys=True))
