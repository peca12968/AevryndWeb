import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-pruned-curve-outlier-r296.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-macro-lock-hierarchy-r297.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-macro-lock-hierarchy-r297.build-report.json"
AUDIT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-macro-lock-hierarchy-r297.audit.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r297-macro-lock-hierarchy"
BODY = "AevryndFemaleBody_CC0_R249"
PRIMARY = "AevryndFemalePrimaryClumps_R264"
FILL = "AevryndFemaleSecondaryFill_R264"
FLY = "AevryndFemaleFlyaways_R264"
LAYERS = (PRIMARY, FILL, FLY)
POINTS = 24
CLUSTERS = 40
FRAMES = (1, 33, 61)
CLEARANCE = 0.0020


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def feature(path):
    result = []
    for point_index, weight in ((0, 5.0), (6, 3.3), (13, 2.0), (19, 1.2), (23, 0.8)):
        point = path[point_index]
        result.extend((point.x * weight, point.y * weight, point.z * weight))
    return result


def distance_squared(left, right):
    return sum((a - b) ** 2 for a, b in zip(left, right))


def cluster_guides(paths):
    features = [feature(path) for path in paths]
    rng = random.Random(2970040)
    seeds = [rng.randrange(len(features))]
    minimum = [distance_squared(item, features[seeds[0]]) for item in features]
    while len(seeds) < CLUSTERS:
        chosen = max(range(len(features)), key=minimum.__getitem__)
        seeds.append(chosen)
        for index, item in enumerate(features):
            minimum[index] = min(minimum[index], distance_squared(item, features[chosen]))
    centroids = [features[index][:] for index in seeds]
    assignments = [0] * len(features)
    for _ in range(9):
        assignments = [min(range(CLUSTERS), key=lambda cluster: distance_squared(item, centroids[cluster])) for item in features]
        sums = [[0.0] * len(features[0]) for _ in range(CLUSTERS)]
        counts = [0] * CLUSTERS
        for item, cluster in zip(features, assignments):
            counts[cluster] += 1
            for index, value in enumerate(item):
                sums[cluster][index] += value
        for cluster in range(CLUSTERS):
            if counts[cluster]:
                centroids[cluster] = [value / counts[cluster] for value in sums[cluster]]
    return assignments


def paths_from_curves(obj):
    if len(obj.data.points) != len(obj.data.curves) * POINTS:
        raise RuntimeError(f"unexpected 24-point layout: {obj.name}")
    return [[obj.data.points[curve * POINTS + point].position.copy() for point in range(POINTS)] for curve in range(len(obj.data.curves))]


def reshape(primary, fill, fly):
    old_guides = paths_from_curves(primary)
    assignments = cluster_guides(old_guides)
    members = [[] for _ in range(CLUSTERS)]
    for guide_index, cluster in enumerate(assignments):
        members[cluster].append(guide_index)
    centroids = []
    for group in members:
        centroids.append([sum((old_guides[index][point] for index in group), Vector()) / len(group) for point in range(POINTS)])
    new_guides = []
    guide_deltas = []
    rng = random.Random(2974040)
    cluster_phase = [rng.uniform(-math.pi, math.pi) for _ in range(CLUSTERS)]
    cluster_wave = [rng.uniform(-0.0038, 0.0038) for _ in range(CLUSTERS)]
    maximum_primary_shift = 0.0
    for guide_index, path in enumerate(old_guides):
        cluster = assignments[guide_index]
        centroid = centroids[cluster]
        root_offset = path[0] - centroid[0]
        radial = Vector((centroid[0].x, centroid[0].y + 0.010, 0.0))
        if radial.length < 1e-6:
            radial = Vector((1.0, 0.0, 0.0))
        radial.normalize()
        circumferential = Vector((radial.y, -radial.x, 0.0))
        shaped, deltas = [], []
        for point_index, original in enumerate(path):
            t = point_index / (POINTS - 1)
            root_release = smoothstep(t / 0.18)
            hierarchy = (0.05 + 0.20 * smoothstep((t - 0.18) / 0.82)) * root_release
            preserved_offset = root_offset * (1.0 - 0.48 * smoothstep(t))
            target = centroid[point_index] + preserved_offset
            point = original.lerp(target, hierarchy)
            point += circumferential * cluster_wave[cluster] * (math.sin(math.pi * t) ** 1.6) * math.sin(cluster_phase[cluster] + t * math.pi)
            delta = point - original
            maximum_primary_shift = max(maximum_primary_shift, delta.length)
            shaped.append(point)
            deltas.append(delta)
            primary.data.points[guide_index * POINTS + point_index].position = point
        new_guides.append(shaped)
        guide_deltas.append(deltas)
    primary.data.update_tag()

    layer_reports = {PRIMARY: {"curves": len(primary.data.curves), "maximumShiftM": maximum_primary_shift}}
    for obj, clump_scale, delta_scale in ((fill, 0.22, 1.0), (fly, 0.0, 0.72)):
        family = obj.data.attributes.get("aevrynd_guide_family")
        maximum_shift = 0.0
        for curve_index in range(len(obj.data.curves)):
            guide = int(family.data[curve_index].value) if family else curve_index % len(new_guides)
            guide = max(0, min(len(new_guides) - 1, guide))
            for point_index in range(POINTS):
                data_point = obj.data.points[curve_index * POINTS + point_index]
                original = data_point.position.copy()
                t = point_index / (POINTS - 1)
                point = original + guide_deltas[guide][point_index] * delta_scale
                if clump_scale:
                    child_clump = clump_scale * smoothstep(t / 0.32)
                    point = point.lerp(new_guides[guide][point_index], child_clump)
                data_point.position = point
                maximum_shift = max(maximum_shift, (point - original).length)
        obj.data.update_tag()
        layer_reports[obj.name] = {"curves": len(obj.data.curves), "maximumShiftM": maximum_shift}

    taper_reports = {}
    for obj, start in ((primary, 0.72), (fill, 0.60), (fly, 0.66)):
        radius = obj.data.attributes.get("radius")
        changed = 0
        if radius:
            before_tip = []
            for point_index, item in enumerate(radius.data):
                t = (point_index % POINTS) / (POINTS - 1)
                if t >= start:
                    if t > 0.999:
                        before_tip.append(item.value)
                    item.value *= 1.0 - smoothstep((t - start) / (1.0 - start))
                    changed += 1
            obj.data.update_tag()
            taper_reports[obj.name] = {"startFactor": start, "changedPoints": changed, "tipBeforeRange": [min(before_tip), max(before_tip)] if before_tip else None, "tipAfter": 0.0}
    return assignments, members, layer_reports, taper_reports


def body_tree(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def repair_rest(scene, body, objects):
    scene.frame_set(1)
    tree = body_tree(body)
    results = {}
    for obj in objects:
        matrix = obj.matrix_world.copy()
        inverse = matrix.inverted()
        moved, maximum = 0, 0.0
        for point in obj.data.points:
            world = matrix @ point.position
            hit = tree.find_nearest(world, 0.20)
            if hit is None or hit[1] is None:
                continue
            normal = hit[1].normalized()
            signed = (world - hit[0]).dot(normal)
            if signed < CLEARANCE:
                corrected = hit[0] + normal * CLEARANCE
                maximum = max(maximum, (corrected - world).length)
                point.position = inverse @ corrected
                moved += 1
        obj.data.update_tag()
        results[obj.name] = {"movedPoints": moved, "maximumCorrectionM": maximum}
    return results


def percentile(values, fraction):
    values = sorted(values)
    return values[min(len(values) - 1, int((len(values) - 1) * fraction))]


def audit(scene, body, objects):
    snapshots, collision, failures = {}, {}, []
    for frame in FRAMES:
        scene.frame_set(frame)
        tree = body_tree(body)
        snapshots[frame], collision[str(frame)] = {}, {}
        for obj in objects:
            depsgraph = bpy.context.evaluated_depsgraph_get()
            depsgraph.update()
            evaluated = obj.evaluated_get(depsgraph)
            local = [point.position.copy() for point in evaluated.data.points]
            world = [evaluated.matrix_world @ point for point in local]
            snapshots[frame][obj.name] = local
            signed = []
            for point in world:
                hit = tree.find_nearest(point, 0.20)
                if hit is not None and hit[1] is not None:
                    signed.append((point - hit[0]).dot(hit[1].normalized()))
            penetrating = sum(value < -1e-7 for value in signed)
            collision[str(frame)][obj.name] = {"samples": len(signed), "minimumSignedM": min(signed), "penetratingPoints": penetrating}
            if penetrating:
                failures.append({"frame": frame, "object": obj.name, "penetratingPoints": penetrating})
    peak_all, settle_all, roots_all, motion = [], [], [], {}
    for obj in objects:
        rest, peak, settled = snapshots[1][obj.name], snapshots[33][obj.name], snapshots[61][obj.name]
        peak_delta = [(b - a).length for a, b in zip(rest, peak)]
        settle_delta = [(b - a).length for a, b in zip(rest, settled)]
        roots = [peak_delta[index] for index in range(0, len(peak_delta), POINTS)]
        peak_all.extend(peak_delta); settle_all.extend(settle_delta); roots_all.extend(roots)
        motion[obj.name] = {"peakMeanM": sum(peak_delta) / len(peak_delta), "peakP95M": percentile(peak_delta, 0.95), "peakMaximumM": max(peak_delta), "rootMaximumM": max(roots), "settleMaximumM": max(settle_delta)}
    summary = {"peakMeanM": sum(peak_all) / len(peak_all), "peakP95M": percentile(peak_all, 0.95), "peakMaximumM": max(peak_all), "rootMaximumM": max(roots_all), "settleMaximumM": max(settle_all)}
    if summary["peakP95M"] < 0.0020:
        failures.append({"motion": "peak P95 below 2mm", "valueM": summary["peakP95M"]})
    if summary["rootMaximumM"] > 0.00002:
        failures.append({"motion": "root drift above 0.02mm", "valueM": summary["rootMaximumM"]})
    if summary["settleMaximumM"] > 0.00005:
        failures.append({"motion": "frame 61 not settled", "valueM": summary["settleMaximumM"]})
    return collision, motion, summary, failures


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, frame, name, location):
    scene.frame_set(frame)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.location = location
    camera.data.lens = 82
    look_at(camera, (0.0, 0.0, 1.56))
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
primary, fill, fly = (bpy.data.objects[name] for name in LAYERS)
assignments, members, layer_reports, taper_reports = reshape(primary, fill, fly)
repair = repair_rest(scene, body, (primary, fill, fly))
collision, motion, summary, failures = audit(scene, body, (primary, fill, fly))
for obj in (primary, fill, fly):
    obj["aevrynd_revision"] = "v249r297"
    obj["aevrynd_macro_lock_count"] = CLUSTERS
scene["aevrynd_mainline_revision"] = "v249r297-macro-lock-hierarchy"
scene["aevrynd_release_state"] = "MACRO_LOCK_VISUAL_REVIEW_PENDING" if not failures else "MACRO_LOCK_TECHNICAL_FAIL"
AUDIT.write_text(json.dumps({"model": str(OUTPUT), "collision": collision, "motion": motion, "motionSummary": summary, "failures": failures, "status": "PASS" if not failures else "FAIL"}, indent=2), encoding="utf-8")
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
for frame, name, location in ((1, "front-f01", (0.0, -0.90, 1.59)), (33, "front-f33", (0.0, -0.90, 1.59)), (1, "left-f01", (-0.72, -0.55, 1.59)), (1, "right-f01", (0.72, -0.55, 1.59)), (1, "back-f01", (0.0, 0.90, 1.59)), (33, "back-f33", (0.0, 0.90, 1.59))):
    render(camera, frame, name, location)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "macroLockCount": CLUSTERS,
    "clusterSizes": [len(group) for group in members], "layerReports": layer_reports,
    "taperReports": taper_reports, "repair": repair, "audit": str(AUDIT),
    "auditStatus": "PASS" if not failures else "FAIL", "motionSummary": summary,
    "failures": failures, "runtimeProxyPreserved": "AevryndFemaleRuntimeHairCards_R276",
    "ownedAssetOnly": True, "renderDirectory": str(RENDER_DIR),
    "status": "VISUAL_REVIEW_PENDING" if not failures else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R297_MACRO_LOCK_HIERARCHY=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
