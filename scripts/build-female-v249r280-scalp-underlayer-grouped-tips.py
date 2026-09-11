import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-balanced-back-chain-motion-r279.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-scalp-underlayer-grouped-tips-r280.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-scalp-underlayer-grouped-tips-r280.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r280-scalp-underlayer-grouped-tips"
BODY = "AevryndFemaleBody_CC0_R249"
RIG = "AevryndFemaleRig"
CARDS = "AevryndFemaleRuntimeHairCards_R276"
SCALP = "AevryndFemaleScalpUnderlayer_R280"
POINTS = 24
STRIDE = POINTS * 2


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def grouped_tip_shortening(cards):
    rng = random.Random(280032)
    group_offsets = [rng.uniform(0.004, 0.032) for _ in range(32)]
    applied = []
    for card_index in range(len(cards.data.vertices) // STRIDE):
        base = card_index * STRIDE
        centers = [(cards.data.vertices[base + point * 2].co + cards.data.vertices[base + point * 2 + 1].co) * 0.5 for point in range(POINTS)]
        root = centers[0]
        angle = (math.atan2(root.y + 0.005, root.x) + math.pi) / (2.0 * math.pi)
        group = int(angle * 32) % 32
        band = int(clamp((root.z - 1.56) / 0.16) * 3.0)
        amount = clamp(group_offsets[group] + (band - 1) * 0.0025, 0.004, 0.034)
        tangent = centers[-1] - centers[16]
        if tangent.length < 1e-6:
            continue
        tangent.normalize()
        for point in range(15, POINTS):
            weight = smoothstep((point - 15) / (POINTS - 1 - 15))
            delta = -tangent * amount * weight
            cards.data.vertices[base + point * 2].co += delta
            cards.data.vertices[base + point * 2 + 1].co += delta
        applied.append({"card": card_index, "group": group, "shortenM": amount})
    cards.data.update()
    return {
        "groupCount": 32, "cardCount": len(applied),
        "minimumShortenM": min(item["shortenM"] for item in applied),
        "maximumShortenM": max(item["shortenM"] for item in applied),
        "groupOffsetsM": group_offsets,
    }


def scalp_material():
    material = bpy.data.materials.new("Aevrynd_ScalpUnderlayer_R280")
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = (0.0065, 0.0015, 0.0008, 1.0)
    shader.inputs["Roughness"].default_value = 0.74
    shader.inputs["Specular IOR Level"].default_value = 0.06
    material["aevrynd_layer"] = "material.hair.scalp_underlayer"
    material["aevrynd_ownership"] = "procedurally generated in-project"
    material["aevrynd_revision"] = "v249r280"
    return material


def build_scalp_underlayer(body, rig):
    mesh = body.data
    mesh.calc_loop_triangles()
    selected = []
    for polygon in mesh.polygons:
        center = sum((mesh.vertices[index].co for index in polygon.vertices), Vector()) / len(polygon.vertices)
        # The cap sits behind the frontal hairline and above the ear/neck region.
        if center.z > 1.555 and center.y > -0.064:
            selected.append(polygon)
    used = sorted({index for polygon in selected for index in polygon.vertices})
    remap = {old: new for new, old in enumerate(used)}
    vertices = [mesh.vertices[index].co + mesh.vertices[index].normal * 0.00075 for index in used]
    faces = [tuple(remap[index] for index in polygon.vertices) for polygon in selected]
    scalp_mesh = bpy.data.meshes.new("AevryndFemaleScalpUnderlayerTopology_R280")
    scalp_mesh.from_pydata(vertices, [], faces)
    scalp_mesh.materials.append(scalp_material())
    for polygon in scalp_mesh.polygons:
        polygon.use_smooth = True
    scalp = bpy.data.objects.new(SCALP, scalp_mesh)
    bpy.context.scene.collection.objects.link(scalp)
    scalp.matrix_world = body.matrix_world.copy()
    head = scalp.vertex_groups.new(name="head")
    head.add(list(range(len(vertices))), 1.0, "REPLACE")
    modifier = scalp.modifiers.new("Aevrynd Scalp Head Binding", "ARMATURE")
    modifier.object = rig
    scalp["aevrynd_layer"] = "hair.scalp_underlayer.head_bound"
    scalp["aevrynd_revision"] = "v249r280"
    scalp["aevrynd_clearance_m"] = 0.00075
    scalp["aevrynd_front_boundary_y_m"] = -0.064
    scalp["aevrynd_lower_boundary_z_m"] = 1.555
    return scalp


def render(camera, frame, name, location):
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.location = location
    camera.data.lens = 82
    look_at(camera, (0.0, 0.0, 1.56))
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
cards = bpy.data.objects[CARDS]
tip_report = grouped_tip_shortening(cards)
scalp = build_scalp_underlayer(bpy.data.objects[BODY], bpy.data.objects[RIG])
cards["aevrynd_revision"] = "v249r280"
scene["aevrynd_mainline_revision"] = "v249r280-scalp-underlayer-grouped-tips"
scene["aevrynd_hair_layers"] = "scalp_underlayer.head_bound|runtime.alpha_cards.dynamic.grouped_tips|flyaways"
scene["aevrynd_release_state"] = "SCALP_AND_TIPS_VISUAL_DYNAMIC_LAYER_REAUDIT_PENDING"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 800
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
for frame, name, location in (
    (1, "front-f01", (0.0, -0.90, 1.59)), (33, "front-f33", (0.0, -0.90, 1.59)),
    (1, "left-f01", (-0.72, -0.55, 1.59)), (1, "right-f01", (0.72, -0.55, 1.59)),
    (1, "back-f01", (0.0, 0.90, 1.59)), (33, "back-f33", (0.0, 0.90, 1.59)),
):
    render(camera, frame, name, location)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "cardObject": CARDS,
    "groupedTips": tip_report,
    "scalpUnderlayer": {"object": SCALP, "vertices": len(scalp.data.vertices), "faces": len(scalp.data.polygons), "clearanceM": 0.00075, "headBound": True},
    "layers": ["hair.scalp_underlayer.head_bound", "hair.runtime.alpha_cards.dynamic.grouped_tips", "hair.flyaways"],
    "ownedAssetOnly": True, "renderDirectory": str(RENDER_DIR),
    "status": "VISUAL_DYNAMIC_LAYER_REAUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R280_SCALP_UNDERLAYER_GROUPED_TIPS=" + json.dumps(report, sort_keys=True))
