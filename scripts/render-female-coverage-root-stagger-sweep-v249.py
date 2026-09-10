import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249.blend"
OUT = ROOT.parent / "Temp/female-realism/coverage-root-stagger-sweep-v249"


def components(mesh):
    adjacency = {vertex.index: set() for vertex in mesh.vertices}
    for edge in mesh.edges:
        a, b = edge.vertices
        adjacency[a].add(b)
        adjacency[b].add(a)
    remaining = set(adjacency)
    result = []
    while remaining:
        seed = remaining.pop()
        group = {seed}
        stack = [seed]
        while stack:
            current = stack.pop()
            for neighbor in adjacency[current]:
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    group.add(neighbor)
                    stack.append(neighbor)
        result.append(sorted(group))
    return result


def scalp_tree(scalp):
    points = [scalp.matrix_world @ vertex.co for vertex in scalp.data.vertices]
    faces = [tuple(polygon.vertices) for polygon in scalp.data.polygons]
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def apply(coverage, scalp, base, strength):
    for vertex, coordinate in zip(coverage.data.vertices, base):
        vertex.co = coordinate
    coverage.data.update()
    tree = scalp_tree(scalp)
    inverse = coverage.matrix_world.inverted()
    root_cards = []
    for group in components(coverage.data):
        ordered = sorted(group)
        pairs = [ordered[index:index + 2] for index in range(0, len(ordered), 2)]
        pair_centers = [sum((coverage.matrix_world @ coverage.data.vertices[index].co for index in pair), Vector()) / 2.0 for pair in pairs]
        if abs(pair_centers[-1].x) < abs(pair_centers[0].x):
            pairs.reverse()
            pair_centers.reverse()
        if abs(pair_centers[0].x) < 0.0075:
            root_cards.append((pairs, pair_centers))

    root_cards.sort(key=lambda item: item[1][0].y)
    moved_vertices = 0
    max_delta = 0.0
    for rank, (pairs, pair_centers) in enumerate(root_cards):
        rng = random.Random(25600 + rank)
        side = -1.0 if pair_centers[0].x < 0.0 else 1.0
        shift_x = strength * rng.uniform(0.0020, 0.0085)
        shift_y = strength * rng.uniform(-0.0032, 0.0032)
        phase_bias = strength * 0.0015 * math.sin(rank * 2.39996)
        for step, (pair, center) in enumerate(zip(pairs, pair_centers)):
            t = step / max(1, len(pairs) - 1)
            weight = max(0.0, 1.0 - t / 0.58)
            weight = weight * weight * (3.0 - 2.0 * weight)
            if weight <= 0.0:
                continue
            nearest = tree.find_nearest(center)
            clearance = nearest[3] if nearest else 0.0026
            candidate = center + Vector((side * (shift_x + phase_bias) * weight, shift_y * weight, 0.0))
            point, normal, _, _ = tree.find_nearest(candidate)
            normal.normalize()
            target = point + normal * max(0.00235, min(0.00315, clearance))
            delta = target - center
            for index in pair:
                world = coverage.matrix_world @ coverage.data.vertices[index].co
                coverage.data.vertices[index].co = inverse @ (world + delta)
                moved_vertices += 1
                max_delta = max(max_delta, delta.length)
    coverage.data.update()
    return {"root_cards": len(root_cards), "moved_vertices": moved_vertices, "max_delta_mm": max_delta * 1000.0}


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens, resolution=1000):
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(OUT / f"{name}.png")
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
coverage = bpy.data.objects["HairCoverageTiles_v246"]
scalp = bpy.data.objects["HairScalp"]
base = [vertex.co.copy() for vertex in coverage.data.vertices]
camera = bpy.data.objects["Aevrynd Review Camera"]
for label, strength in (("055", 0.55), ("085", 0.85), ("115", 1.15)):
    report = apply(coverage, scalp, base, strength)
    render(camera, f"hair-top-{label}", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78)
    render(camera, f"face-front-{label}", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88)
    render(camera, f"face-three-quarter-{label}", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88)
    print("COVERAGE_ROOT_STAGGER", label, report)
