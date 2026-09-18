"""Add an owned lower-lid tear meniscus ribbon from the current aperture topology."""
from collections import defaultdict
from pathlib import Path
import json
import os

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-anatomical-caruncle-r1101-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-lower-wetline-r1102-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1102-lower-wetline-sweep.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1102-lower-wetline"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
ORIGINAL_VERTEX_COUNT = 13817
FRAMES = (1, 20, 33, 61)
# label, ribbon width toward eye centre, forward offset from aperture (metres)
VARIANTS = (("a-fine", 0.00008, 0.00040), ("b-natural", 0.00012, 0.00060), ("c-visible", 0.00017, 0.00080))
SELECTED = "b-natural"
REQUESTED_VARIANT = os.environ.get("AEVRYND_VARIANT")


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def active_coordinates(body):
    blocks = body.data.shape_keys.key_blocks; coordinates = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or block.name in ("Aevrynd_MouthOpenTest_R1030", "Aevrynd_SmileTest_R1030") or abs(block.value) < 1e-8: continue
        for index, item in enumerate(block.data): coordinates[index] += block.value * (item.co - block.relative_key.data[index].co)
    return [body.matrix_world @ coordinate for coordinate in coordinates]


def ordered_loop(edges):
    adjacency = defaultdict(list)
    for a, b in edges: adjacency[a].append(b); adjacency[b].append(a)
    start = min(adjacency); loop, previous, current = [start], None, start
    while True:
        following = adjacency[current][0] if adjacency[current][0] != previous else adjacency[current][1]
        if following == start: break
        loop.append(following); previous, current = current, following
    return loop


def lower_paths(body):
    points = active_coordinates(body); outer_edges = []
    for polygon in body.data.polygons:
        old = [index for index in polygon.vertices if index < ORIGINAL_VERTEX_COUNT]
        wall = [index for index in polygon.vertices if ORIGINAL_VERTEX_COUNT <= index < ORIGINAL_VERTEX_COUNT + 180]
        if len(polygon.vertices) == 4 and len(old) == 2 and len(wall) == 2: outer_edges.append(tuple(old))
    unused = set(tuple(sorted(edge)) for edge in outer_edges); loops = []
    while unused:
        seed = next(iter(unused)); component, frontier = set(seed), list(seed)
        while frontier:
            vertex = frontier.pop()
            for edge in list(unused):
                if vertex in edge:
                    unused.remove(edge)
                    for item in edge:
                        if item not in component: component.add(item); frontier.append(item)
        loops.append(ordered_loop([edge for edge in outer_edges if edge[0] in component and edge[1] in component]))
    result = {}
    for loop in loops:
        side = "L" if sum(points[index].x for index in loop) > 0 else "R"
        oriented = lambda index: points[index].x if side == "L" else -points[index].x
        medial, lateral = min(loop, key=oriented), max(loop, key=oriented)
        start = loop.index(medial); rotated = loop[start:] + loop[:start]; split = rotated.index(lateral)
        paths = (rotated[:split + 1], [rotated[0]] + list(reversed(rotated[split:])))
        lower = min(paths, key=lambda path: sum(points[index].z for index in path) / len(path))
        trimmed = lower[5:-5]
        result[side] = [points[index].copy() for index in trimmed]
    if set(result) != {"L", "R"}: raise RuntimeError("paired lower lid paths were not found")
    return result


def eye_centres():
    result = {}
    for side in ("L", "R"):
        obj = bpy.data.objects[f"Eye_{side}_Sclera"]; points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
        result[side] = sum(points, Vector()) / len(points)
    return result


def wetline_material():
    material = bpy.data.materials.new("Aevrynd_LowerWetline_R1102"); material.use_nodes = True; material.surface_render_method = "BLENDED"
    bsdf = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = (0.37, 0.095, 0.075, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.14; bsdf.inputs["Specular IOR Level"].default_value = 0.34
    bsdf.inputs["Transmission Weight"].default_value = 0.12; bsdf.inputs["Alpha"].default_value = 0.82
    if bsdf.inputs.get("Coat Weight"): bsdf.inputs["Coat Weight"].default_value = 0.25
    if bsdf.inputs.get("Coat Roughness"): bsdf.inputs["Coat Roughness"].default_value = 0.10
    material["aevrynd_ownership"] = "procedural-in-project"; material["aevrynd_revision"] = "v249r1102"
    return material


def parent_to_head(obj, rig):
    world = obj.matrix_world.copy(); obj.parent = rig; obj.parent_type = "BONE"; obj.parent_bone = "head"; obj.matrix_world = world


def build_ribbon(side, path, centre, width, forward, body_tree, material, rig):
    vertices = []
    for point in path:
        radial = Vector((centre.x - point.x, 0.0, centre.z - point.z))
        if radial.length < 1e-9: radial = Vector((0.0, 0.0, 1.0))
        radial.normalize()
        outer = point + radial * 0.000018
        inner = point + radial * width
        hit, _normal, _face, _distance = body_tree.ray_cast(Vector((outer.x, -0.34, outer.z)), Vector((0.0, 1.0, 0.0)), 0.60)
        surface_y = hit.y if hit is not None and abs(hit.y - point.y) < 0.010 else point.y
        outer.y = surface_y - forward
        inner.y = surface_y - forward
        vertices.extend((tuple(outer), tuple(inner)))
    faces = [(2 * index, 2 * index + 1, 2 * index + 3, 2 * index + 2) for index in range(len(path) - 1)]
    mesh = bpy.data.meshes.new(f"Eye_{side}_LowerWetline_R1102Mesh"); mesh.from_pydata(vertices, [], faces); mesh.materials.append(material)
    for polygon in mesh.polygons: polygon.use_smooth = True
    obj = bpy.data.objects.new(f"Eye_{side}_LowerWetline_R1102", mesh); bpy.context.collection.objects.link(obj); parent_to_head(obj, rig)
    obj["aevrynd_layer"] = "eye.tear-meniscus.lower"; obj["aevrynd_revision"] = "v249r1102-lower-wetline"; obj["aevrynd_ownership"] = "procedural-in-project"
    return obj, {"pathPoints": len(path), "vertices": len(vertices), "faces": len(faces), "widthMm": width * 1000.0, "forwardOffsetMm": forward * 1000.0}


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph); mesh = evaluated.to_mesh(); vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    mesh.calc_loop_triangles(); triangles = [tuple(item.vertices) for item in mesh.loop_triangles]; evaluated.to_mesh_clear(); return BVHTree.FromPolygons(vertices, triangles, all_triangles=True)


def collision_frames(body, ribbons):
    results, failures = {}, []
    for frame in FRAMES:
        bpy.context.scene.frame_set(frame); deps = bpy.context.evaluated_depsgraph_get(); deps.update(); body_tree = world_tree(body, deps); result = {}
        for side, obj in ribbons.items():
            ribbon = world_tree(obj, deps); values = {"body": len(ribbon.overlap(body_tree))}
            for layer in ("Sclera", "Cornea", "Iris", "UpperLashes", "LowerLashes"):
                values[layer] = len(ribbon.overlap(world_tree(bpy.data.objects[f"Eye_{side}_{layer}"], deps)))
            result[side] = values
            for target, count in values.items():
                if count: failures.append({"frame": frame, "side": side, "target": target, "triangleOverlapCount": count})
        results[str(frame)] = result
    return results, failures


def render(scene, label, view):
    camera = scene.camera
    if view == "eye-front": camera.location, target, camera.data.lens, size = (0.0, -0.405, 1.449), (0.0, -0.105, 1.449), 135, (1400, 760)
    elif view == "eye-oblique": camera.location, target, camera.data.lens, size = (0.235, -0.405, 1.451), (0.0, -0.105, 1.449), 135, (1400, 900)
    else: camera.location, target, camera.data.lens, size = (0.0, -0.72, 1.445), (0.0, -0.025, 1.445), 88, (1000, 1000)
    look_at(camera, target); scene.render.resolution_x, scene.render.resolution_y = size; scene.render.resolution_percentage = 100
    path = OUT / f"{label}-{view}.png"; scene.render.filepath = str(path); bpy.ops.render.render(write_still=True); return str(path)


OUT.mkdir(parents=True, exist_ok=True); variants = []
active_variants = tuple(item for item in VARIANTS if REQUESTED_VARIANT in (None, item[0]))
if not active_variants: raise RuntimeError(f"unknown AEVRYND_VARIANT={REQUESTED_VARIANT}")
for label, width, forward in active_variants:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); scene = bpy.context.scene; scene.frame_set(1); body = bpy.data.objects[BODY]; rig = bpy.data.objects["AevryndFemaleRig"]
    paths, centres, material = lower_paths(body), eye_centres(), wetline_material()
    # The right lower path is the collision-clean topology branch; mirror it to
    # remove the legacy left-path corner fold while retaining bilateral anatomy.
    canonical = paths["R"][1:-1]
    paths["R"] = canonical
    paths["L"] = [Vector((-point.x, point.y, point.z)) for point in canonical]
    ribbons = {}; geometry = {}; deps = bpy.context.evaluated_depsgraph_get(); deps.update(); body_projection = world_tree(body, deps)
    for side in ("L", "R"): ribbons[side], geometry[side] = build_ribbon(side, paths[side], centres[side], width, forward, body_projection, material, rig)
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")): obj.hide_render = True
    bpy.context.view_layer.update(); collisions, failures = collision_frames(body, ribbons); scene.frame_set(1); bpy.context.view_layer.update(); renders = [render(scene, label, view) for view in ("eye-front", "eye-oblique", "face-front")]
    status = "TECHNICAL_PASS" if not failures else "TECHNICAL_FAIL"; variants.append({"label": label, "geometry": geometry, "collisionFrames": collisions, "collisionFailures": failures, "renders": renders, "status": status})
    if label == SELECTED and status == "TECHNICAL_PASS":
        body["aevrynd_revision"] = "v249r1102-lower-wetline"; body["aevrynd_source"] = SOURCE.name
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"; scene["aevrynd_website_promotion"] = "forbidden"; bpy.context.preferences.filepaths.save_version = 0; bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {"revision": "v249r1102-lower-wetline-sweep", "source": str(SOURCE), "output": str(OUTPUT), "method": "derive independent lower tear-meniscus ribbons from the current active eyelid aperture, inset them toward each eye centre and shade them with a restrained owned wet-tissue material", "variants": variants, "selectedVariant": SELECTED, "externalDependencies": [], "websitePromotionApproved": False, "candidateStatus": "VISUAL_REVIEW_PENDING"}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1102_WETLINE=" + json.dumps({"selected": SELECTED, "variants": [{"label": item["label"], "geometry": item["geometry"], "failures": len(item["collisionFailures"]), "status": item["status"]} for item in variants]}, sort_keys=True))
