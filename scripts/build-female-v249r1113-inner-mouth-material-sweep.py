"""Separate the mouth-interior faces from skin shading without changing collision geometry."""
from pathlib import Path
import json

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-integrated-upper-lip-r1110-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-inner-mouth-material-r1113-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1113-inner-mouth-material-sweep.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1113-inner-mouth-material-sweep"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
PATCH = "Aevrynd_ContinuousUpperLip_R1105"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
FRAMES = (1, 20, 33, 61)
VARIANTS = (
    ("a-deep-wine", (0.020, 0.0025, 0.0035, 1.0), 0.08),
    ("b-balanced-wine", (0.038, 0.0055, 0.0070, 1.0), 0.16),
    ("c-lifted-wine", (0.060, 0.0090, 0.0110, 1.0), 0.24),
)
SELECTED = None


def active_coordinates(obj):
    blocks = obj.data.shape_keys.key_blocks
    points = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        for index, item in enumerate(block.data):
            points[index] += block.value * (item.co - block.relative_key.data[index].co)
    return [obj.matrix_world @ point for point in points]


def make_inner_material(label, color, emission_strength):
    material = bpy.data.materials.new(f"Aevrynd_InnerMouth_R1113_{label}")
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = 0.82
    if "Subsurface Weight" in shader.inputs:
        shader.inputs["Subsurface Weight"].default_value = 0.03
    if "Specular IOR Level" in shader.inputs:
        shader.inputs["Specular IOR Level"].default_value = 0.18
    if "Emission Color" in shader.inputs:
        shader.inputs["Emission Color"].default_value = color
    if "Emission Strength" in shader.inputs:
        shader.inputs["Emission Strength"].default_value = emission_strength
    material["aevrynd_layer"] = "inner_mouth"
    material["aevrynd_owned_material"] = True
    return material


def assign_inner_faces(body, material):
    points = active_coordinates(body)
    selected = []
    bounds = {"x": [99.0, -99.0], "y": [99.0, -99.0], "z": [99.0, -99.0]}
    for polygon in body.data.polygons:
        polygon_points = [points[index] for index in polygon.vertices]
        centre = sum(polygon_points, Vector()) / len(polygon_points)
        normal = (polygon_points[1] - polygon_points[0]).cross(polygon_points[2] - polygon_points[0]).normalized()
        if abs(centre.x) > 0.030 or not 1.376 < centre.z < 1.399 or not -0.1345 < centre.y < -0.1200:
            continue
        if normal.y <= 0.40:
            continue
        selected.append(polygon.index)
        for axis, value in zip(("x", "y", "z"), centre):
            bounds[axis][0] = min(bounds[axis][0], value)
            bounds[axis][1] = max(bounds[axis][1], value)
    body.data.materials.append(material)
    material_index = len(body.data.materials) - 1
    for index in selected:
        body.data.polygons[index].material_index = material_index
    return {
        "faces": len(selected),
        "materialIndex": material_index,
        "bounds": {axis: [value * 1000.0 for value in pair] for axis, pair in bounds.items()},
        "selectionRule": "abs(x)<=30mm, 1376<z<1399mm, -134.5<y<-120mm, active-face normal y>0.40",
    }


def world_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles()
    triangles = [tuple(item.vertices) for item in mesh.loop_triangles]
    tree = BVHTree.FromPolygons(vertices, triangles, all_triangles=True)
    evaluated.to_mesh_clear()
    return tree, triangles


def self_collision(obj):
    tree, triangles = world_tree(obj)
    pairs = [(a, b) for a, b in tree.overlap(tree) if a < b and set(triangles[a]).isdisjoint(triangles[b])]
    return {"nonAdjacentPairs": len(pairs), "samplePairs": [list(pair) for pair in pairs[:20]]}


def set_pose(body, pose):
    keys = body.data.shape_keys.key_blocks
    keys[OPEN_KEY].value = 1.0 if pose == "open" else 0.0
    keys[SMILE_KEY].value = 1.0 if pose == "smile" else 0.0


def audit(scene, body):
    poses = {}
    scene.frame_set(1)
    for pose in ("neutral", "open", "smile"):
        set_pose(body, pose)
        bpy.context.view_layer.update()
        poses[pose] = self_collision(body)
    set_pose(body, "neutral")
    frames = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        frames[str(frame)] = self_collision(body)
    scene.frame_set(1)
    return poses, frames


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def hide_hair(scene):
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")):
                obj.hide_render = True


def render(scene, label, location, target, lens, size):
    camera = scene.camera
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    path = OUT / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


OUT.mkdir(parents=True, exist_ok=True)
variants = []
for label, color, emission_strength in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    body = bpy.data.objects[BODY]
    patch = bpy.data.objects.get(PATCH)
    if patch:
        patch.hide_render = True
        patch.hide_viewport = True
        patch["aevrynd_release_excluded"] = True
    hide_hair(scene)
    source_poses, source_frames = audit(scene, body)
    material = make_inner_material(label, color, emission_strength)
    assignment = assign_inner_faces(body, material)
    poses, frames = audit(scene, body)
    technical_pass = all(poses[key]["nonAdjacentPairs"] <= source_poses[key]["nonAdjacentPairs"] for key in poses) and all(
        frames[key]["nonAdjacentPairs"] <= source_frames[key]["nonAdjacentPairs"] for key in frames
    )
    scene.frame_set(1)
    set_pose(body, "neutral")
    renders = [
        render(scene, f"{label}-neutral-mouth-front", (0.0, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)),
        render(scene, f"{label}-neutral-face-front", (0.0, -0.72, 1.445), (0.0, -0.025, 1.445), 88, (1000, 1000)),
    ]
    set_pose(body, "open")
    renders.append(render(scene, f"{label}-open-mouth-front", (0.0, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)))
    set_pose(body, "smile")
    renders.append(render(scene, f"{label}-smile-mouth-front", (0.0, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)))
    set_pose(body, "neutral")
    variants.append({
        "label": label,
        "material": {"name": material.name, "baseColor": list(color), "emissionStrength": emission_strength},
        "assignment": assignment,
        "sourcePoseSelfCollision": source_poses,
        "sourceFrameSelfCollision": source_frames,
        "poseSelfCollision": poses,
        "frameSelfCollision": frames,
        "technicalStatus": "TECHNICAL_PASS" if technical_pass else "TECHNICAL_FAIL",
        "renders": renders,
    })
    if label == SELECTED and technical_pass:
        body["aevrynd_revision"] = "v249r1113-inner-mouth-material"
        body["aevrynd_inner_mouth_layer"] = material.name
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))


selected_item = next((item for item in variants if item["label"] == SELECTED and item["technicalStatus"] == "TECHNICAL_PASS"), None)
report = {
    "revision": "v249r1113-inner-mouth-material-sweep",
    "source": str(SOURCE),
    "output": str(OUTPUT) if selected_item else None,
    "method": "assign a separate owned dark-wine material to inward-facing mouth-interior polygons while leaving the continuous collision mesh unchanged",
    "variants": variants,
    "selectedVariant": SELECTED if selected_item else None,
    "websitePromotionApproved": False,
    "candidateStatus": "VISUAL_REVIEW_PENDING" if selected_item else "TECHNICAL_FAIL_DIAGNOSTIC_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1113_INNER_MOUTH=" + json.dumps({
    "variants": [{
        "label": item["label"],
        "faces": item["assignment"]["faces"],
        "poses": {key: value["nonAdjacentPairs"] for key, value in item["poseSelfCollision"].items()},
        "frames": {key: value["nonAdjacentPairs"] for key, value in item["frameSelfCollision"].items()},
        "status": item["technicalStatus"],
    } for item in variants]
}, sort_keys=True))
