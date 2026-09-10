import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-radial-drape-hair-r92.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-smooth-clearance-hair-r93.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-cc0-smooth-clearance-hair-r93"
MAIN = "AevryndFemaleCC0LongHairFitMain_v249r86"
FLY = "AevryndFemaleCC0LongHairFitFlyaway_v249r86"
ROOT_LAYER = "AevryndFemaleCC0LongHairRootDensity_v249r93"
HAIR = (MAIN, FLY)
SOLIDS = (
    "AevryndFemaleBodyBaseV118",
    "Clothing_Bandeau_v160",
    "Clothing_BandeauBinding_v162",
    "Clothing_BodyFitShorts_v135",
)
TARGET = 0.0015
NEAR = 0.050


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def collect_smooth_corrections(obj, trees):
    inverse_rotation = obj.matrix_world.inverted().to_3x3()
    corrections = [Vector((0.0, 0.0, 0.0)) for _ in obj.data.curves]
    violation_count = 0
    maximum_penetration = 0.0
    for curve_index, curve in enumerate(obj.data.curves):
        best = Vector((0.0, 0.0, 0.0))
        for local_index in range(1, curve.points_length):
            blend = smoothstep((local_index / max(1, curve.points_length - 1) - 0.08) / 0.92) ** 2
            if blend < 0.015:
                continue
            point = obj.data.points[curve.first_point_index + local_index]
            world = obj.matrix_world @ point.position
            for tree in trees:
                hit = tree.find_nearest(world)
                if hit is None or hit[1] is None or hit[3] > NEAR:
                    continue
                normal = hit[1].normalized()
                signed = (world - hit[0]).dot(normal)
                if signed >= TARGET:
                    continue
                violation_count += 1
                maximum_penetration = max(maximum_penetration, TARGET - signed)
                local_normal = inverse_rotation @ normal
                if local_normal.length_squared:
                    local_normal.normalize()
                required = min(0.045, (TARGET - signed) / max(0.10, blend) + 0.0005)
                candidate = local_normal * required
                if candidate.length > best.length:
                    best = candidate
        corrections[curve_index] = best
    return corrections, violation_count, maximum_penetration


def apply_smooth_corrections(obj, corrections):
    corrected = 0
    maximum = 0.0
    for curve_index, curve in enumerate(obj.data.curves):
        correction = corrections[curve_index]
        if not correction.length_squared:
            continue
        corrected += 1
        maximum = max(maximum, correction.length)
        for local_index in range(1, curve.points_length):
            t = local_index / max(1, curve.points_length - 1)
            blend = smoothstep((t - 0.08) / 0.92) ** 2
            obj.data.points[curve.first_point_index + local_index].position += correction * blend
    obj.data.update_tag()
    return corrected, maximum


def rebuild_root_density(scene, main):
    old = bpy.data.objects.get("AevryndFemaleCC0LongHairRootDensity_v249r90")
    if old:
        old_data = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if old_data.users == 0:
            bpy.data.hair_curves.remove(old_data)
    records = []
    for curve_index, curve in enumerate(main.data.curves):
        if curve_index % 3:
            continue
        count = min(4, curve.points_length)
        source = [main.matrix_world @ main.data.points[curve.first_point_index + i].position for i in range(count)]
        if len(source) < 3:
            continue
        for sign in (-1.0, 1.0):
            strand = []
            for index, point in enumerate(source):
                before = source[max(0, index - 1)]
                after = source[min(len(source) - 1, index + 1)]
                tangent = (after - before).normalized()
                radial = Vector((point.x, point.y, 0.0))
                if radial.length_squared < 1.0e-10:
                    radial = Vector((1.0, 0.0, 0.0))
                radial.normalize()
                side = radial.cross(tangent)
                if side.length_squared < 1.0e-10:
                    side = Vector((1.0, 0.0, 0.0))
                side.normalize()
                strand.append(point + side * sign * 0.00028)
            records.append(strand)
    data = bpy.data.hair_curves.new(ROOT_LAYER + "Data")
    data.add_curves([len(strand) for strand in records])
    radius = data.attributes.get("radius") or data.attributes.new("radius", "FLOAT", "POINT")
    flat = 0
    for strand in records:
        for point_index, point in enumerate(strand):
            data.points[flat].position = point
            t = point_index / max(1, len(strand) - 1)
            radius.data[flat].value = 0.000018 * (1.0 - t) + 0.000002 * t
            flat += 1
    if main.data.materials:
        data.materials.append(main.data.materials[0])
    root = bpy.data.objects.new(ROOT_LAYER, data)
    scene.collection.objects.link(root)
    root["aevrynd_layer"] = "hair.root_density.short-fibers"
    root["aevrynd_revision"] = "v249-mainline-cc0-smooth-clearance-hair-r93"
    root["aevrynd_runtime_dependency"] = "none"
    rig = bpy.data.objects["AevryndFemaleRig"]
    world = root.matrix_world.copy()
    root.parent = rig
    root.parent_type = "BONE"
    root.parent_bone = "head"
    root.matrix_world = world
    return root, len(records), len(data.points)


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
passes = []
for pass_index in range(6):
    combined = {name: [Vector((0.0, 0.0, 0.0)) for _ in bpy.data.objects[name].data.curves] for name in HAIR}
    pass_record = {"pass": pass_index + 1, "frames": {}}
    for frame in (1, 20):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        trees = [evaluated_tree(bpy.data.objects[name], depsgraph) for name in SOLIDS]
        frame_record = {}
        for name in HAIR:
            obj = bpy.data.objects[name]
            corrections, violations, maximum = collect_smooth_corrections(obj, trees)
            for index, correction in enumerate(corrections):
                if correction.length > combined[name][index].length:
                    combined[name][index] = correction
            frame_record[name] = {"violatingSamples": violations, "maximumRequiredM": maximum}
        pass_record["frames"][str(frame)] = frame_record
    scene.frame_set(1)
    for name in HAIR:
        corrected, maximum = apply_smooth_corrections(bpy.data.objects[name], combined[name])
        pass_record[name] = {"correctedCurves": corrected, "maximumSmoothDisplacementM": maximum}
    passes.append(pass_record)

main = bpy.data.objects[MAIN]
root, root_curves, root_points = rebuild_root_density(scene, main)
for name in HAIR:
    obj = bpy.data.objects[name]
    obj["aevrynd_revision"] = "v249-mainline-cc0-smooth-clearance-hair-r93"
    obj["aevrynd_collision_frames"] = "1,20"
    obj["aevrynd_collision_clearance_m"] = TARGET
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "cc0-smooth-clearance-hair-r93"
scene["aevrynd_release_state"] = "R93_STATIC_COLLISION_AND_STRICT_VISUAL_REVIEW_REQUIRED"
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
for args in (
    ("01-front", (0.0, -2.15, 1.55), (0.0, 0.0, 1.55), 82),
    ("02-three-quarter", (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82),
    ("03-profile", (2.15, 0.0, 1.57), (0.0, 0.0, 1.55), 86),
    ("04-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82),
    ("05-top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78),
    ("06-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
):
    render(camera, *args)

report = {"source": str(SOURCE), "output": str(OUTPUT), "passes": passes,
          "rootDensity": {"curves": root_curves, "points": root_points},
          "status": "STATIC_COLLISION_AND_STRICT_VISUAL_REVIEW_REQUIRED"}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_CC0_SMOOTH_CLEARANCE_R93=" + json.dumps({
    "output": str(OUTPUT), "rootCurves": root_curves,
    "lastPass": passes[-1], "status": report["status"],
}, sort_keys=True))
