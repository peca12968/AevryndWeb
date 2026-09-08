import json
import sys

import bpy


def mesh_summary(mesh):
    coordinates = [vertex.co for vertex in mesh.vertices]
    return {
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "polygons": len(mesh.polygons),
        "uv_layers": [layer.name for layer in mesh.uv_layers],
        "shape_keys": (
            [key.name for key in mesh.shape_keys.key_blocks]
            if mesh.shape_keys
            else []
        ),
        "local_bounds": {
            "min": [round(min(co[i] for co in coordinates), 6) for i in range(3)],
            "max": [round(max(co[i] for co in coordinates), 6) for i in range(3)],
        },
    }


args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
name_filter = args[0].casefold() if args else ""


def matches(name):
    return not name_filter or name_filter in name.casefold()


def object_summary(obj):
    entry = {
        "name": obj.name,
        "type": obj.type,
        "parent": obj.parent.name if obj.parent else None,
        "modifiers": [modifier.type for modifier in obj.modifiers],
        "dimensions": [round(value, 6) for value in obj.dimensions],
    }
    multires = next((modifier for modifier in obj.modifiers if modifier.type == "MULTIRES"), None)
    if multires:
        entry["multires"] = {
            "levels": multires.levels,
            "sculpt_levels": multires.sculpt_levels,
            "render_levels": multires.render_levels,
            "total_levels": multires.total_levels,
        }
    if obj.type == "MESH":
        entry["mesh"] = mesh_summary(obj.data)
        entry["materials"] = [material.name if material else None for material in obj.data.materials]
        entry["material_face_counts"] = {
            str(index): sum(1 for polygon in obj.data.polygons if polygon.material_index == index)
            for index in sorted({polygon.material_index for polygon in obj.data.polygons})
        }
    return entry


assets = []
for collection in bpy.data.collections:
    if collection.asset_data and matches(collection.name):
        assets.append(
            {
                "kind": "COLLECTION",
                "name": collection.name,
                "description": collection.asset_data.description,
                "objects": [object_summary(obj) for obj in collection.all_objects],
            }
        )

for obj in bpy.data.objects:
    if not obj.asset_data or not matches(obj.name):
        continue
    entry = object_summary(obj)
    entry["kind"] = "OBJECT"
    entry["description"] = obj.asset_data.description
    assets.append(entry)

print("AEVRYND_ASSET_AUDIT=" + json.dumps(assets, ensure_ascii=False))
