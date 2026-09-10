import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-deform-matched-scalp-r163.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-primary-family-groom-r169.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-primary-family-groom-r169.build-report.json"
SOURCE_HAIR = "AevryndFemaleOwnedCurlyHairMain_v249r162"
SCALP = "AevryndFemaleDeformMatchedScalp_v249r163"
RIG = "AevryndFemaleRig"
MATERIAL = "AevryndOwnedLayeredHairMaterial_v249r129"
PRIMARY = "AevryndFemaleOwnedPrimaryGuides_v249r169"
FOLLOW = "AevryndFemaleOwnedFamilyFollowers_v249r169"
GUIDE_COUNT = 320
FOLLOWERS_PER_GUIDE = 16
POINTS_PER_CURVE = 24
SEED = 249169


def resample(points, count):
    if len(points) == count:
        return [point.copy() for point in points]
    lengths = [(points[index + 1] - points[index]).length for index in range(len(points) - 1)]
    cumulative = [0.0]
    for length in lengths:
        cumulative.append(cumulative[-1] + length)
    total = cumulative[-1]
    if total <= 1e-12:
        return [points[0].copy() for _ in range(count)]
    result = []
    segment = 0
    for sample_index in range(count):
        distance = total * sample_index / (count - 1)
        while segment + 1 < len(cumulative) - 1 and cumulative[segment + 1] < distance:
            segment += 1
        span = max(1e-12, cumulative[segment + 1] - cumulative[segment])
        t = (distance - cumulative[segment]) / span
        result.append(points[segment].lerp(points[segment + 1], t))
    return result


def world_curves(obj):
    curves = []
    for curve in obj.data.curves:
        points = [
            obj.matrix_world @ obj.data.points[curve.first_point_index + local_index].position
            for local_index in range(curve.points_length)
        ]
        curves.append(resample(points, POINTS_PER_CURVE))
    return curves


def choose_guides(curves, count):
    roots = [curve[0] for curve in curves]
    first = min(range(len(curves)), key=lambda index: (roots[index].y, abs(roots[index].x)))
    chosen = [first]
    nearest_sq = [(root - roots[first]).length_squared for root in roots]
    while len(chosen) < min(count, len(curves)):
        index = max(range(len(curves)), key=lambda candidate: nearest_sq[candidate])
        chosen.append(index)
        root = roots[index]
        for candidate, other in enumerate(roots):
            distance_sq = (other - root).length_squared
            if distance_sq < nearest_sq[candidate]:
                nearest_sq[candidate] = distance_sq
    return chosen


def local_frame(points, index):
    if index == 0:
        tangent = points[1] - points[0]
    elif index == len(points) - 1:
        tangent = points[-1] - points[-2]
    else:
        tangent = points[index + 1] - points[index - 1]
    tangent.normalize()
    radial = points[index] - Vector((0.0, 0.0, 1.615))
    radial -= tangent * radial.dot(tangent)
    if radial.length < 1e-6:
        radial = tangent.cross(Vector((1.0, 0.0, 0.0)))
    radial.normalize()
    side = tangent.cross(radial).normalized()
    return radial, side


def create_curves(name, curves, material, root_radius, tip_radius, layer, revision, shadow):
    data = bpy.data.hair_curves.new(name + "Data")
    data.add_curves([len(curve) for curve in curves])
    radius = data.attributes.new("radius", "FLOAT", "POINT")
    flat = 0
    for curve in curves:
        for point_index, point in enumerate(curve):
            u = point_index / max(1, len(curve) - 1)
            data.points[flat].position = point
            radius.data[flat].value = root_radius * (1.0 - u) + tip_radius * u
            flat += 1
    data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.visible_shadow = shadow
    obj["aevrynd_layer"] = layer
    obj["aevrynd_revision"] = revision
    obj["aevrynd_source"] = "Aevrynd-owned family reconstruction using CC0 curly curvature reference"
    obj["aevrynd_runtime_dependency"] = "none"
    obj["aevrynd_collision_status"] = "PENDING_STRICT_AUDIT"
    return obj


def bone_parent(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
source = bpy.data.objects[SOURCE_HAIR]
curves = world_curves(source)
guide_indices = choose_guides(curves, GUIDE_COUNT)
guides = [curves[index] for index in guide_indices]
rng = random.Random(SEED)
followers = []
family_ids = []
for family_index, guide in enumerate(guides):
    for child_index in range(FOLLOWERS_PER_GUIDE):
        phase = math.tau * child_index / FOLLOWERS_PER_GUIDE + rng.uniform(-0.10, 0.10)
        spread_scale = rng.uniform(0.72, 1.18)
        length_scale = rng.uniform(0.90, 1.04)
        child = []
        for point_index in range(POINTS_PER_CURVE):
            source_u = min(1.0, (point_index / (POINTS_PER_CURVE - 1)) * length_scale)
            source_index = min(POINTS_PER_CURVE - 1, round(source_u * (POINTS_PER_CURVE - 1)))
            base = guide[source_index]
            radial, side = local_frame(guide, source_index)
            u = point_index / (POINTS_PER_CURVE - 1)
            spread = (0.00035 * (1.0 - u) + 0.0048 * u) * spread_scale
            wave = math.sin(math.pi * u) * rng.uniform(-0.00035, 0.00035)
            offset = radial * (0.00055 * (1.0 - u) + spread * math.cos(phase))
            offset += side * (spread * math.sin(phase) + wave)
            child.append(base + offset)
        followers.append(child)
        family_ids.append(family_index)

material = bpy.data.materials[MATERIAL]
primary = create_curves(PRIMARY, guides, material, 0.000072, 0.000014, "hair.guides.primary", "v249r169", True)
follow = create_curves(FOLLOW, followers, material, 0.000038, 0.000007, "hair.follow.family", "v249r169", False)
family_attribute = follow.data.attributes.new("aevrynd_clump_family", "INT", "CURVE")
for index, family_id in enumerate(family_ids):
    family_attribute.data[index].value = family_id
rig = bpy.data.objects[RIG]
bone_parent(primary, rig)
bone_parent(follow, rig)
source.hide_render = True
source.hide_viewport = True
source["aevrynd_replaced_by"] = f"{PRIMARY},{FOLLOW}"
scene["aevrynd_revision"] = "v249r169"
scene["aevrynd_candidate_status"] = "COLLISION_AND_VISUAL_REVIEW_PENDING"
scene["aevrynd_hair_layers"] = ["hair.scalp.foundation", "hair.guides.primary", "hair.follow.family"]
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE), "output": str(OUTPUT),
    "sourceCurves": len(curves), "primaryGuides": len(guides),
    "followersPerGuide": FOLLOWERS_PER_GUIDE,
    "followCurves": len(followers),
    "primaryPoints": len(primary.data.points), "followPoints": len(follow.data.points),
    "combinedHairPoints": len(primary.data.points) + len(follow.data.points),
    "layers": ["hair.scalp.foundation", "hair.guides.primary", "hair.follow.family"],
    "runtimeDependency": "none", "status": "COLLISION_AND_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R169_BUILD=" + json.dumps(report, sort_keys=True))
