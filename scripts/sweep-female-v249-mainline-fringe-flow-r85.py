import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-cleanup-r84.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-fringe-flow-r85-sweep"
MAIN = "AevryndFemaleGuideBob_v249r25"
SCALP = "AevryndFemaleScalpCoverage_v378"
POINTS = 20
FAMILY_SIZE = 25


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def world_bvh(obj):
    vertices = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    faces = [tuple(poly.vertices) for poly in obj.data.polygons]
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def front_families(data):
    selected = []
    for family in range(len(data.curves) // FAMILY_SIZE):
        curve = data.curves[family * FAMILY_SIZE]
        root = data.points[curve.first_point_index].position
        tip = data.points[curve.first_point_index + curve.points_length - 1].position
        if root.y < -0.060 and root.z > 1.585 and tip.x > 0.055:
            selected.append(family)
    return selected


def build_surface_route(tree, root, family, route_points):
    route = [root.copy()]
    current = root.copy()
    # Front fringe grows sideways from the part and slightly toward the crown.
    # Projecting each step back to the true scalp prevents the straight chord
    # that currently cuts across the forehead.
    for index in range(1, route_points):
        phase = math.sin((family + 1) * 1.618 + index * 0.73)
        desired = Vector((1.0, 0.22 + 0.08 * phase, -0.05))
        nearest = tree.find_nearest(current)
        if nearest is None:
            route.append(current.copy())
            continue
        normal = nearest[1].normalized()
        tangent = desired - normal * desired.dot(normal)
        if tangent.length_squared < 1.0e-10:
            tangent = Vector((1.0, 0.0, 0.0))
        tangent.normalize()
        guess = current + tangent * (0.0105 + 0.0015 * phase)
        hit = tree.find_nearest(guess, 0.035)
        if hit is None:
            current = guess
        else:
            clearance = 0.0011 + 0.00035 * index
            current = hit[0] + hit[1].normalized() * clearance
        route.append(current.copy())
    return route


def cubic_bezier(p0, p1, p2, p3, t):
    u = 1.0 - t
    return u ** 3 * p0 + 3.0 * u * u * t * p1 + 3.0 * u * t * t * p2 + t ** 3 * p3


def rebuild(data, tree, original, hair_matrix, strength, route_points):
    inverse = hair_matrix.inverted()
    for index, position in enumerate(original):
        data.points[index].position = position
    selected = front_families(data)
    maximum = 0.0
    for family in selected:
        representative = data.curves[family * FAMILY_SIZE]
        rep_root = hair_matrix @ data.points[representative.first_point_index].position
        route = build_surface_route(tree, rep_root, family, route_points)
        junction = route[-1]
        for follow in range(FAMILY_SIZE):
            curve = data.curves[family * FAMILY_SIZE + follow]
            root = hair_matrix @ data.points[curve.first_point_index].position
            tip = hair_matrix @ data.points[curve.first_point_index + curve.points_length - 1].position
            root_offset = root - rep_root
            # Keep the authored, collision-safe tip and use a smooth gravity arc
            # after the scalp-following section.
            control1 = junction + Vector((0.020, 0.006, -0.015))
            control2 = tip + Vector((0.010, -0.002, 0.070))
            follow_phase = math.sin((follow + 1) * 2.399963 + family * 0.37)
            for point_index in range(1, curve.points_length - 1):
                flat = curve.first_point_index + point_index
                t = point_index / (curve.points_length - 1)
                original_world = hair_matrix @ original[flat]
                split = (route_points - 1) / (curve.points_length - 1)
                if t <= split:
                    route_position = t / max(split, 1.0e-6) * (route_points - 1)
                    lo = min(route_points - 2, int(route_position))
                    frac = route_position - lo
                    target = route[lo].lerp(route[lo + 1], frac)
                    target += root_offset * (1.0 - 0.35 * smoothstep(t / split))
                else:
                    u = (t - split) / max(1.0e-6, 1.0 - split)
                    target = cubic_bezier(junction + root_offset * 0.65, control1, control2, tip, u)
                    # Sub-millimetre variation keeps follows from sharing a
                    # perfectly synchronous highlight without opening gaps.
                    target.y -= 0.0008 * follow_phase * math.sin(math.pi * u)
                    target.z += 0.0012 * follow_phase * math.sin(math.pi * u)
                blend = strength * smoothstep((t - 0.015) / 0.18) * (1.0 - smoothstep((t - 0.90) / 0.10))
                adjusted = original_world.lerp(target, blend)
                data.points[flat].position = inverse @ adjusted
                maximum = max(maximum, (adjusted - original_world).length)
    data.update_tag()
    return {"families": selected, "family_count": len(selected), "curves": len(selected) * FAMILY_SIZE, "max_displacement_mm": maximum * 1000.0}


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
hair = bpy.data.objects[MAIN]
tree = world_bvh(bpy.data.objects[SCALP])
original = [point.position.copy() for point in hair.data.points]
views = (
    ("face", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("three-quarter", (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82),
    ("profile", (2.15, 0.0, 1.57), (0.0, 0.0, 1.55), 86),
    ("top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78),
)
variants = (
    ("control", 0.0, 7),
    ("gentle", 0.34, 6),
    ("moderate", 0.50, 7),
    ("short-route", 0.72, 7),
    ("balanced", 0.88, 9),
    ("long-route", 1.0, 11),
)
reports = {}
for label, strength, route_points in variants:
    reports[label] = rebuild(hair.data, tree, original, hair.matrix_world, strength, route_points)
    for view, location, target, lens in views:
        render(camera, f"{label}-{view}", location, target, lens)

payload = {
    "source": str(SOURCE),
    "variants": reports,
    "method": "root/tip locked front guides projected along the actual scalp, then joined to a gravity Bezier segment",
}
(OUT / "report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("AEVRYND_V249_FRINGE_FLOW_R85_SWEEP=" + json.dumps(payload, sort_keys=True))
