"""Rebuild the visible upper-lip eversion without moving the oral rim or lower lip."""
from pathlib import Path
import json
import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-lower-wetline-r1102-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-upper-lip-eversion-r1104-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1104-upper-lip-eversion.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1104-upper-lip-eversion"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
OPEN_KEY = "Aevrynd_MouthOpenTest_R1030"
SMILE_KEY = "Aevrynd_SmileTest_R1030"
FRAMES = (1, 20, 33, 61)


def gaussian(value, centre, width):
    return math.exp(-0.5 * ((value - centre) / width) ** 2)


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def active_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    points = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        for index, item in enumerate(block.data):
            points[index] += block.value * (item.co - block.relative_key.data[index].co)
    return [body.matrix_world @ point for point in points]


def build_deltas(body, strength):
    points = active_coordinates(body)
    lip_group = body.vertex_groups["lips"]
    inner_rim = body.data.attributes["aevrynd_inner_rim_r1074"].data
    deltas = {}
    regions = {"upperVermilion": 0, "centralTubercle": 0, "cupidPeaks": 0, "centralNotch": 0}
    for vertex in body.data.vertices:
        weights = [item.weight for item in vertex.groups if item.group == lip_group.index]
        if not weights or inner_rim[vertex.index].value > 0.025:
            continue
        point = points[vertex.index]
        if abs(point.x) > 0.030 or not 1.3885 < point.z < 1.4035 or point.y > -0.1350:
            continue
        horizontal = 1.0 - smoothstep((abs(point.x) - 0.019) / 0.011)
        band = gaussian(point.z, 1.3940, 0.0065) * horizontal
        if band < 0.025:
            continue

        lateral = min(1.0, abs(point.x) / 0.030)
        target_y = -0.1415 + 0.0085 * (lateral ** 1.5)
        projection = min(0.0, target_y - point.y) * band * strength
        delta = Vector((0.0, projection, 0.0))
        regions["upperVermilion"] += 1

        tubercle = band * gaussian(point.x, 0.0, 0.0080) * gaussian(point.z, 1.3940, 0.0040)
        delta.y -= strength * 0.00015 * tubercle
        regions["centralTubercle"] += int(tubercle > 0.025)

        peaks = band * gaussian(abs(point.x), 0.0105, 0.0048) * gaussian(point.z, 1.3970, 0.0035)
        delta.y -= strength * 0.00005 * peaks
        delta.z += strength * 0.00012 * peaks
        regions["cupidPeaks"] += int(peaks > 0.025)

        notch = band * gaussian(point.x, 0.0, 0.0045) * gaussian(point.z, 1.3990, 0.0035)
        delta.z -= strength * 0.00008 * notch
        regions["centralNotch"] += int(notch > 0.025)
        deltas[vertex.index] = delta
    return deltas, regions


def apply_deltas(body, world_deltas):
    local_inverse = body.matrix_world.inverted().to_3x3()
    local = {index: local_inverse @ delta for index, delta in world_deltas.items()}
    for block in body.data.shape_keys.key_blocks:
        for index, delta in local.items():
            block.data[index].co += delta
    body.data.update()
    return {
        "vertices": len(local),
        "shapeKeysUpdated": len(body.data.shape_keys.key_blocks),
        "maximumMoveMm": max(delta.length for delta in world_deltas.values()) * 1000.0,
        "meanMoveMm": sum(delta.length for delta in world_deltas.values()) / len(world_deltas) * 1000.0,
    }


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles()
    triangles = [tuple(item.vertices) for item in mesh.loop_triangles]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, triangles, all_triangles=True), triangles


def self_collision(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    tree, triangles = world_tree(body, depsgraph)
    pairs = [(a, b) for a, b in tree.overlap(tree) if a < b and set(triangles[a]).isdisjoint(triangles[b])]
    return {"nonAdjacentPairs": len(pairs), "samplePairs": [list(pair) for pair in pairs[:20]]}


def set_pose(body, pose):
    keys = body.data.shape_keys.key_blocks
    keys[OPEN_KEY].value = 1.0 if pose == "open" else 0.0
    keys[SMILE_KEY].value = 1.0 if pose == "smile" else 0.0


def audit_poses(scene, body):
    result = {}
    scene.frame_set(1)
    for pose in ("neutral", "open", "smile"):
        set_pose(body, pose)
        bpy.context.view_layer.update()
        result[pose] = self_collision(body)
    set_pose(body, "neutral")
    return result


def audit_frames(scene, body):
    result = {}
    set_pose(body, "neutral")
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        result[str(frame)] = self_collision(body)
    scene.frame_set(1)
    return result


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


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
hide_hair(scene)
source_pose = audit_poses(scene, body)
source_frames = audit_frames(scene, body)

EVERSION_STRENGTH = 1.0
deltas, regions = build_deltas(body, EVERSION_STRENGTH)
edit = apply_deltas(body, deltas)
after_pose = audit_poses(scene, body)
after_frames = audit_frames(scene, body)
no_pose_regression = all(after_pose[key]["nonAdjacentPairs"] <= source_pose[key]["nonAdjacentPairs"] for key in source_pose)
no_frame_regression = all(after_frames[key]["nonAdjacentPairs"] <= source_frames[key]["nonAdjacentPairs"] for key in source_frames)
technical_status = "TECHNICAL_PASS" if no_pose_regression and no_frame_regression else "TECHNICAL_FAIL"

OUT.mkdir(parents=True, exist_ok=True)
scene.frame_set(1)
set_pose(body, "neutral")
renders = [
    render(scene, "neutral-mouth-front", (0.0, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)),
    render(scene, "neutral-mouth-oblique", (-0.105, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)),
    render(scene, "neutral-face-front", (0.0, -0.72, 1.445), (0.0, -0.025, 1.445), 88, (1000, 1000)),
]
set_pose(body, "open")
renders.append(render(scene, "open-mouth-front", (0.0, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)))
set_pose(body, "smile")
renders.append(render(scene, "smile-mouth-front", (0.0, -0.43, 1.391), (0.0, -0.115, 1.386), 135, (1100, 720)))
set_pose(body, "neutral")

if technical_status == "TECHNICAL_PASS":
    body["aevrynd_revision"] = "v249r1104-upper-lip-eversion"
    body["aevrynd_source"] = SOURCE.name
    scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"
    scene["aevrynd_website_promotion"] = "forbidden"
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "revision": "v249r1104-upper-lip-eversion",
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "isolate the outward-facing upper vermilion outside the authored inner-rim mask, evert its lower roll, and add restrained tubercle and Cupid-bow relief through every shape key",
    "regions": regions,
    "eversionStrength": EVERSION_STRENGTH,
    "edit": edit,
    "sourcePoseSelfCollision": source_pose,
    "poseSelfCollision": after_pose,
    "sourceFrameSelfCollision": source_frames,
    "frameSelfCollision": after_frames,
    "technicalStatus": technical_status,
    "renders": renders,
    "websitePromotionApproved": False,
    "candidateStatus": "VISUAL_REVIEW_PENDING" if technical_status == "TECHNICAL_PASS" else "TECHNICAL_REJECTED",
}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1104_UPPER_LIP=" + json.dumps({"regions": regions, "eversionStrength": EVERSION_STRENGTH,
    "edit": edit, "sourcePose": {k: v["nonAdjacentPairs"] for k, v in source_pose.items()}, "afterPose": {k: v["nonAdjacentPairs"] for k, v in after_pose.items()}, "sourceFrames": {k: v["nonAdjacentPairs"] for k, v in source_frames.items()}, "afterFrames": {k: v["nonAdjacentPairs"] for k, v in after_frames.items()}, "status": technical_status}, sort_keys=True))



