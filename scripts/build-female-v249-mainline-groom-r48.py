import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-groom-r47.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-groom-r48.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-groom-r48"
OUT.mkdir(parents=True, exist_ok=True)
BODY = "AevryndFemaleBodyBaseV118"
RIG = "AevryndFemaleRig"
COVERAGE = "AevryndFemaleCoverageGroom_v249r47"
MATERIAL = "AevryndFemaleHairMaterial_v249r27"
POINTS = 16


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smooth(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def fract(value):
    return value - math.floor(value)


def rnd(index, salt=0.0):
    return fract(math.sin(index * 12.9898 + salt * 78.233) * 43758.5453)


def bezier(p0, p1, p2, p3, t):
    u = 1.0 - t
    return p0 * u**3 + p1 * 3.0 * u * u * t + p2 * 3.0 * u * t * t + p3 * t**3


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


def make_hair(name, strands, layer, root_radius):
    data = bpy.data.hair_curves.new(name + "Data")
    data.add_curves([len(strand) for strand in strands])
    data.points.foreach_set("position", [axis for strand in strands for point in strand for axis in point])
    radius = data.attributes.new("radius", "FLOAT", "POINT")
    values = []
    for strand_index, strand in enumerate(strands):
        scale = 0.85 + 0.22 * rnd(strand_index, 31.0)
        for point_index in range(len(strand)):
            t = point_index / max(1, len(strand) - 1)
            values.append(root_radius * scale * (1.0 - 0.76 * smooth(t)))
    radius.data.foreach_set("value", values)
    data.materials.append(bpy.data.materials[MATERIAL])
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = bpy.data.objects[RIG]
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = Matrix.Identity(4)
    obj["aevrynd_layer"] = layer
    obj["aevrynd_mainline_baseline"] = "v249"
    obj["aevrynd_candidate"] = "v249-mainline-groom-r48"
    return obj


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
tree = evaluated_tree(bpy.data.objects[BODY], bpy.context.evaluated_depsgraph_get())

# Close the rear split without moving roots. Posterior strands fall toward their
# root column instead of diverging into symmetric side curtains.
coverage = bpy.data.objects[COVERAGE]
coverage_data = coverage.data
coverage_points = 24
rear_curves = 0
maximum_rear_displacement = 0.0
for curve_index in range(len(coverage_data.curves)):
    start = curve_index * coverage_points
    root = coverage_data.points[start].position.copy()
    if root.y < 0.012:
        continue
    rear = smooth((root.y - 0.012) / 0.075)
    target_x = root.x * (0.22 + 0.20 * (1.0 - rear))
    target_y = 0.090 + 0.018 * rear + 0.006 * (rnd(curve_index, 1.0) - 0.5)
    target_z = 1.365 + 0.075 * rnd(curve_index, 2.0)
    original_tip = coverage_data.points[start + coverage_points - 1].position.copy()
    target_tip = Vector((target_x, target_y, target_z))
    tip_delta = (target_tip - original_tip) * rear
    maximum_rear_displacement = max(maximum_rear_displacement, tip_delta.length)
    for point_index in range(5, coverage_points):
        t = point_index / (coverage_points - 1)
        envelope = smooth((t - 0.20) / 0.80)
        coverage_data.points[start + point_index].position += tip_delta * envelope
    rear_curves += 1
coverage_data.update_tag()
coverage.name = "AevryndFemaleCoverageGroom_v249r48"
coverage.data.name = "AevryndFemaleCoverageGroomData_v249r48"
coverage["aevrynd_candidate"] = "v249-mainline-groom-r48"
coverage["aevrynd_rear_flow"] = "root-locked posterior center coverage"

# Add a staggered frontal transition. These fibers bridge the dark scalp shell
# and the long coverage groom, while a sparse subset forms actual baby hairs.
center = Vector((0.0, -0.012, 1.635))
radius_x, radius_y, radius_z = 0.083, 0.108, 0.096
transition = []
baby = []
root_count = 92
for root_index in range(root_count):
    q = (root_index + 0.5) / root_count
    x = -0.076 + 0.152 * q + 0.0012 * (rnd(root_index, 3.0) - 0.5)
    normalized = abs(x) / 0.076
    y = -0.112 + 0.040 * normalized**1.70 + 0.0018 * (rnd(root_index, 4.0) - 0.5)
    x_norm = x / radius_x
    y_norm = (y - center.y) / radius_y
    z = center.z + radius_z * math.sqrt(max(0.0, 1.0 - x_norm * x_norm - y_norm * y_norm))
    nearest = tree.find_nearest(Vector((x, y, z)), 0.060)
    if nearest is None or nearest[1] is None:
        continue
    normal = nearest[1].normalized()
    root = nearest[0] + normal * 0.0013
    side = -1.0 if x < -0.024 else 1.0
    desired = Vector((side * (0.70 + 0.20 * normalized), 0.65, 0.18))
    tangent = desired - normal * desired.dot(normal)
    if tangent.length < 1e-6:
        continue
    tangent.normalize()
    bitangent = normal.cross(tangent).normalized()
    for follower in range(5):
        strand_id = root_index * 5 + follower
        root_offset = bitangent * ((follower - 2) * 0.00045)
        local_root = root + root_offset
        length = 0.052 + 0.026 * rnd(strand_id, 5.0)
        p0 = local_root
        p1 = local_root + tangent * (length * 0.34) + normal * 0.0016
        p2 = local_root + tangent * (length * 0.73) + normal * 0.0030
        p3 = local_root + tangent * length + normal * 0.0020
        phase = rnd(strand_id, 6.0) * math.tau
        strand = []
        for point_index in range(POINTS):
            t = point_index / (POINTS - 1)
            point = bezier(p0, p1, p2, p3, t)
            point += bitangent * math.sin(phase + t * math.tau * 0.85) * 0.0007 * smooth(t)
            strand.append(point)
        transition.append(strand)

    if root_index % 3 == 0:
        length = 0.011 + 0.013 * rnd(root_index, 7.0)
        down = Vector((side * 0.35, -0.20, -0.92)).normalized()
        p0 = root + normal * 0.0004
        p1 = p0 + down * length * 0.38
        p2 = p0 + down * length * 0.78 + Vector((side * 0.002, 0.0, 0.0))
        p3 = p0 + down * length + Vector((side * 0.003, 0.0, 0.0))
        baby.append([bezier(p0, p1, p2, p3, i / (POINTS - 1)) for i in range(POINTS)])

transition_obj = make_hair(
    "AevryndFemaleHairlineTransition_v249r48",
    transition,
    "hair.hairline.transition",
    0.000032,
)
baby_obj = make_hair(
    "AevryndFemaleBabyHair_v249r48",
    baby,
    "hair.hairline.baby",
    0.000024,
)

scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_hair_candidate"] = "v249-mainline-groom-r48"
scene["aevrynd_release_state"] = "R48_STRICT_VISUAL_REVIEW_REQUIRED"
scene["aevrynd_hair_layers"] = "coverage|silhouette|flyaway|hairline-transition|baby-hair|scalp-root-shadow"

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
for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "rear_curves_reshaped": rear_curves,
    "maximum_rear_displacement_mm": maximum_rear_displacement * 1000.0,
    "hairline_transition_curves": len(transition),
    "baby_hair_curves": len(baby),
    "status": "STRICT_VISUAL_REVIEW_REQUIRED",
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_MAINLINE_GROOM_R48=" + json.dumps(report, sort_keys=True))
