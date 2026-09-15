"""Separate visible vermilion from the deep oral rim on r1038 geometry."""

import hashlib
import json
import struct
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-inset-lip-support-r1038-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-separated-vermilion-r1039-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1039-lip-material-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1039-lip-material-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
INNER_MATERIAL = "Aevrynd_InnerMouthRimMat_R1035"
VARIANTS = (
    ("a-soft-dry-rose", (0.24, 0.055, 0.045), 0.66, 0.08),
    ("b-natural-vermilion", (0.31, 0.080, 0.060), 0.61, 0.12),
    ("c-warm-satin", (0.38, 0.105, 0.075), 0.56, 0.15),
)
SELECTED = "b-natural-vermilion"


def geometry_hash(body):
    digest = hashlib.sha256()
    for block in body.data.shape_keys.key_blocks:
        digest.update(block.name.encode("utf-8"))
        for item in block.data:
            digest.update(struct.pack("<3f", item.co.x, item.co.y, item.co.z))
    for polygon in body.data.polygons:
        digest.update(struct.pack("<I", len(polygon.vertices)))
        for index in polygon.vertices:
            digest.update(struct.pack("<I", index))
    return digest.hexdigest()


def make_material(label, color, roughness, subsurface):
    material = bpy.data.materials.new("Aevrynd_LipVermilion_R1039_" + label)
    material.use_nodes = True
    bsdf = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = subsurface
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.035
    material["aevrynd_owned_procedural"] = True
    material["aevrynd_layer_role"] = "visible lip vermilion"
    material["aevrynd_layer_revision"] = "v249r1039"
    return material


def assign_visible_vermilion(body, material):
    inner_index = body.data.materials.find(INNER_MATERIAL)
    if inner_index < 0:
        raise RuntimeError("r1035 inner-mouth material is missing")
    body.data.materials.append(material)
    vermilion_index = len(body.data.materials) - 1
    deepest_ring_start = len(body.data.vertices) - 120
    visible_faces = []
    deep_faces = []
    for polygon in body.data.polygons:
        if polygon.material_index != inner_index:
            continue
        if any(index >= deepest_ring_start for index in polygon.vertices):
            deep_faces.append(polygon.index)
        else:
            polygon.material_index = vermilion_index
            visible_faces.append(polygon.index)
    if len(visible_faces) != 480 or len(deep_faces) != 120:
        raise RuntimeError(f"Unexpected mouth material split: visible={len(visible_faces)}, deep={len(deep_faces)}")
    body.data.update()
    return {
        "visibleVermilionFaces": len(visible_faces),
        "deepOralRimFaces": len(deep_faces),
        "visibleMaterialIndex": vermilion_index,
        "deepMaterialIndex": inner_index,
        "deepestRingVertexStart": deepest_ring_start,
    }


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def hide_hair(scene):
    hidden = []
    for obj in scene.objects:
        is_hair = obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES"
        is_face_fibre = "Brow" in obj.name or obj.name.endswith(("UpperLashes", "LowerLashes"))
        if is_hair and not is_face_fibre and not obj.hide_render:
            obj.hide_render = True
            hidden.append(obj.name)
    return hidden


def render(scene, label, location, target, lens, size):
    camera = scene.camera
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    path = RENDER_DIR / (label + ".png")
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


source_audit = json.loads((ASSETS / "female-v249-mainline-r1038-inset-lip-support-rings.study.json").read_text(encoding="utf-8"))
source_selected = next(item for item in source_audit["variants"] if item["label"] == "b-natural-slit")
if source_selected["status"] != "TECHNICAL_PASS" or not all(state["status"] == "PASS" for state in source_selected["states"]):
    raise RuntimeError("r1038 selected geometry has not passed all collision states")

RENDER_DIR.mkdir(parents=True, exist_ok=True)
variants = []
source_hash = None
for label, color, roughness, subsurface in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    body = bpy.data.objects[BODY]
    before_hash = geometry_hash(body)
    if source_hash is None:
        source_hash = before_hash
    elif before_hash != source_hash:
        raise RuntimeError("Source geometry changed between material variants")
    split = assign_visible_vermilion(body, make_material(label, color, roughness, subsurface))
    after_hash = geometry_hash(body)
    hidden = hide_hair(scene)
    rendered = [
        render(scene, label + "-face-front", (0.0, -0.72, 1.430), (0.0, -0.060, 1.420), 88, (1000, 1000)),
        render(scene, label + "-mouth-front", (0.0, -0.43, 1.388), (0.0, -0.105, 1.386), 135, (1200, 700)),
        render(scene, label + "-mouth-oblique", (0.21, -0.39, 1.392), (0.0, -0.100, 1.386), 128, (1200, 700)),
    ]
    for expression, suffix in ((OPEN_KEY, "open"), (SMILE_KEY, "smile")):
        body.data.shape_keys.key_blocks[expression].value = 1.0
        bpy.context.view_layer.update()
        rendered.append(render(scene, label + "-" + suffix, (0.0, -0.43, 1.388), (0.0, -0.100, 1.386), 135, (1200, 700)))
        body.data.shape_keys.key_blocks[expression].value = 0.0
    for name in hidden:
        bpy.data.objects[name].hide_render = False
    item = {
        "label": label,
        "material": {"baseColor": color, "roughness": roughness, "subsurfaceWeight": subsurface},
        "split": split,
        "geometryHashBefore": before_hash,
        "geometryHashAfter": after_hash,
        "geometryIdentityPass": before_hash == after_hash,
        "inheritedCollisionEvidence": "r1038 b-natural-slit: frames 1/20/33/61 plus mouth-open and smile all PASS",
        "rendered": rendered,
        "status": "TECHNICAL_PASS" if before_hash == after_hash else "TECHNICAL_FAIL",
    }
    variants.append(item)
    if label == SELECTED and item["status"] == "TECHNICAL_PASS":
        scene["aevrynd_mainline_revision"] = "v249r1039-separated-vermilion"
        scene["aevrynd_mainline_parent"] = SOURCE.name
        scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_REQUIRED"
        scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "material-only split of 480 visible vermilion faces from the final 120-face deep oral rim",
    "sourceGeometryHash": source_hash,
    "variants": variants,
    "provisionalSelection": SELECTED,
    "selectedVariant": SELECTED,
    "skinToneContract": "Skin material, lights, exposure and color management are byte-identical to r1038; only mouth material indices and one owned material are added",
    "websitePromotionApproved": False,
    "status": "VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1039_LIP_MATERIAL=" + json.dumps({"output": str(OUTPUT), "variants": [{"label": item["label"], "identity": item["geometryIdentityPass"], "status": item["status"]} for item in variants]}, sort_keys=True))
