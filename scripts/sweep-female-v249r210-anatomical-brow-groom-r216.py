import bisect
import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r216-anatomical-brow-groom-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-anatomical-brow-groom-r216.sweep-report.json"
VARIANTS = (
    ("a-control", 0, 0.0, 0.0, 0.0, 0.0, True),
    ("b-soft-microfill", 160, 0.018, 0.46, 0.58, 0.35, True),
    ("c-irregular-microfill", 240, 0.017, 0.52, 0.52, 0.55, True),
    ("d-short-replacement", 420, 0.022, 0.62, 0.72, 0.42, False),
)


def hash_signed(value):
    raw = math.sin(value * 12.9898 + 78.233) * 43758.5453
    return 2.0 * (raw - math.floor(raw)) - 1.0


def copied_material(source_name, output_name, alpha):
    material = bpy.data.materials[source_name].copy()
    material.name = output_name
    for node in material.node_tree.nodes:
        if node.type == "BSDF_PRINCIPLED" and "Alpha" in node.inputs:
            node.inputs["Alpha"].default_value = alpha
            break
    return material


def surface_triangles(surface):
    matrix = surface.matrix_world
    normal_matrix = matrix.to_3x3().inverted().transposed()
    triangles = []
    for polygon in surface.data.polygons:
        normal = (normal_matrix @ polygon.normal).normalized()
        if abs(normal.y) < 0.20:
            continue
        if normal.y > 0.0:
            normal.negate()
        indices = list(polygon.vertices)
        for offset in range(1, len(indices) - 1):
            points = [matrix @ surface.data.vertices[index].co for index in (indices[0], indices[offset], indices[offset + 1])]
            cross = (points[1] - points[0]).cross(points[2] - points[0])
            area = 0.5 * cross.length
            if area > 1e-12:
                triangles.append((points, normal, area))
    return triangles


def sample_surface(triangles, count, seed):
    cumulative = []
    total = 0.0
    for _points, _normal, area in triangles:
        total += area
        cumulative.append(total)
    rng = random.Random(seed)
    samples = []
    for _ in range(count):
        selected = min(len(triangles) - 1, bisect.bisect_left(cumulative, rng.random() * total))
        points, normal, _area = triangles[selected]
        r1 = math.sqrt(rng.random())
        r2 = rng.random()
        weights = (1.0 - r1, r1 * (1.0 - r2), r1 * r2)
        point = sum((points[index] * weights[index] for index in range(3)), Vector())
        samples.append((point, normal))
    return samples, total


def make_tube(vertices, faces, centers, tangent, normal, root_radius, material_index):
    side = tangent.cross(normal).normalized()
    up = tangent.cross(side).normalized()
    start = len(vertices)
    ring_count = len(centers)
    for ring_index, center in enumerate(centers):
        fraction = ring_index / (ring_count - 1)
        radius = root_radius * max(0.12, (1.0 - fraction) ** 0.72)
        for corner in range(3):
            angle = 2.0 * math.pi * corner / 3.0
            vertices.append(center + radius * (math.cos(angle) * side + math.sin(angle) * up))
    first_face = len(faces)
    for ring_index in range(ring_count - 1):
        for corner in range(3):
            a = start + ring_index * 3 + corner
            b = start + ring_index * 3 + (corner + 1) % 3
            c = start + (ring_index + 1) * 3 + (corner + 1) % 3
            d = start + (ring_index + 1) * 3 + corner
            faces.append((a, b, c, d))
    faces.append((start + 2, start + 1, start))
    tip = start + (ring_count - 1) * 3
    faces.append((tip, tip + 1, tip + 2))
    return first_face, len(faces), material_index


def create_brow_groom(side, count, width_mm, length_scale, alpha, direction_jitter, keep_original):
    source_fibers = bpy.data.objects[f"Brow_{side}"]
    surface = bpy.data.objects[f"Brow_{side}_Density"]
    source_fibers.hide_render = not keep_original
    triangles = surface_triangles(surface)
    samples, area = sample_surface(triangles, count, 2150 + (1 if side == "L" else 2))
    all_surface_points = [point for triangle, _normal, _area in triangles for point in triangle]
    x_min = min(abs(point.x) for point in all_surface_points)
    x_max = max(abs(point.x) for point in all_surface_points)
    side_sign = 1.0 if side == "L" else -1.0
    vertices = []
    faces = []
    face_materials = []
    lengths = []
    for index, (root, normal) in enumerate(samples):
        t = max(0.0, min(1.0, (abs(root.x) - x_min) / max(1e-8, x_max - x_min)))
        # Human eyebrow growth transitions from upright at the medial head,
        # through an oblique body, to a nearly lateral tail.  Apply bounded
        # per-fiber angular variation so the groom does not read as a brush.
        base_angle = math.radians(68.0 * (1.0 - t) + 4.0 * t)
        angle_jitter = direction_jitter * math.radians(26.0) * hash_signed(index + (47 if side == "R" else 0))
        angle = base_angle + angle_jitter
        desired = Vector((side_sign * math.cos(angle), 0.0, math.sin(angle)))
        tangent = (desired - normal * desired.dot(normal)).normalized()
        length_mm = length_scale * (3.2 + 1.25 * math.sin(math.pi * t) - 0.55 * max(0.0, (t - 0.72) / 0.28))
        length_mm += 0.28 * hash_signed(index + 91)
        length = max(0.0012, length_mm / 1000.0)
        lengths.append(length * 1000.0)
        root_lift = 0.00010
        centers = []
        for fraction in (0.0, 0.32, 0.68, 1.0):
            lift = root_lift + 0.00024 * math.sin(math.pi * fraction)
            bend = 0.00014 * fraction * (1.0 - fraction) * hash_signed(index + 173)
            centers.append(root + tangent * (length * fraction) + normal * lift + Vector((0.0, 0.0, bend)))
        first, last, material_index = make_tube(vertices, faces, centers, tangent, normal, width_mm / 1000.0, index % 5 == 0)
        face_materials.extend([material_index] * (last - first))

    mesh = bpy.data.meshes.new(f"Aevrynd_Brow_{side}_AnatomicalGroom_R216_Mesh")
    local_vertices = [surface.matrix_world.inverted() @ point for point in vertices]
    mesh.from_pydata(local_vertices, [], faces)
    mesh.materials.append(copied_material("Aevrynd_Brow_Hair_v39_Dark", f"Aevrynd_Brow_AnatomicalGroom_Dark_R216_{side}", alpha))
    mesh.materials.append(copied_material("Aevrynd_Brow_Hair_v39_Warm", f"Aevrynd_Brow_AnatomicalGroom_Warm_R216_{side}", alpha * 0.92))
    for polygon, material_index in zip(mesh.polygons, face_materials):
        polygon.material_index = material_index
        polygon.use_smooth = True
    mesh.update()
    obj = surface.copy()
    obj.data = mesh
    obj.name = f"Brow_{side}_AnatomicalGroom_R216"
    for collection in surface.users_collection:
        collection.objects.link(obj)
    obj["aevrynd_layer"] = "face.eyebrow.anatomical_microgroom"
    obj["aevrynd_revision"] = "v249r216"
    obj["aevrynd_source_surface"] = surface.name
    obj["aevrynd_runtime_dependency"] = "none"
    return obj, {
        "fibers": count,
        "vertices": len(mesh.vertices),
        "polygons": len(mesh.polygons),
        "sourceSurfaceAreaM2": area,
        "rootLiftMm": root_lift * 1000.0,
        "rootRadiusMm": width_mm,
        "materialAlpha": alpha,
        "directionJitter": direction_jitter,
        "keepsOriginalFibers": keep_original,
        "lengthMm": {"min": min(lengths), "mean": sum(lengths) / len(lengths), "max": max(lengths)},
        "binding": "copied head-bone parent from density surface",
    }


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, filename, location, target, lens, size):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "variants": {}, "status": "VISUAL_SELECTION_PENDING"}
for label, count, width_mm, length_scale, alpha, direction_jitter, keep_original in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    metrics = {"fibersPerSide": count, "rootRadiusMm": width_mm, "lengthScale": length_scale, "materialAlpha": alpha, "directionJitter": direction_jitter, "keepsOriginalFibers": keep_original, "layers": {}}
    if count:
        for side in ("L", "R"):
            obj, detail = create_brow_groom(side, count, width_mm, length_scale, alpha, direction_jitter, keep_original)
            metrics["layers"][obj.name] = detail
    camera = bpy.data.objects["Aevrynd Review Camera"]
    views = (
        ("01-brows-front", (0.0, -0.445, 1.638), (0.0, -0.076, 1.638), 132, (1280, 760)),
        ("02-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000)),
        ("03-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88, (1000, 1000)),
        ("04-brow-three-quarter", (0.225, -0.390, 1.650), (0.018, -0.080, 1.638), 138, (1100, 900)),
    )
    for view_name, location, target, lens, size in views:
        render(camera, f"{label}-{view_name}.png", location, target, lens, size)
    report["variants"][label] = metrics
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R216_ANATOMICAL_BROW_GROOM=" + json.dumps(report, sort_keys=True))
