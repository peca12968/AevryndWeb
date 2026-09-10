import hashlib
import json
import struct
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-anatomical-hairline-fade-r187.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-satin-hair-r192.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-satin-hair-r192.build-report.json"
MATERIAL = "AevryndOwnedLayeredHairMaterial_v249r129"
HAIR_OBJECTS = (
    "AevryndFemaleCC0LongHairStudyMain_v249r85",
    "AevryndFemaleCC0LongHairStudyFlyaway_v249r85",
)


def geometry_digest(obj):
    digest = hashlib.sha256()
    if obj.type == "CURVES":
        for curve in obj.data.curves:
            digest.update(struct.pack("<II", curve.first_point_index, curve.points_length))
        for point in obj.data.points:
            digest.update(struct.pack("<fff", *point.position))
        for attribute in sorted(obj.data.attributes, key=lambda item: item.name):
            digest.update(attribute.name.encode("utf-8"))
            if attribute.data_type == "FLOAT":
                for item in attribute.data:
                    digest.update(struct.pack("<f", item.value))
    return digest.hexdigest()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
before = {name: geometry_digest(bpy.data.objects[name]) for name in HAIR_OBJECTS}
base = bpy.data.materials[MATERIAL]
material = base.copy()
material.name = "AevryndOwnedSatinHairMaterial_v249r192"
group = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeGroup")
group.node_tree = group.node_tree.copy()
tree = group.node_tree
shader = next(node for node in tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
for socket_name in ("Coat Weight", "Coat Roughness"):
    for link in list(shader.inputs[socket_name].links):
        tree.links.remove(link)
shader.inputs["Metallic"].default_value = 0.62
shader.inputs["Roughness"].default_value = 0.58
shader.inputs["Subsurface Weight"].default_value = 0.18
shader.inputs["Subsurface Scale"].default_value = 0.002
shader.inputs["Specular IOR Level"].default_value = 0.28
shader.inputs["Anisotropic"].default_value = 0.42
shader.inputs["Coat Weight"].default_value = 0.025
shader.inputs["Coat Roughness"].default_value = 0.48
material["aevrynd_revision"] = "v249r192"
material["aevrynd_layer"] = "hair.material.layered.satin"
material["aevrynd_runtime_dependency"] = "none"
for name in HAIR_OBJECTS:
    obj = bpy.data.objects[name]
    obj.data.materials.clear()
    obj.data.materials.append(material)
    obj["aevrynd_material_revision"] = "v249r192"

after = {name: geometry_digest(bpy.data.objects[name]) for name in HAIR_OBJECTS}
parity = before == after
scene = bpy.context.scene
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "satin-hair-r192"
scene["aevrynd_release_state"] = "R192_11SHOT_AND_STRICT_VISUAL_REVIEW_REQUIRED"
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "material": material.name,
    "settings": {"metallic": 0.62, "roughness": 0.58, "subsurfaceWeight": 0.18, "subsurfaceScale": 0.002, "specularIorLevel": 0.28, "anisotropic": 0.42, "coatWeight": 0.025, "coatRoughness": 0.48},
    "geometryChanged": False,
    "hairGeometryParity": parity,
    "before": before,
    "after": after,
    "status": "STRICT_VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249R192_SATIN_HAIR=" + json.dumps(report, sort_keys=True))
