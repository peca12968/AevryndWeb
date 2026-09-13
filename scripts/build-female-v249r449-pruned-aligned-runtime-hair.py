import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-open-topology-runtime-hair-r448-study.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-pruned-aligned-runtime-hair-r449-study.blend"
REPORT = ASSETS / "female-v249-mainline-pruned-aligned-runtime-hair-r449.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r449-pruned-aligned-runtime-hair"
BODY = "AevryndFemaleBodyBaseV118"
LAYERS = tuple(f"AevryndFemaleRuntimeCards_{region}_R409" for region in ("front", "crown", "rear", "hairline"))
FRAMES = (1, 20, 33, 61)
VERTICES_PER_CARD = 48
FACES_PER_CARD = 23
PENETRATION_LIMIT = -0.0005


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def body_tree(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def evaluated_points(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    return [evaluated.matrix_world @ vertex.co for vertex in evaluated.data.vertices]


def find_colliding_cards(scene, body, objects):
    rejected = {obj.name: set() for obj in objects}
    frame_counts = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        tree = body_tree(body)
        frame_counts[str(frame)] = {}
        for obj in objects:
            points = evaluated_points(obj)
            penetrating = []
            for index, point in enumerate(points):
                hit = tree.find_nearest(point, 0.20)
                if hit is None or hit[1] is None:
                    continue
                if (point - hit[0]).dot(hit[1].normalized()) < PENETRATION_LIMIT:
                    penetrating.append(index)
                    rejected[obj.name].add(index // VERTICES_PER_CARD)
            frame_counts[str(frame)][obj.name] = {
                "penetratingVertices": len(penetrating),
                "affectedCards": len({index // VERTICES_PER_CARD for index in penetrating}),
            }
    return rejected, frame_counts


def rebuild_without_cards(obj, rejected):
    old_mesh = obj.data
    old_card_count = len(old_mesh.vertices) // VERTICES_PER_CARD
    retained = [card for card in range(old_card_count) if card not in rejected]
    group_names = [group.name for group in obj.vertex_groups]
    group_weights = {name: [] for name in group_names}
    vertices = []
    faces = []
    old_polygon_indices = []
    for new_card, old_card in enumerate(retained):
        old_base = old_card * VERTICES_PER_CARD
        new_base = new_card * VERTICES_PER_CARD
        for local in range(VERTICES_PER_CARD):
            old_vertex = old_mesh.vertices[old_base + local]
            new_index = len(vertices)
            vertices.append(old_vertex.co.copy())
            for membership in old_vertex.groups:
                group_weights[group_names[membership.group]].append((new_index, membership.weight))
        for segment in range(FACES_PER_CARD):
            a = new_base + segment * 2
            faces.append((a, a + 1, a + 3, a + 2))
            old_polygon_indices.append(old_card * FACES_PER_CARD + segment)
    new_mesh = bpy.data.meshes.new(old_mesh.name.replace("_Data", "_R449_Data"))
    new_mesh.from_pydata(vertices, [], faces)
    for material in old_mesh.materials:
        new_mesh.materials.append(material)
    old_uv = old_mesh.uv_layers.active
    if old_uv:
        new_uv = new_mesh.uv_layers.new(name=old_uv.name)
        for new_polygon, old_polygon_index in zip(new_mesh.polygons, old_polygon_indices):
            old_polygon = old_mesh.polygons[old_polygon_index]
            for new_loop, old_loop in zip(new_polygon.loop_indices, old_polygon.loop_indices):
                new_uv.data[new_loop].uv = old_uv.data[old_loop].uv
        new_uv.active_render = True
    obj.data = new_mesh
    for group in list(obj.vertex_groups):
        obj.vertex_groups.remove(group)
    for name in group_names:
        group = obj.vertex_groups.new(name=name)
        for vertex_index, weight in group_weights[name]:
            group.add([vertex_index], weight, "REPLACE")
    obj["aevrynd_card_count"] = len(retained)
    obj["aevrynd_removed_collision_cards_r449"] = len(rejected)
    obj["aevrynd_revision"] = "v249r449"
    return {
        "sourceCards": old_card_count,
        "removedCards": len(rejected),
        "retainedCards": len(retained),
        "retainedPercent": 100.0 * len(retained) / old_card_count,
        "vertices": len(new_mesh.vertices),
        "faces": len(new_mesh.polygons),
    }


def render(scene, camera, frame, label, location, target, lens):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{label}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
objects = [bpy.data.objects[name] for name in LAYERS]
rejected, pre_prune = find_colliding_cards(scene, body, objects)
pruning = {obj.name: rebuild_without_cards(obj, rejected[obj.name]) for obj in objects}
scene.frame_set(1)
scene["aevrynd_mainline_revision"] = "v249r449-pruned-aligned-runtime-hair-study"
scene["aevrynd_release_state"] = "R449_COLLISION_REVALIDATION_AND_VISUAL_REVIEW_REQUIRED"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
for frame, label, location, target, lens in (
    (1, "01-front-f01", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    (1, "02-hairline-f01", (0.0, -0.57, 1.76), (0.0, -0.02, 1.64), 92),
    (1, "03-top-f01", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    (1, "04-three-quarter-f01", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
    (1, "05-back-f01", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
    (33, "06-front-f33", (0.0, -0.76, 1.58), (0.0, -0.015, 1.56), 84),
    (33, "07-back-f33", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
):
    render(scene, camera, frame, label, location, target, lens)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "renderDirectory": str(RENDER_DIR),
    "frames": list(FRAMES),
    "penetrationLimitM": PENETRATION_LIMIT,
    "prePruneCollision": pre_prune,
    "pruning": pruning,
    "totalSourceCards": sum(item["sourceCards"] for item in pruning.values()),
    "totalRemovedCards": sum(item["removedCards"] for item in pruning.values()),
    "totalRetainedCards": sum(item["retainedCards"] for item in pruning.values()),
    "method": "Remove each complete 48-vertex card if any evaluated vertex penetrates the r446 body at frame 1, 20, 33 or 61; do not distort surviving card surfaces.",
    "ownedAssetOnly": True,
    "websitePromotionApproved": False,
    "status": "COLLISION_REVALIDATION_AND_VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R449_PRUNED_ALIGNED_RUNTIME_HAIR=" + json.dumps(report, sort_keys=True))
