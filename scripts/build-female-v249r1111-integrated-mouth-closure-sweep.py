"""Reduce the relaxed mouth aperture after replacing the floating upper-lip layer."""
from pathlib import Path
import json
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-integrated-upper-lip-r1110-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-integrated-mouth-closure-r1111-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1111-integrated-mouth-closure-sweep.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1111-integrated-mouth-closure-sweep"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
PATCH = "Aevrynd_ContinuousUpperLip_R1105"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
CLOSURE_KEY = "Aevrynd_RelaxedMouthClosure_R1111"
FRAMES = (1, 20, 33, 61)
VARIANTS = (("a-gentle", 0.0005), ("b-balanced", 0.0009), ("c-firm", 0.0013))
SELECTED = None


def gaussian(value, centre, width):
    return math.exp(-0.5 * ((value - centre) / width) ** 2)


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def active_coordinates(obj):
    blocks = obj.data.shape_keys.key_blocks
    points = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        for index, item in enumerate(block.data):
            points[index] += block.value * (item.co - block.relative_key.data[index].co)
    return [obj.matrix_world @ point for point in points]


def add_closure_key(body, lift):
    points = active_coordinates(body)
    group = body.vertex_groups["lips"]
    basis = body.data.shape_keys.key_blocks[0]
    key = body.shape_key_add(name=CLOSURE_KEY)
    key.relative_key = basis
    key.slider_min = 0.0
    key.slider_max = 1.0
    key.value = 1.0
    for index, point in enumerate(basis.data):
        key.data[index].co = point.co
    selected = []
    maximum = 0.0
    for vertex in body.data.vertices:
        if not any(item.group == group.index for item in vertex.groups):
            continue
        point = points[vertex.index]
        if abs(point.x) > 0.027 or not 1.3820 < point.z < 1.3900 or point.y > -0.1325:
            continue
        horizontal = 1.0 - smoothstep((abs(point.x) - 0.018) / 0.009)
        rim = gaussian(point.z, 1.3862, 0.0028) * horizontal
        if rim <= 0.02:
            continue
        delta = Vector((0.0, 0.00012 * rim, lift * rim))
        key.data[vertex.index].co = basis.data[vertex.index].co + delta
        selected.append(vertex.index)
        maximum = max(maximum, delta.length)
    return {
        "shapeKey": CLOSURE_KEY,
        "vertices": len(selected),
        "maximumMoveMm": maximum * 1000.0,
        "liftMm": lift * 1000.0,
        "surfaceRecessionMm": 0.12,
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


def set_pose(body, pose, closure=True):
    keys = body.data.shape_keys.key_blocks
    keys[OPEN_KEY].value = 1.0 if pose == "open" else 0.0
    keys[SMILE_KEY].value = 1.0 if pose == "smile" else 0.0
    if CLOSURE_KEY in keys:
        keys[CLOSURE_KEY].value = (0.0 if pose == "open" else (0.55 if pose == "smile" else 1.0)) if closure else 0.0


def audit(scene, body, closure):
    poses = {}
    scene.frame_set(1)
    for pose in ("neutral", "open", "smile"):
        set_pose(body, pose, closure)
        bpy.context.view_layer.update()
        poses[pose] = self_collision(body)
    set_pose(body, "neutral", closure)
    frames = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        frames[str(frame)] = self_collision(body)
    scene.frame_set(1)
    return poses, frames


def no_regression(source, after):
    return all(after[key]["nonAdjacentPairs"] <= source[key]["nonAdjacentPairs"] for key in source)


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
for label, lift in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    body = bpy.data.objects[BODY]
    patch = bpy.data.objects.get(PATCH)
    if patch:
        patch.hide_render = True
        patch.hide_viewport = True
        patch["aevrynd_release_excluded"] = True
    hide_hair(scene)
    source_poses, source_frames = audit(scene, body, closure=False)
    edit = add_closure_key(body, lift)
    poses, frames = audit(scene, body, closure=True)
    technical_pass = no_regression(source_poses, poses) and no_regression(source_frames, frames)
    scene.frame_set(1)
    set_pose(body, "neutral", True)
    renders = [
        render(scene, f"{label}-neutral-mouth-front", (0.0, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)),
        render(scene, f"{label}-neutral-face-front", (0.0, -0.72, 1.445), (0.0, -0.025, 1.445), 88, (1000, 1000)),
    ]
    set_pose(body, "open", True)
    renders.append(render(scene, f"{label}-open-mouth-front", (0.0, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)))
    set_pose(body, "smile", True)
    renders.append(render(scene, f"{label}-smile-mouth-front", (0.0, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)))
    set_pose(body, "neutral", True)
    variants.append({
        "label": label,
        "edit": edit,
        "sourcePoseSelfCollision": source_poses,
        "sourceFrameSelfCollision": source_frames,
        "poseSelfCollision": poses,
        "frameSelfCollision": frames,
        "technicalStatus": "TECHNICAL_PASS" if technical_pass else "TECHNICAL_FAIL",
        "renders": renders,
    })
    if label == SELECTED and technical_pass:
        body["aevrynd_revision"] = "v249r1111-integrated-mouth-closure"
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"
        scene["aevrynd_website_promotion"] = "forbidden"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))


selected_item = next((item for item in variants if item["label"] == SELECTED and item["technicalStatus"] == "TECHNICAL_PASS"), None)
report = {
    "revision": "v249r1111-integrated-mouth-closure-sweep",
    "source": str(SOURCE),
    "output": str(OUTPUT) if selected_item else None,
    "method": "raise and slightly recess the lower-lip outer rim in a neutral-only corrective key after excluding the former floating upper-lip geometry",
    "variants": variants,
    "selectedVariant": SELECTED if selected_item else None,
    "websitePromotionApproved": False,
    "candidateStatus": "VISUAL_REVIEW_PENDING" if selected_item else "TECHNICAL_FAIL_DIAGNOSTIC_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1111_MOUTH_CLOSURE=" + json.dumps({
    "variants": [{
        "label": item["label"],
        "edit": item["edit"],
        "poses": {key: value["nonAdjacentPairs"] for key, value in item["poseSelfCollision"].items()},
        "frames": {key: value["nonAdjacentPairs"] for key, value in item["frameSelfCollision"].items()},
        "status": item["technicalStatus"],
    } for item in variants]
}, sort_keys=True))
