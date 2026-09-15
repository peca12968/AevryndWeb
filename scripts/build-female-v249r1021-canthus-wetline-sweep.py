"""Close the r1020 inner canthi and assign a dedicated wet eyelid margin."""

import json
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-dense-eyelid-patch-r1020-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-canthus-wetline-r1021-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1021-canthus-wetline-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1021-canthus-wetline-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
FRAMES = (1, 20, 33, 61)
VARIANTS = (
    ("a-subtle", 0.00020, (0.34, 0.10, 0.08, 1.0), 0.32),
    ("b-balanced", 0.00035, (0.28, 0.065, 0.055, 1.0), 0.27),
    ("c-defined", 0.00050, (0.22, 0.045, 0.038, 1.0), 0.22),
)


def mixed_coordinates(body):
    blocks = body.data.shape_keys.key_blocks
    coordinates = [item.co.copy() for item in blocks[0].data]
    for block in blocks[1:]:
        if block.mute or abs(block.value) < 1e-8:
            continue
        for index, coordinate in enumerate(coordinates):
            coordinate += block.value * (block.data[index].co - block.relative_key.data[index].co)
    return [body.matrix_world @ coordinate for coordinate in coordinates]


def eye_frames():
    result = {}
    for side in ("L", "R"):
        points = []
        for name in (f"Eye_{side}_Sclera", f"Eye_{side}_Cornea"):
            obj = bpy.data.objects[name]
            points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
        minimum = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
        maximum = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
        result[side] = ((minimum + maximum) * 0.5, (maximum - minimum) * 0.5)
    return result


def visible_inner_boundary(body, frames):
    points = mixed_coordinates(body); users = defaultdict(int)
    for polygon in body.data.polygons:
        vertices = list(polygon.vertices)
        for index, first in enumerate(vertices): users[tuple(sorted((first, vertices[(index + 1) % len(vertices)])))] += 1
    candidates = {"L": [], "R": []}
    for edge in body.data.edges:
        if users[tuple(sorted(edge.vertices))] != 1: continue
        midpoint = (points[edge.vertices[0]] + points[edge.vertices[1]]) * 0.5
        for side, (center, radius) in frames.items():
            if abs(midpoint.x - center.x) < radius.x * 1.25 and abs(midpoint.z - center.z) < radius.z * 0.85 and midpoint.y < -0.070:
                candidates[side].append(edge.index); break
    selected = {}; inventory = {}
    for side, indices in candidates.items():
        vertex_edges = defaultdict(set)
        for edge_index in indices:
            for vertex_index in body.data.edges[edge_index].vertices: vertex_edges[vertex_index].add(edge_index)
        remaining = set(indices); components = []
        while remaining:
            seed = remaining.pop(); stack = [seed]; component = {seed}
            while stack:
                edge_index = stack.pop(); neighbours = set()
                for vertex_index in body.data.edges[edge_index].vertices: neighbours.update(vertex_edges[vertex_index])
                fresh = neighbours & remaining; remaining.difference_update(fresh); component.update(fresh); stack.extend(fresh)
            components.append(component)
        chosen = min(components, key=lambda component: abs(len(component) - 48))
        selected[side] = sorted(chosen); inventory[side] = sorted((len(component) for component in components), reverse=True)
    return selected, inventory, points


def close_canthi(body, frames, edges, points, closure):
    inverse3 = body.matrix_world.inverted().to_3x3(); deltas = {}; counts = {"L": 0, "R": 0}
    for side, edge_indices in edges.items():
        center, radius = frames[side]
        vertices = {vertex for edge_index in edge_indices for vertex in body.data.edges[edge_index].vertices}
        for index in vertices:
            point = points[index]; u = (point.x - center.x) / radius.x; magnitude = abs(u)
            factor = max(0.0, min(1.0, (magnitude - 0.52) / 0.30))
            factor = factor * factor * (3.0 - 2.0 * factor)
            if factor <= 0.0: continue
            world_delta = Vector((-1.0 if u > 0.0 else 1.0, 0.0, 0.0)) * closure * factor
            deltas[index] = inverse3 @ world_delta; counts[side] += 1
    for block in body.data.shape_keys.key_blocks:
        for index, delta in deltas.items(): block.data[index].co += delta
    body.data.update()
    return {"movedVertices": len(deltas), "movedVerticesBySide": counts, "maximumDeltaMm": max((delta.length for delta in deltas.values()), default=0.0) * 1000.0}


def add_wetline_material(body, edges, color, roughness):
    material = bpy.data.materials.new("Aevrynd_EyelidWetline_R1021")
    material.use_nodes = True; material.diffuse_color = color
    bsdf = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = color; bsdf.inputs["Roughness"].default_value = roughness
    if "Coat Weight" in bsdf.inputs: bsdf.inputs["Coat Weight"].default_value = 0.18
    if "Coat Roughness" in bsdf.inputs: bsdf.inputs["Coat Roughness"].default_value = 0.10
    body.data.materials.append(material); material_index = len(body.data.materials) - 1
    boundary = {tuple(sorted(body.data.edges[index].vertices)) for values in edges.values() for index in values}
    assigned = 0
    for polygon in body.data.polygons:
        vertices = list(polygon.vertices)
        polygon_edges = {tuple(sorted((vertices[index], vertices[(index + 1) % len(vertices)]))) for index in range(len(vertices))}
        if polygon_edges & boundary:
            polygon.material_index = material_index; polygon.use_smooth = True; assigned += 1
    body.data.update(); return {"material": material.name, "materialSlot": material_index, "assignedPolygons": assigned, "baseColorLinearRGBA": list(color), "roughness": roughness}


def world_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph); mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]; polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False); evaluated.to_mesh_clear(); return tree


def collision_frames(body):
    scene = bpy.context.scene; results = {}; failures = []
    for frame in FRAMES:
        scene.frame_set(frame); depsgraph = bpy.context.evaluated_depsgraph_get(); depsgraph.update(); body_tree = world_tree(body, depsgraph); frame_result = {}
        for side in ("L", "R"):
            values = {}
            for layer in ("Sclera", "Cornea", "Iris", "UpperLashes", "LowerLashes"):
                values[layer] = len(body_tree.overlap(world_tree(bpy.data.objects[f"Eye_{side}_{layer}"], depsgraph)))
                if values[layer]: failures.append({"frame": frame, "side": side, "layer": layer, "triangleOverlapCount": values[layer]})
            frame_result[side] = values
        results[str(frame)] = frame_result
    return results, failures


def look_at(camera, target): camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


RENDER_DIR.mkdir(parents=True, exist_ok=True); variants = []
for label, closure, color, roughness in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); scene = bpy.context.scene; scene.frame_set(1); bpy.context.view_layer.update(); body = bpy.data.objects[BODY]; frames = eye_frames()
    edges, inventory, points = visible_inner_boundary(body, frames); edit = close_canthi(body, frames, edges, points, closure); material = add_wetline_material(body, edges, color, roughness); bpy.context.view_layer.update()
    collisions, failures = collision_frames(body); scene.frame_set(1); bpy.context.view_layer.update(); hidden = []
    for obj in scene.objects:
        if (obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type == "CURVES" or obj.name.endswith(("UpperLashes", "LowerLashes"))) and not obj.hide_render: obj.hide_render = True; hidden.append(obj.name)
    scene.render.resolution_x = scene.render.resolution_y = 900; camera = scene.camera; camera.data.lens = 105; rendered = []
    for view, location, target in (("front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.484)), ("three-quarter-left", (0.205, -0.425, 1.490), (0.0, -0.057, 1.482)), ("three-quarter-right", (-0.205, -0.425, 1.490), (0.0, -0.057, 1.482))):
        camera.location = location; look_at(camera, target); path = RENDER_DIR / f"{label}-{view}.png"; scene.render.filepath = str(path); bpy.ops.render.render(write_still=True); rendered.append(str(path))
    for name in hidden: bpy.data.objects[name].hide_render = False
    variants.append({"label": label, "closureMm": closure * 1000.0, "boundaryComponentEdgeCounts": inventory, "edit": edit, "wetline": material, "collisionFrames": collisions, "collisionFailures": failures, "rendered": rendered, "status": "TECHNICAL_PASS" if not failures else "TECHNICAL_FAIL"})
    if label == "a-subtle" and not failures:
        scene["aevrynd_mainline_revision"] = "v249r1021-subtle-canthus-wetline-study"; scene["aevrynd_mainline_parent"] = SOURCE.name; scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_REQUIRED"; scene["aevrynd_website_promotion"] = "forbidden"; bpy.context.preferences.filepaths.save_version = 0; bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {"source": str(SOURCE), "output": str(OUTPUT), "method": "move only the r1020 inner 48-edge ring inward at both canthi and assign its innermost band a separate Aevrynd-owned wetline material", "variants": variants, "selectedVariant": None, "status": "VISUAL_REVIEW_REQUIRED", "websitePromotionApproved": False}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1021_CANTHUS_WETLINE=" + json.dumps({"output": str(OUTPUT), "variants": [{"label": item["label"], "edit": item["edit"], "wetline": item["wetline"], "collisionFailures": len(item["collisionFailures"]), "status": item["status"]} for item in variants]}, sort_keys=True))
