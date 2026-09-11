import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-balanced-back-chain-motion-r279.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-balanced-back-chain-motion-r279.material-audit.json"
TEXTURE = ROOT / "assets-source/aevrynd-character/textures/aevrynd-owned-hair-card-alpha-r272.png"
HAIR = "AevryndFemaleRuntimeHairCards_R276"
UV_NAME = "AevryndRuntimeHairCardUV"
MATERIAL = "Aevrynd_RuntimeHairCards_DenseAlpha_R276"


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
failures = []

hair = bpy.data.objects.get(HAIR)
if hair is None or hair.type != "MESH":
    failures.append({"missingMesh": HAIR})
    vertex_count = polygon_count = loop_count = 0
    uv_names = []
    material_names = []
else:
    vertex_count = len(hair.data.vertices)
    polygon_count = len(hair.data.polygons)
    loop_count = len(hair.data.loops)
    uv_names = [layer.name for layer in hair.data.uv_layers]
    material_names = [slot.material.name if slot.material else None for slot in hair.material_slots]
    if vertex_count != 18432:
        failures.append({"vertexCount": vertex_count, "expected": 18432})
    if polygon_count != 8832:
        failures.append({"polygonCount": polygon_count, "expected": 8832})
    if UV_NAME not in uv_names:
        failures.append({"missingUV": UV_NAME})
    if MATERIAL not in material_names:
        failures.append({"missingMaterial": MATERIAL})

material = bpy.data.materials.get(MATERIAL)
render_method = getattr(material, "surface_render_method", None) if material else None
texture_node = None
base_linked = alpha_linked = False
alpha_gain = None
image = None
if material is None or not material.use_nodes:
    failures.append({"missingNodeMaterial": MATERIAL})
else:
    principled = next((node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None)
    texture_node = next((node for node in material.node_tree.nodes if node.type == "TEX_IMAGE"), None)
    if texture_node is None or texture_node.image is None:
        failures.append({"missingImageTextureNode": MATERIAL})
    else:
        image = texture_node.image
    if principled is None:
        failures.append({"missingPrincipled": MATERIAL})
    else:
        base_linked = any(link.from_node == texture_node and link.to_socket == principled.inputs["Base Color"] for link in material.node_tree.links)
        opacity = next((node for node in material.node_tree.nodes if node.type == "MATH" and node.operation == "MULTIPLY"), None)
        alpha_gain = opacity.inputs[1].default_value if opacity else None
        texture_to_opacity = bool(opacity and any(link.from_node == texture_node and link.to_node == opacity for link in material.node_tree.links))
        opacity_to_alpha = bool(opacity and any(link.from_node == opacity and link.to_socket == principled.inputs["Alpha"] for link in material.node_tree.links))
        alpha_linked = texture_to_opacity and opacity_to_alpha
        if not base_linked:
            failures.append({"baseColorNotLinked": True})
        if not alpha_linked:
            failures.append({"alphaNotLinked": True})
        if alpha_gain is None or abs(alpha_gain - 2.45) > 1e-6:
            failures.append({"alphaGain": alpha_gain, "expected": 2.45})
    if render_method != "DITHERED":
        failures.append({"surfaceRenderMethod": render_method, "expected": "DITHERED"})

texture_size = list(image.size) if image else None
packed = bool(image and image.packed_file)
if texture_size != [256, 1024]:
    failures.append({"textureSize": texture_size, "expected": [256, 1024]})
if not packed and not TEXTURE.exists():
    failures.append({"textureUnavailable": str(TEXTURE)})

dynamic_bones = [bone.name for bone in bpy.data.objects["AevryndFemaleRig"].data.bones if bone.name.startswith("hair_dyn.")]
if len(dynamic_bones) != 15:
    failures.append({"dynamicBoneCount": len(dynamic_bones), "expected": 15})

report = {
    "model": str(MODEL),
    "mesh": {"name": HAIR, "vertices": vertex_count, "polygons": polygon_count, "loops": loop_count},
    "uvLayers": uv_names,
    "materials": material_names,
    "material": {"name": MATERIAL, "surfaceRenderMethod": render_method, "baseColorLinked": base_linked, "alphaLinked": alpha_linked, "alphaGain": alpha_gain},
    "texture": {"path": str(TEXTURE), "size": texture_size, "packed": packed, "ownedProceduralAsset": True},
    "dynamicBoneCount": len(dynamic_bones),
    "failures": failures,
    "status": "FAIL" if failures else "PASS",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R279_DENSE_ALPHA_HAIR_CARD_AUDIT=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)

