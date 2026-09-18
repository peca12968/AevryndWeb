"""Test a ray-hit-localized inner-lip material on the r1068 technical base."""
import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-exact-edge-support-r1068-study.blend"
INSPECTION = ASSETS / "female-v249-mainline-r1070-visible-support-faces.inspect.json"
OUTPUT = ASSETS / "aevrynd-female-cc0-ray-hit-inner-strip-r1071-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1071-ray-hit-inner-strip-material.study.json"
OUT = ROOT.parent / "Temp/female-realism/v249r1071-ray-hit-inner-strip"
BODY = "AevryndFemaleCC0ExactEdgeSupport_R1068"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
SELECTED = "b-exact-ray-hit"


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def hide_hair(scene):
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")):
                obj.hide_render = True


def active_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    coords = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.name in (OPEN_KEY, SMILE_KEY) or block.mute or abs(block.value) < 1e-8:
            continue
        for index, item in enumerate(block.data):
            coords[index] += block.value * (item.co - block.relative_key.data[index].co)
    return coords


def face_center(body, polygon, coords):
    return sum((body.matrix_world @ coords[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)


def grow_faces(mesh, seeds, coords, body):
    seed_vertices = {index for face_index in seeds for index in mesh.polygons[face_index].vertices}
    grown = set(seeds)
    for polygon in mesh.polygons:
        if not any(index in seed_vertices for index in polygon.vertices):
            continue
        center = face_center(body, polygon, coords)
        if abs(center.x) <= 0.032 and center.y < -0.118 and 1.3825 <= center.z <= 1.3900:
            grown.add(polygon.index)
    return grown


def make_inner_lip_material():
    material = bpy.data.materials.new("Aevrynd_RayHitInnerLip_R1071")
    material.use_nodes = True
    bsdf = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.16, 0.028, 0.035, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.58
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.22
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = 0.05
    material["aevrynd_owned_procedural"] = True
    return material


def render(scene, label, oblique=False, opened=False):
    body = bpy.data.objects[BODY]
    keys = body.data.shape_keys.key_blocks
    keys[OPEN_KEY].value = 1.0 if opened else 0.0
    keys[SMILE_KEY].value = 0.0
    camera = scene.camera
    camera.data.lens = 135
    camera.location = ((-0.105 if oblique else 0.0), -0.43, 1.391)
    look_at(camera, (0.0, -0.115, 1.386))
    scene.render.resolution_x, scene.render.resolution_y = 1100, 720
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


inspection = json.loads(INSPECTION.read_text(encoding="utf-8"))
exact_faces = sorted({
    item["nearestBaseFace"] for item in inspection["whiteLinePixelRays"]
    if item.get("sampleKind") == "brightLine" and item.get("object") == BODY
    and item.get("location", [0.0, 0.0])[1] < -0.1 and item.get("nearestBaseFace") is not None
})
OUT.mkdir(parents=True, exist_ok=True)
results = []
variants = (("a-control", 0), ("b-exact-ray-hit", 1), ("c-one-ring", 2), ("d-two-ring", 3), ("e-support-adjacent-union", 4))
for label, growth in variants:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    body = bpy.data.objects[BODY]
    hide_hair(scene)
    coords = active_coordinates(body)
    selected = set(exact_faces)
    if growth == 4:
        new_vertices = set(range(13583, len(body.data.vertices)))
        support_faces = {polygon.index for polygon in body.data.polygons if any(index in new_vertices for index in polygon.vertices)}
        support_vertices = {index for face_index in support_faces for index in body.data.polygons[face_index].vertices}
        selected = set(support_faces)
        for polygon in body.data.polygons:
            if not any(index in support_vertices for index in polygon.vertices):
                continue
            center = face_center(body, polygon, coords)
            if abs(center.x) <= 0.032 and center.y < -0.118 and 1.3825 <= center.z <= 1.3900:
                selected.add(polygon.index)
    else:
        for _ in range(max(0, growth - 1)):
            selected = grow_faces(body.data, selected, coords, body)
    if growth:
        material_index = len(body.data.materials)
        body.data.materials.append(make_inner_lip_material())
        for face_index in selected:
            body.data.polygons[face_index].material_index = material_index
        body.data.update()
    renders = [
        render(scene, f"{label}-neutral-front"),
        render(scene, f"{label}-neutral-oblique", oblique=True),
        render(scene, f"{label}-open", opened=True),
    ]
    results.append({"label": label, "growth": growth, "selectedFaceCount": len(selected) if growth else 0, "selectedFaces": sorted(selected) if growth else [], "renders": renders})
    if label == SELECTED:
        body.name = "AevryndFemaleCC0RayHitInnerStrip_R1071"
        body["aevrynd_revision"] = "v249r1071-ray-hit-inner-strip"
        body["aevrynd_source"] = SOURCE.name
        body["aevrynd_exact_ray_hit_faces"] = len(exact_faces)
        scene["aevrynd_release_state"] = "VISUAL_AND_COLLISION_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "revision": "v249r1071-ray-hit-inner-strip-material",
    "source": str(SOURCE),
    "inspection": str(INSPECTION),
    "output": str(OUTPUT),
    "method": "assign one owned inner-lip material only to low-density faces mapped from bright-line camera rays, then compare exact, one-ring and two-ring coverage",
    "exactRayHitFaces": exact_faces,
    "variants": results,
    "selectedVariant": SELECTED,
    "topologyChanged": False,
    "websitePromotionApproved": False,
    "candidateStatus": "VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1071_RAY_HIT_STRIP=" + json.dumps({"exactFaces": exact_faces, "variantCounts": {item["label"]: item["selectedFaceCount"] for item in results}}, sort_keys=True))
