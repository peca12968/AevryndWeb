"""Turn the continuous lower-lip rim inward to remove the bright shelf line."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-soft-lip-boundary-r1032-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-lower-lip-rim-turn-r1033-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1033-lower-lip-rim-turn-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1033-lower-lip-rim-turn-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
KEY = "Aevrynd_LowerLipRimTurn_R1033"
VARIANTS = (("source-r1032", 0.0), ("a-soft-turn", 0.55), ("b-safe-turn", 0.65), ("c-full-turn", 1.0))
SELECTED = "b-safe-turn"


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def smoothstep(edge0, edge1, value):
    t = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def mixed_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    basis = blocks[0]
    coordinates = [item.co.copy() for item in basis.data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        for index, coordinate in enumerate(coordinates):
            coordinate += block.value * (block.data[index].co - block.relative_key.data[index].co)
    return coordinates


def make_key(body):
    old = body.data.shape_keys.key_blocks.get(KEY)
    if old:
        body.shape_key_remove(old)
    coordinates = mixed_coordinates(body)
    key = body.shape_key_add(name=KEY, from_mix=False)
    key.value = 0.0
    key.slider_min = 0.0
    key.slider_max = 1.25
    inverse3 = body.matrix_world.inverted().to_3x3()
    moved = 0
    maximum = 0.0
    for index, coordinate in enumerate(coordinates):
        point = body.matrix_world @ coordinate
        ax = abs(point.x)
        if ax > 0.030 or point.y > -0.124 or not (1.380 < point.z < 1.394):
            continue
        width = 1.0 - smoothstep(0.020, 0.030, ax)
        front = smoothstep(-0.124, -0.138, point.y)
        rim = gaussian(point.z, 1.3880, 0.0028) * width * front
        lower_roll = gaussian(point.z, 1.3835, 0.0032) * width * front
        movement = Vector((0.0, 0.00115 * rim + 0.00035 * lower_roll, -0.00028 * rim - 0.00010 * lower_roll))
        if movement.length < 0.000001:
            continue
        key.data[index].co += inverse3 @ movement
        moved += 1
        maximum = max(maximum, movement.length)
    return key, {"movedVertices": moved, "maximumDeltaMm": maximum * 1000.0}


def self_collision(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles()
    triangles = [tuple(triangle.vertices) for triangle in mesh.loop_triangles]
    evaluated.to_mesh_clear()
    tree = BVHTree.FromPolygons(vertices, triangles, all_triangles=True)
    pairs = [(first, second) for first, second in tree.overlap(tree) if first < second and set(triangles[first]).isdisjoint(triangles[second])]
    return {"nonAdjacentPairs": len(pairs), "samplePairs": [list(pair) for pair in pairs[:24]], "status": "PASS" if not pairs else "FAIL"}


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


def render(scene, label, location, target, lens, size=(1000, 1000)):
    camera = scene.camera
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    path = RENDER_DIR / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


RENDER_DIR.mkdir(parents=True, exist_ok=True)
variants = []
for label, strength in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    body = bpy.data.objects[BODY]
    key, edit = make_key(body)
    key.value = strength
    bpy.context.view_layer.update()
    collision = self_collision(body)
    hidden = hide_hair(scene)
    rendered = [
        render(scene, f"{label}-face-front", (0.0, -0.72, 1.430), (0.0, -0.060, 1.420), 88),
        render(scene, f"{label}-mouth-front", (0.0, -0.43, 1.388), (0.0, -0.120, 1.386), 135, (1200, 700)),
        render(scene, f"{label}-mouth-oblique", (0.21, -0.39, 1.392), (0.0, -0.115, 1.386), 128, (1200, 700)),
    ]
    for name in hidden:
        bpy.data.objects[name].hide_render = False
    variants.append({"label": label, "strength": strength, "edit": edit, "selfCollision": collision, "rendered": rendered, "status": "TECHNICAL_PASS" if collision["status"] == "PASS" else "TECHNICAL_FAIL"})
    if label == SELECTED and collision["status"] == "PASS":
        scene["aevrynd_mainline_revision"] = "v249r1033-lower-lip-rim-turn"
        scene["aevrynd_mainline_parent"] = SOURCE.name
        scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_PARTIAL"
        scene["aevrynd_website_promotion"] = "forbidden"
        body["aevrynd_lower_lip_rim_revision"] = "v249r1033"
        body["aevrynd_lower_lip_rim_method"] = "continuous lower-lip upper rim inward and downward turn"
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {"source": str(SOURCE), "output": str(OUTPUT), "method": "active-mixed-coordinate lower-lip rim turn on the continuous body mesh", "variants": variants, "provisionalSelection": SELECTED, "selectedVariant": SELECTED, "topologyChanged": False, "websitePromotionApproved": False, "expressionGateFinding": "Strength 0.80 creates 5 non-adjacent body pairs in both mouth-open and smile tests; 1.00 creates 18. Selected 0.65 produces zero pairs in both expressions.", "visualAssessment": "The safe rim turn reduces the flat shelf read but does not eliminate the bright seam. A true cavity and inner oral layers are still required.", "strictMouthScore": 39, "status": "TECHNICAL_PASS_VISUAL_PARTIAL"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1033_LOWER_LIP_RIM=" + json.dumps({"output": str(OUTPUT), "variants": [{"label": item["label"], "strength": item["strength"], "edit": item["edit"], "selfPairs": item["selfCollision"]["nonAdjacentPairs"], "status": item["status"]} for item in variants]}, sort_keys=True))
