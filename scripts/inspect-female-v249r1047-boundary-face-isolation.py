"""Color-code the first visible r1046 skin faces around the mouth slit."""

import json
from collections import Counter
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-depth-cleanup-r1046-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1047-boundary-face-isolation.inspect.json"
RENDER = ROOT.parent / "Temp" / "female-realism" / "v249r1047-boundary-face-isolation" / "boundary-groups.png"
BODY = "AevryndFemaleCC0Baseline_v259"
CENTER_Z = 1.3862


def mixed_coordinates(obj):
    blocks = obj.data.shape_keys.key_blocks
    result = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-9:
            continue
        relative = block.relative_key
        for index, coordinate in enumerate(result):
            coordinate += block.value * (block.data[index].co - relative.data[index].co)
    return result


def material(name, color):
    result = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1.0)
    result.use_nodes = True
    bsdf = next(node for node in result.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.55
    return result


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
points = mixed_coordinates(body)
polygons = [tuple(polygon.vertices) for polygon in body.data.polygons]
tree = BVHTree.FromPolygons(points, polygons, all_triangles=False)
first_visible = set()
ray_hits = Counter()
for x_step in range(-42, 43):
    x = x_step * 0.0005
    for z_step in range(-5, 6):
        z = CENTER_Z + z_step * 0.0002
        location, _normal, polygon_index, _distance = tree.ray_cast(Vector((x, -0.40, z)), Vector((0.0, 1.0, 0.0)), 0.60)
        if polygon_index is None:
            continue
        polygon = body.data.polygons[polygon_index]
        center = sum((points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
        if polygon.material_index == 0 and center.y < -0.125:
            first_visible.add(polygon_index)
            ray_hits[polygon_index] += 1

colors = (
    ("Aevrynd_R1047_FrontBand", (0.90, 0.02, 0.02)),
    ("Aevrynd_R1047_MidBand", (0.02, 0.75, 0.05)),
    ("Aevrynd_R1047_RearBand", (0.03, 0.12, 0.95)),
)
slots = []
for name, color in colors:
    body.data.materials.append(material(name, color))
    slots.append(len(body.data.materials) - 1)

groups = {"front": [], "mid": [], "rear": []}
details = []
for face_index in sorted(first_visible):
    polygon = body.data.polygons[face_index]
    center = sum((points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)
    if center.y < -0.136:
        group, slot = "front", slots[0]
    elif center.y < -0.131:
        group, slot = "mid", slots[1]
    else:
        group, slot = "rear", slots[2]
    polygon.material_index = slot
    groups[group].append(face_index)
    details.append({
        "face": face_index,
        "group": group,
        "rayHits": ray_hits[face_index],
        "center": [round(center.x, 7), round(center.y, 7), round(center.z, 7)],
        "vertices": list(polygon.vertices),
    })

for obj in scene.objects:
    name = obj.name.lower()
    if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
        if not any(token in name for token in ("brow", "lash")):
            obj.hide_render = True
camera = scene.camera
camera.location = (0.0, -0.43, 1.388)
camera.data.lens = 135
look_at(camera, (0.0, -0.105, 1.386))
scene.render.resolution_x, scene.render.resolution_y = 1400, 820
scene.render.resolution_percentage = 100
RENDER.parent.mkdir(parents=True, exist_ok=True)
scene.render.filepath = str(RENDER)
bpy.ops.render.render(write_still=True)

report = {
    "revision": "v249r1047-boundary-face-isolation",
    "source": str(SOURCE),
    "render": str(RENDER),
    "firstVisibleSkinFaceCount": len(first_visible),
    "groups": groups,
    "faces": details,
    "status": "DIAGNOSTIC_COLOR_ISOLATION",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1047_BOUNDARY=" + json.dumps({"faces": len(first_visible), "groups": {key: len(value) for key, value in groups.items()}}, sort_keys=True))
