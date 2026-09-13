import heapq
import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-layered-optical-stack-r420.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-native-eyelid-loop-r441-study.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-native-eyelid-loop-r441.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r441-native-eyelid-loop-discovery"
BODY = "AevryndFemaleBody_CC0_R249"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def curve_points(name):
    obj = bpy.data.objects[name]
    spline = obj.data.splines[0]
    if spline.type == "BEZIER":
        points = [obj.matrix_world @ point.co for point in spline.bezier_points]
    else:
        points = [obj.matrix_world @ point.co.xyz for point in spline.points]
    return sorted(points, key=lambda point: point.x)


def interpolate(samples, x):
    if x <= samples[0].x:
        return samples[0]
    if x >= samples[-1].x:
        return samples[-1]
    low, high = 0, len(samples) - 1
    while high - low > 1:
        middle = (low + high) // 2
        if samples[middle].x <= x:
            low = middle
        else:
            high = middle
    a, b = samples[low], samples[high]
    factor = (x - a.x) / max(1e-9, b.x - a.x)
    return a.lerp(b, factor)


def nearest_vertex(indices, points, target):
    return min(indices, key=lambda index: (points[index] - target).length_squared)


def shortest_margin_path(start, end, candidates, neighbors, points, samples, upper):
    distances = {start: 0.0}
    previous = {}
    queue = [(0.0, start)]
    while queue:
        distance, current = heapq.heappop(queue)
        if distance != distances.get(current):
            continue
        if current == end:
            break
        current_point = points[current]
        for neighbor in neighbors[current]:
            if neighbor not in candidates:
                continue
            point = points[neighbor]
            target = interpolate(samples, point.x)
            vertical_error = abs(point.z - target.z)
            depth_error = abs(point.y - target.y)
            wrong_side = max(0.0, target.z - point.z) if upper else max(0.0, point.z - target.z)
            reverse_x = max(0.0, current_point.x - point.x)
            edge_length = (point - current_point).length
            cost = edge_length * (1.0 + 90.0 * vertical_error + 18.0 * depth_error)
            cost += 5.0 * wrong_side + 8.0 * reverse_x
            candidate_distance = distance + cost
            if candidate_distance < distances.get(neighbor, float("inf")):
                distances[neighbor] = candidate_distance
                previous[neighbor] = current
                heapq.heappush(queue, (candidate_distance, neighbor))
    if end not in distances:
        raise RuntimeError("No native topology path found")
    path = [end]
    while path[-1] != start:
        path.append(previous[path[-1]])
    path.reverse()
    return path, distances[end]


def make_emission_material(name, color):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Emission Color"].default_value = (*color, 1.0)
    shader.inputs["Emission Strength"].default_value = 3.0
    shader.inputs["Roughness"].default_value = 0.25
    return material


def make_path_curve(name, points, material):
    curve = bpy.data.curves.new(name + "Geometry", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = 0.00034
    curve.bevel_resolution = 2
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for slot, point in zip(spline.points, points):
        slot.co = (*point, 1.0)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    return obj


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
body.data.calc_loop_triangles()
points = [body.matrix_world @ vertex.co for vertex in body.data.vertices]
normal_matrix = body.matrix_world.to_3x3()
normals = [(normal_matrix @ vertex.normal).normalized() for vertex in body.data.vertices]
neighbors = [set() for _ in body.data.vertices]
for edge in body.data.edges:
    first, second = edge.vertices
    neighbors[first].add(second)
    neighbors[second].add(first)

upper_material = make_emission_material("Aevrynd R441 Native Upper Path", (0.0, 0.55, 1.0))
lower_material = make_emission_material("Aevrynd R441 Native Lower Path", (1.0, 0.16, 0.5))
results = {}
for side in ("L", "R"):
    upper = curve_points(f"AevryndEye_{side}_UpperLidMargin_R258")
    lower = curve_points(f"AevryndEye_{side}_LowerLidMargin_R258")
    x_min, x_max = upper[0].x, upper[-1].x
    z_min = min(point.z for point in lower) - 0.005
    z_max = max(point.z for point in upper) + 0.006
    candidates = {
        index for index, (point, normal) in enumerate(zip(points, normals))
        if x_min - 0.004 <= point.x <= x_max + 0.004
        and z_min <= point.z <= z_max
        and point.y < -0.105
        and normal.y < -0.18
    }
    left_target = (upper[0] + lower[0]) * 0.5
    right_target = (upper[-1] + lower[-1]) * 0.5
    start = nearest_vertex(candidates, points, left_target)
    end = nearest_vertex(candidates, points, right_target)
    upper_path, upper_cost = shortest_margin_path(start, end, candidates, neighbors, points, upper, True)
    lower_path, lower_cost = shortest_margin_path(start, end, candidates, neighbors, points, lower, False)
    make_path_curve(f"AevryndEye_{side}_NativeUpperPath_R441", [points[index] for index in upper_path], upper_material)
    make_path_curve(f"AevryndEye_{side}_NativeLowerPath_R441", [points[index] for index in lower_path], lower_material)
    results[side] = {
        "candidateVertices": len(candidates),
        "canthusVertices": [start, end],
        "upper": {"vertices": upper_path, "count": len(upper_path), "cost": upper_cost},
        "lower": {"vertices": lower_path, "count": len(lower_path), "cost": lower_cost},
        "sharedInteriorVertices": sorted(set(upper_path[1:-1]) & set(lower_path[1:-1])),
    }

for obj in bpy.data.objects:
    name = obj.name.lower()
    if obj == body or "nativeupperpath_r441" in name or "nativelowerpath_r441" in name:
        obj.hide_render = False
    elif any(token in name for token in ("eye", "caruncle", "tear", "brow", "lash")):
        obj.hide_render = False
    elif obj.type in {"MESH", "CURVES", "CURVE"}:
        obj.hide_render = True

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
scene.camera = camera
views = (
    ("front", (0.0, -0.63, 1.607), (0.0, -0.035, 1.607), 105),
    ("three-quarter", (0.31, -0.57, 1.618), (0.0, -0.025, 1.605), 100),
    ("eyes-close", (0.0, -0.44, 1.607), (0.0, -0.045, 1.607), 118),
)
for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 1200
    scene.render.filepath = str(RENDER_DIR / f"r441-{name}.png")
    bpy.ops.render.render(write_still=True)

path_gate = all(not result["sharedInteriorVertices"] and result["upper"]["count"] >= 8 and result["lower"]["count"] >= 8 for result in results.values())
status = "PARTIAL_PASS_UPPER_PATH_ONLY_LOWER_PATH_FAIL" if path_gate else "REJECTED_NATIVE_PATH_DISCOVERY_GATE_FAIL"
scene["aevrynd_native_eyelid_loop_discovery"] = "v249r441-study"
scene["aevrynd_release_state"] = status
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "renderDirectory": str(RENDER_DIR),
    "method": "Dijkstra path discovery over the existing continuous high-density body topology, guided by the authored upper and lower lid margins. No body vertices are changed.",
    "eyes": results,
    "gates": {"separateUpperLowerPaths": path_gate},
    "bodyGeometryChanged": False,
    "strictVisualFinding": "Upper paths follow the external lid margin, but both lower paths detour through the inner eyelid surface and cannot drive deformation.",
    "derivedOnlyFromOwnedCC0Mainline": True,
    "websitePromotionApproved": False,
    "colorManagement": {"viewTransform": "Standard", "look": "None", "exposureEV": 0.0},
    "status": status,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R441_NATIVE_EYELID_LOOP=" + json.dumps({"eyes": results, "status": status}, sort_keys=True))
