import json
from pathlib import Path

import bpy


SOURCE = Path(r"D:\Download\Aevrynd\Temp\female-realism\blender-human-base-meshes-v1.4.1\extracted\human-base-meshes-bundle-v1.4.1\human_base_meshes_bundle.blend")
OUTPUT = Path(__file__).resolve().parents[1] / "assets-source/aevrynd-character/blender-human-base-meshes-v141.inventory.json"

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
objects = []
for obj in bpy.data.objects:
    row = {
        "name": obj.name,
        "type": obj.type,
        "collections": [collection.name for collection in obj.users_collection],
        "asset": bool(obj.asset_data),
    }
    if obj.type == "MESH":
        row.update({
            "vertices": len(obj.data.vertices),
            "edges": len(obj.data.edges),
            "polygons": len(obj.data.polygons),
            "uvLayers": [layer.name for layer in obj.data.uv_layers],
            "shapeKeys": [key.name for key in obj.data.shape_keys.key_blocks] if obj.data.shape_keys else [],
        })
    objects.append(row)

collections = [{
    "name": collection.name,
    "objects": [obj.name for obj in collection.objects],
    "children": [child.name for child in collection.children],
    "asset": bool(collection.asset_data),
} for collection in bpy.data.collections]

report = {
    "source": str(SOURCE),
    "objects": objects,
    "collections": collections,
    "status": "INSPECTED",
}
OUTPUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_BLENDER_HUMAN_BASE_MESH_V141=" + json.dumps({
    "objects": len(objects),
    "collections": len(collections),
    "meshObjects": sum(row["type"] == "MESH" for row in objects),
    "assetObjects": sum(row["asset"] for row in objects),
    "assetCollections": sum(row["asset"] for row in collections),
}, sort_keys=True))
