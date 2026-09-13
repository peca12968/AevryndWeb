import json
import math
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-layered-optical-stack-r420.blend"
PATH_REPORT = ROOT / "assets-source/aevrynd-character/female-v249-native-eyelid-loop-r441.study.json"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-native-eyelid-aperture-r442-study.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-native-eyelid-aperture-r442.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r442-native-eyelid-aperture-sweep"
BODY = "AevryndFemaleBody_CC0_R249"
EYE_LAYERS = ("ScleraOpen", "LimbalAnnulus", "IrisConcave", "PupilRecessed", "CorneaConvex")


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def copy_body(source, name):
    obj = source.copy()
    obj.data = source.data.copy()
    obj.name = name
    obj.data.name = name + "Geometry"
    bpy.context.scene.collection.objects.link(obj)
    return obj


def world_bvh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def reshape_native_lids(body, paths, upper_rise, lower_drop):
    inverse = body.matrix_world.inverted()
    points = [body.matrix_world @ vertex.co for vertex in body.data.vertices]
    normal_matrix = body.matrix_world.to_3x3()
    normals = [(normal_matrix @ vertex.normal).normalized() for vertex in body.data.vertices]
    neighbors = [set() for _ in body.data.vertices]
    for edge in body.data.edges:
        first, second = edge.vertices
        neighbors[first].add(second)
        neighbors[second].add(first)

    seed_delta = {}
    side_seeds = {"L": set(), "R": set()}
    for side in ("L", "R"):
        asymmetry = 0.98 if side == "L" else 1.0
        for kind, magnitude in (("upper", upper_rise * asymmetry), ("lower", -lower_drop)):
            path = paths[side][kind]["vertices"]
            start, end = points[path[0]], points[path[-1]]
            x_min, x_max = start.x, end.x
            if x_min > x_max:
                x_min, x_max = x_max, x_min
            for index in path:
                point = points[index]
                parameter = max(0.0, min(1.0, (point.x - x_min) / max(1e-9, x_max - x_min)))
                canthus_line = start.z + (end.z - start.z) * parameter
                profile = math.sin(math.pi * parameter) ** (0.82 if kind == "upper" else 1.18)
                seed_delta[index] = canthus_line + magnitude * profile - point.z
                side_seeds[side].add(index)

    numerator = defaultdict(float)
    denominator = defaultdict(float)
    falloff = (1.0, 0.72, 0.40, 0.18, 0.065)
    for side in ("L", "R"):
        side_sign = 1.0 if side == "L" else -1.0
        for seed in side_seeds[side]:
            frontier = {seed}
            visited = {seed}
            delta = seed_delta[seed]
            for step, weight in enumerate(falloff):
                for index in frontier:
                    numerator[index] += delta * weight
                    denominator[index] += weight
                if step == len(falloff) - 1:
                    break
                next_frontier = set()
                for index in frontier:
                    for neighbor in neighbors[index]:
                        point = points[neighbor]
                        if neighbor in visited or point.x * side_sign <= 0.0 or not (1.585 < point.z < 1.628):
                            continue
                        if normals[neighbor].y >= -0.18 or point.y >= -0.105:
                            continue
                        next_frontier.add(neighbor)
                visited.update(next_frontier)
                frontier = next_frontier

    moved = {"L": 0, "R": 0}
    maximum = 0.0
    for index, total in numerator.items():
        delta = total / denominator[index]
        if index in seed_delta:
            delta = seed_delta[index]
        if abs(delta) < 1e-8:
            continue
        point = points[index].copy()
        point.z += delta
        body.data.vertices[index].co = inverse @ point
        moved["L" if point.x >= 0.0 else "R"] += 1
        maximum = max(maximum, abs(delta))
    body.data.update()
    return {
        "upperRiseM": upper_rise,
        "lowerDropM": lower_drop,
        "targetCentralApertureM": upper_rise + lower_drop,
        "movedVertices": moved,
        "maximumDisplacementM": maximum,
        "exactPathVertices": {side: len(side_seeds[side]) for side in side_seeds},
    }


def neutral_lights(scene):
    for obj in list(bpy.data.objects):
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)
    target = (0.0, -0.025, 1.60)
    for name, location, energy, size in (
        ("Aevrynd Neutral Key R442", (-0.42, -0.82, 1.82), 39.0, 0.56),
        ("Aevrynd Neutral Fill R442", (0.48, -0.62, 1.70), 24.0, 0.68),
        ("Aevrynd Neutral Top R442", (0.0, -0.08, 2.28), 22.0, 0.52),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.color, data.shape, data.size = energy, (1.0, 1.0, 1.0), "DISK", size
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
        obj.location = location
        look_at(obj, target)
    scene.world.use_nodes = True
    background = next(node for node in scene.world.node_tree.nodes if node.type == "BACKGROUND")
    background.inputs["Color"].default_value = (0.018, 0.018, 0.018, 1.0)
    background.inputs["Strength"].default_value = 0.35


def hide_large_hair():
    for obj in bpy.data.objects:
        name = obj.name.lower()
        if any(token in name for token in ("brow", "lash", "lid", "tear", "caruncle", "eye")):
            continue
        materials = getattr(obj.data, "materials", ()) if hasattr(obj, "data") else ()
        material_names = " ".join(material.name.lower() for material in materials if material)
        if obj.type in {"MESH", "CURVES", "CURVE"} and any(token in name or token in material_names for token in ("hair", "scalp", "groom", "flyaway", "root", "lock", "fiber")):
            obj.hide_render = True


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
hide_large_hair()
neutral_lights(scene)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
scene.camera = camera
source_body = bpy.data.objects[BODY]
source_body.hide_render = True
paths = json.loads(PATH_REPORT.read_text(encoding="utf-8"))["eyes"]
variants = (
    ("a-redistributed", 0.0038, 0.0026),
    ("b-balanced", 0.0045, 0.0028),
    ("c-open", 0.0050, 0.0030),
)
views = (
    ("face", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92, (1000, 1000)),
    ("eyes", (0.0, -0.46, 1.615), (0.0, -0.035, 1.610), 105, (1200, 760)),
    ("three-quarter", (0.44, -0.63, 1.62), (0.0, -0.02, 1.595), 88, (1000, 1000)),
)
metrics = {}
previous = None
for label, upper_rise, lower_drop in variants:
    if previous:
        bpy.data.objects.remove(previous, do_unlink=True)
    body = copy_body(source_body, f"AevryndFemaleBody_NativeLids_{label}_R442")
    body.hide_render = False
    edit = reshape_native_lids(body, paths, upper_rise, lower_drop)
    scene.frame_set(1)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = world_bvh(body, depsgraph)
    overlaps = {
        side: {
            kind: len(body_tree.overlap(world_bvh(bpy.data.objects[f"AevryndEye_{side}_{kind}_R420"], depsgraph)))
            for kind in EYE_LAYERS
        }
        for side in ("L", "R")
    }
    metrics[label] = {**edit, "frame1BodyOpticalTriangleOverlaps": overlaps}
    for view_name, location, target, lens, size in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.resolution_x, scene.render.resolution_y = size
        scene.render.filepath = str(RENDER_DIR / f"{label}-{view_name}.png")
        bpy.ops.render.render(write_still=True)
    previous = body

collision_pass = all(value == 0 for variant in metrics.values() for side in variant["frame1BodyOpticalTriangleOverlaps"].values() for value in side.values())
status = "REJECTED_INNER_LOWER_LID_PATH_DEFORMATION" if collision_pass else "REJECTED_NATIVE_APERTURE_COLLISION_FAIL"
bpy.data.objects.remove(source_body, do_unlink=True)
previous.name = BODY
previous["aevrynd_revision"] = "v249r442-study-c-open"
scene["aevrynd_native_eyelid_aperture_study"] = "v249r442"
scene["aevrynd_release_state"] = status
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "pathSource": str(PATH_REPORT),
    "output": str(OUTPUT),
    "outputContainsVariant": "c-open",
    "renderDirectory": str(RENDER_DIR),
    "method": "Reshape the discovered native continuous eyelid paths in Z, with four topology-ring falloff steps and no detached patch geometry.",
    "variants": metrics,
    "gates": {"frame1BodyOpticalCollisionPass": collision_pass},
    "strictVisualFinding": "The lower discovered path lies on the internal lid surface; propagation lifts a rigid lower-lid plate despite zero optical triangle overlap.",
    "derivedOnlyFromOwnedCC0Mainline": True,
    "integratedIntoContinuousBodyMesh": True,
    "rigTransferred": True,
    "websitePromotionApproved": False,
    "colorManagement": {"viewTransform": "Standard", "look": "None", "exposureEV": 0.0, "neutralWhiteLights": True},
    "status": status,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R442_NATIVE_EYELID_APERTURE=" + json.dumps(report, sort_keys=True))
