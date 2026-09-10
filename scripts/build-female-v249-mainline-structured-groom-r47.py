import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r38.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-groom-r47.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-groom-r47"
OUT.mkdir(parents=True, exist_ok=True)
BODY = "AevryndFemaleBodyBaseV118"
RIG = "AevryndFemaleRig"
POINTS = 24
FOLLOWERS = 28
TARGET_GUIDES = 420
ROOT_CLEARANCE = 0.0016
OLD_HAIR = (
    "AevryndFemaleGuideBob_v249r25",
    "AevryndFemaleNapeFiberFill_v249r17",
)


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smooth(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def fract(value):
    return value - math.floor(value)


def rnd(index, salt=0.0):
    return fract(math.sin(index * 12.9898 + salt * 78.233) * 43758.5453)


def radical_inverse(index, base):
    value = 0.0
    factor = 1.0 / base
    while index:
        value += (index % base) * factor
        index //= base
        factor /= base
    return value


def bezier(p0, p1, p2, p3, t):
    u = 1.0 - t
    return p0 * u**3 + p1 * 3.0 * u * u * t + p2 * 3.0 * u * t * t + p3 * t**3


def part_x(y):
    # A shallow left side part which terminates at the crown.
    front_to_crown = smooth((y + 0.105) / 0.150)
    return -0.030 + 0.020 * front_to_crown


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


def make_curves(name, strands, material, layer, radius_scale=1.0):
    data = bpy.data.hair_curves.new(name + "Data")
    data.add_curves([POINTS] * len(strands))
    data.points.foreach_set("position", [axis for strand in strands for point in strand for axis in point])
    radius = data.attributes.new("radius", "FLOAT", "POINT")
    values = []
    for strand_index in range(len(strands)):
        strand_scale = radius_scale * (0.88 + 0.20 * rnd(strand_index, 41.0))
        for point_index in range(POINTS):
            t = point_index / (POINTS - 1)
            values.append(0.000042 * strand_scale * (1.0 - 0.70 * smooth(t)))
    radius.data.foreach_set("value", values)
    data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = bpy.data.objects[RIG]
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = Matrix.Identity(4)
    obj["aevrynd_layer"] = layer
    obj["aevrynd_mainline_baseline"] = "v249"
    obj["aevrynd_candidate"] = "v249-mainline-groom-r47"
    obj["aevrynd_points_per_curve"] = POINTS
    return obj


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
for old in bpy.data.objects:
    layer = str(old.get("aevrynd_layer", ""))
    if old.type == "CURVES" and layer.startswith("hair."):
        old.hide_render = True
        old.hide_viewport = True
        old["aevrynd_mainline_hair_collision"] = False
    elif old.type == "MESH" and (layer.startswith("hair.") or old.name.lower().startswith("hair")):
        if not layer.startswith("hair.scalp.") or layer == "hair.scalp.visible_part":
            old.hide_render = True
            old.hide_viewport = True

body = bpy.data.objects[BODY]
tree = evaluated_tree(body, bpy.context.evaluated_depsgraph_get())
material = bpy.data.materials["AevryndFemaleHairMaterial_v249r27"]

# The roots are independent scalp samples. Guides control the visible families;
# followers are generated only after each guide has a stable tangent field.
center = Vector((0.0, -0.012, 1.635))
radius_x, radius_y, radius_z = 0.083, 0.108, 0.096
guides = []
guide_meta = []
guide_index = 0
candidate_index = 1
accepted_roots = []
while len(guides) < TARGET_GUIDES and candidate_index < 24000:
    y = -0.112 + 0.198 * radical_inverse(candidate_index, 2)
    y_norm = (y - center.y) / radius_y
    half_x = radius_x * math.sqrt(max(0.06, 1.0 - y_norm * y_norm))
    x = (-1.0 + 2.0 * radical_inverse(candidate_index, 3)) * half_x
    candidate_index += 1
    normalized_side = abs(x) / max(half_x, 1e-6)
    front_limit = -0.112 + 0.040 * normalized_side**1.7
    if y < front_limit:
        continue
    seam = part_x(y)
    seam_active = y < 0.045
    if seam_active and abs(x - seam) < 0.0015:
        continue
    x_norm = x / radius_x
    z = center.z + radius_z * math.sqrt(max(0.0, 1.0 - x_norm * x_norm - y_norm * y_norm))
    nearest = tree.find_nearest(Vector((x, y, z)), 0.060)
    if nearest is None or nearest[1] is None or nearest[1].z < -0.08:
        continue
    root = nearest[0] + nearest[1].normalized() * ROOT_CLEARANCE
    if any((root - existing).length < 0.0034 for existing in accepted_roots):
        continue
    accepted_roots.append(root.copy())
    normal = nearest[1].normalized()
    side = -1.0 if x < seam else 1.0
    front = clamp((-y - 0.010) / 0.098)
    back = clamp((y - 0.000) / 0.085)
    lateral = clamp(abs(x - seam) / 0.090)
    crown = clamp((root.z - 1.665) / 0.072)

    desired = Vector((
        side * (0.080 + 0.040 * crown) * (1.0 - 0.72 * back),
        0.060 * back - 0.018 * front,
        -0.010,
    ))
    tangent = desired - normal * desired.dot(normal)
    if tangent.length < 1e-6:
        tangent = Vector((side, 0.0, 0.0))
    tangent.normalize()

        # Region-specific endpoints avoid a single synchronized shoulder line.
    length_jitter = (rnd(guide_index, 1.0) - 0.5)
    rear_centering = smooth((back - 0.12) / 0.88)
    side_end_x = side * (0.106 + 0.026 * lateral + 0.012 * length_jitter)
    rear_end_x = root.x * 0.72 + side * (0.012 + 0.010 * rnd(guide_index, 16.0))
    end_x = side_end_x * (1.0 - rear_centering) + rear_end_x * rear_centering
    end_y = -0.044 * front + 0.092 * back + 0.012 * (rnd(guide_index, 2.0) - 0.5)
    end_z = 1.385 + 0.075 * rnd(guide_index, 3.0) + 0.022 * lateral - 0.025 * back
    if front > 0.60 and lateral < 0.45:
        end_x += side * 0.018
        end_y -= 0.026
        end_z += 0.020

    p0 = root
    p1 = root + tangent * (0.040 + 0.012 * crown) + normal * (0.0035 + 0.0020 * crown)
    p3 = Vector((end_x, end_y, end_z))
    p2 = Vector((
        end_x - side * (0.016 + 0.010 * front) * (1.0 - rear_centering),
        end_y - 0.010 * front,
        end_z + 0.105 + 0.020 * crown,
    ))
    phase = rnd(guide_index, 4.0) * math.tau
    wave_amp = 0.004 + 0.008 * rnd(guide_index, 5.0)
    guide = []
    for point_index in range(POINTS):
        t = point_index / (POINTS - 1)
        point = bezier(p0, p1, p2, p3, t)
        free = smooth((t - 0.24) / 0.76)
        macro = math.sin(phase + t * math.tau * (0.58 + 0.38 * rnd(guide_index, 6.0)))
        point.x += side * wave_amp * macro * free
        point.y += wave_amp * 0.38 * math.cos(phase + t * math.tau * 0.82) * free
        if front > 0.22:
            avoid = front * smooth((t - 0.12) / 0.40)
            safe_x = side * (0.079 + 0.035 * smooth(t))
            blended = point.x * (1.0 - avoid) + safe_x * avoid
            point.x = min(point.x, blended) if side < 0.0 else max(point.x, blended)
        guide.append(point)
    guides.append(guide)
    guide_meta.append((root, normal, tangent, side, front, back, lateral, guide_index))
    guide_index += 1

if len(guides) != TARGET_GUIDES:
    raise RuntimeError(f"Only sampled {len(guides)} of {TARGET_GUIDES} guides")

coverage = []
silhouette = []
flyaways = []
golden = 0.6180339887498949
for guide, meta in zip(guides, guide_meta):
    root, normal, tangent, side, front, back, lateral, index = meta
    bitangent = normal.cross(tangent)
    if bitangent.length < 1e-6:
        bitangent = Vector((0.0, 1.0, 0.0))
    bitangent.normalize()
    for follower in range(FOLLOWERS):
        strand_index = index * FOLLOWERS + follower
        angle = math.tau * fract(follower * golden + rnd(index, 7.0))
        root_radius = 0.00045 + 0.0027 * math.sqrt((follower + 0.5) / FOLLOWERS)
        offset = tangent * (math.cos(angle) * root_radius) + bitangent * (math.sin(angle) * root_radius)
        subgroup = follower % 4
        subgroup_phase = subgroup * (math.tau / 4.0) + rnd(index, 8.0) * 0.65
        subgroup_offset = tangent * (math.cos(subgroup_phase) * 0.0016) + bitangent * (math.sin(subgroup_phase) * 0.0016)
        length_jitter = (rnd(strand_index, 9.0) - 0.5) * 0.034
        fine_phase = rnd(strand_index, 10.0) * math.tau
        strand = []
        for point_index, base in enumerate(guide):
            t = point_index / (POINTS - 1)
            spread = 0.90 + 0.18 * smooth(t)
            clump = math.sin(math.pi * smooth(t))
            point = base + offset * spread + subgroup_offset * clump
            point.z += length_jitter * smooth(t)
            fine = math.sin(fine_phase + t * math.tau * (1.10 + 0.55 * rnd(strand_index, 11.0)))
            fine *= (0.00030 + 0.00065 * rnd(strand_index, 12.0)) * smooth((t - 0.10) / 0.90)
            point += bitangent * fine
            strand.append(point)
        coverage.append(strand)

    if lateral > 0.72 and index % 2 == 0:
        for strand_number in range(3):
            phase = rnd(index * 5 + strand_number, 13.0) * math.tau
            strand = []
            for point_index, base in enumerate(guide):
                t = point_index / (POINTS - 1)
                free = smooth(t)
                point = base + normal * (0.0020 + 0.0035 * math.sin(math.pi * t))
                point += bitangent * math.sin(phase + t * math.tau * 1.25) * 0.0024 * free
                point.z += (rnd(index * 5 + strand_number, 14.0) - 0.5) * 0.040 * free
                strand.append(point)
            silhouette.append(strand)

    if index % 17 == 0:
        strand = []
        phase = rnd(index, 15.0) * math.tau
        for point_index, base in enumerate(guide):
            t = point_index / (POINTS - 1)
            free = smooth(t)
            point = base + normal * (0.002 + 0.012 * math.sin(math.pi * t) * free)
            point += bitangent * math.sin(phase + t * math.tau * 1.70) * 0.006 * free
            point.z += 0.018 * math.sin(math.pi * t) * free
            strand.append(point)
        flyaways.append(strand)

main_obj = make_curves("AevryndFemaleCoverageGroom_v249r47", coverage, material, "hair.coverage.follow", 1.0)
silhouette_obj = make_curves("AevryndFemaleSilhouetteGroom_v249r47", silhouette, material, "hair.silhouette", 0.78)
flyaway_obj = make_curves("AevryndFemaleFlyawayGroom_v249r47", flyaways, material, "hair.flyaway", 0.55)
main_obj["aevrynd_guide_count"] = len(guides)
main_obj["aevrynd_followers_per_guide"] = FOLLOWERS

scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_hair_candidate"] = "v249-mainline-groom-r47"
scene["aevrynd_release_state"] = "R47_STRICT_VISUAL_REVIEW_REQUIRED"
scene["aevrynd_hair_layers"] = "coverage|silhouette|flyaway|scalp-root-shadow|visible-part"

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("01-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("02-three-quarter", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84),
    ("03-profile", (0.70, -0.02, 1.60), (0.0, 0.0, 1.56), 88),
    ("04-back", (0.0, 0.74, 1.58), (0.0, 0.02, 1.56), 88),
    ("05-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
)
scene.frame_set(1)
for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "guide_count": len(guides),
    "layers": {
        "coverage": {"curves": len(coverage), "points": len(coverage) * POINTS},
        "silhouette": {"curves": len(silhouette), "points": len(silhouette) * POINTS},
        "flyaway": {"curves": len(flyaways), "points": len(flyaways) * POINTS},
    },
    "root_clearance_m": ROOT_CLEARANCE,
    "status": "STRICT_VISUAL_REVIEW_REQUIRED",
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_MAINLINE_GROOM_R47=" + json.dumps(report, sort_keys=True))
