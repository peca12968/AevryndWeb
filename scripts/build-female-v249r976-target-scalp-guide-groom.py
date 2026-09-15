"""Build a target-native scalp and owned guide/follower groom on r962."""

import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-knee-crease-volume-r962.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-target-scalp-guide-groom-r976.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-target-scalp-guide-groom-r976.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r976-target-scalp-guide-groom"
BODY = "AevryndFemaleCC0Baseline_v259"
RIG = "AevryndFemaleRig"
SCALP = "AevryndFemaleTargetScalp_R976"
GROOM = "AevryndFemaleTargetGuideGroom_R976"
POINTS_PER_STRAND = 20
FOLLOWERS_PER_GUIDE = 14
MAX_GUIDES = 260
ROOT_CLEARANCE = 0.0012
HEAD_CLEARANCE = 0.0016


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def evaluated_surface(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    normal_matrix = evaluated.matrix_world.to_3x3()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    normals = [(normal_matrix @ vertex.normal).normalized() for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return points, normals, faces, BVHTree.FromPolygons(points, faces, all_triangles=False)


def hairline_threshold(x):
    side = clamp(abs(x) / 0.096)
    # Slight central point, soft temporal recession, then a lower temple join.
    center = 1.542 + 0.010 * smoothstep((side - 0.28) / 0.42)
    return center - 0.012 * smoothstep((side - 0.78) / 0.22)


def scalp_density(point):
    side = abs(point.x) / 0.108
    if side >= 1.05 or point.z < 1.485:
        return 0.0
    if point.y < -0.095:
        threshold = hairline_threshold(point.x)
    else:
        rear = smoothstep((point.y - 0.005) / 0.055)
        threshold = 1.492 + 0.018 * rear
    vertical = smoothstep((point.z - threshold) / 0.018)
    lateral = 1.0 - smoothstep((side - 0.88) / 0.17)
    return vertical * lateral


def make_scalp(points, normals, faces):
    density = [scalp_density(point) for point in points]
    selected = [face for face in faces if max(density[index] for index in face) > 0.20]
    used = sorted({index for face in selected for index in face})
    remap = {old: new for new, old in enumerate(used)}
    vertices = [points[index] + normals[index] * ROOT_CLEARANCE for index in used]
    polygons = [tuple(remap[index] for index in face) for face in selected]
    data = bpy.data.meshes.new(SCALP + "Data")
    data.from_pydata(vertices, [], polygons)
    data.update()
    attribute = data.attributes.new("aevrynd_root_density", "FLOAT", "POINT")
    for new_index, old_index in enumerate(used):
        attribute.data[new_index].value = density[old_index]
    obj = bpy.data.objects.new(SCALP, data)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_layer"] = "hair.scalp.target_native"
    obj["aevrynd_revision"] = "v249r976"
    obj["aevrynd_source"] = "r962 evaluated body surface; Aevrynd generated"
    return obj, [(vertices[new], normals[old], density[old]) for new, old in enumerate(used)]


def make_scalp_material():
    material = bpy.data.materials.new("Aevrynd_TargetScalp_WarmBrown_R976")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.052, 0.014, 0.005, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.68
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.32
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return material


def make_hair_material():
    material = bpy.data.materials.new("Aevrynd_HairMelanin_R976")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    hair = nodes.new("ShaderNodeBsdfHairPrincipled")
    hair.parametrization = "MELANIN"
    for name, value in (
        ("Melanin", 0.63),
        ("Melanin Redness", 0.28),
        ("Roughness", 0.34),
        ("IOR", 1.55),
        ("Random Color", 0.14),
        ("Random Roughness", 0.10),
    ):
        if name in hair.inputs:
            hair.inputs[name].default_value = value
    links.new(hair.outputs[0], output.inputs["Surface"])
    return material


def choose_guides(candidates):
    candidates = [item for item in candidates if item[2] > 0.55]
    candidates.sort(key=lambda item: (round(item[0].y, 4), round(item[0].x, 4), -item[0].z))
    if len(candidates) <= MAX_GUIDES:
        return candidates
    step = len(candidates) / MAX_GUIDES
    return [candidates[min(len(candidates) - 1, int((index + 0.5) * step))] for index in range(MAX_GUIDES)]


def bezier(p0, p1, p2, p3, t):
    u = 1.0 - t
    return p0 * u ** 3 + p1 * 3.0 * u * u * t + p2 * 3.0 * u * t * t + p3 * t ** 3


def nearest_clear(surface, point, clearance):
    hit = surface.find_nearest(point, 0.075)
    if hit is None or hit[1] is None:
        return point
    nearest, normal, _face, _distance = hit
    normal = normal.normalized()
    signed = (point - nearest).dot(normal)
    return nearest + normal * clearance if signed < clearance else point


def guide_curve(root, normal, index):
    rng = random.Random(976000 + index)
    part = -0.012 + 0.010 * smoothstep((root.y + 0.10) / 0.16)
    side = -1.0 if root.x < part else 1.0
    front = smoothstep((-root.y - 0.035) / 0.105)
    back = smoothstep((root.y + 0.005) / 0.060)
    crown = smoothstep((root.z - 1.575) / 0.090)
    length = 0.245 + 0.070 * crown + 0.030 * back + rng.uniform(-0.014, 0.014)
    end = Vector((
        clamp(root.x + side * (0.052 + 0.050 * crown + 0.025 * front), -0.158, 0.158),
        root.y + 0.022 * back - 0.014 * front,
        root.z - length,
    ))
    p1 = root + normal * (0.010 + 0.006 * crown) + Vector((side * 0.020, -0.004 * front, 0.006))
    p2 = Vector((end.x - side * 0.014, end.y, end.z + 0.090))
    phase = rng.uniform(0.0, math.tau)
    wave = rng.uniform(0.0022, 0.0058)
    points = []
    for point_index in range(POINTS_PER_STRAND):
        t = point_index / (POINTS_PER_STRAND - 1)
        point = bezier(root, p1, p2, end, t)
        weight = smoothstep((t - 0.18) / 0.82)
        point.x += side * math.sin(phase + t * math.tau * 0.85) * wave * weight
        point.y += math.cos(phase + t * math.tau) * wave * 0.38 * weight
        points.append(point)
    return points, normal, side, rng


def build_strands(guides, surface):
    strands = []
    for index, (root, normal, _density) in enumerate(guides):
        guide, normal, side, rng = guide_curve(root, normal, index)
        tangent = Vector((normal.z, 0.0, -normal.x)).normalized()
        bitangent = normal.cross(tangent).normalized()
        for follower in range(FOLLOWERS_PER_GUIDE):
            angle = math.tau * ((follower * 0.61803398875 + rng.random() * 0.08) % 1.0)
            radius = 0.0003 if follower == 0 else 0.0010 + 0.0038 * math.sqrt(rng.random())
            offset = tangent * (math.cos(angle) * radius) + bitangent * (math.sin(angle) * radius)
            follower_root = nearest_clear(surface, root + offset, ROOT_CLEARANCE)
            root_delta = follower_root - root
            strand = []
            length_jitter = rng.uniform(-0.012, 0.012)
            for point_index, base in enumerate(guide):
                t = point_index / (POINTS_PER_STRAND - 1)
                point = base + root_delta * (1.0 - 0.35 * smoothstep(t))
                point += offset * (0.20 + 0.80 * smoothstep(t))
                point.z += length_jitter * smoothstep(t)
                if point.z > 1.34:
                    point = nearest_clear(surface, point, HEAD_CLEARANCE)
                strand.append(point)
            strands.append(strand)
    return strands


def make_groom(strands, material):
    data = bpy.data.hair_curves.new(GROOM + "Data")
    data.add_curves([POINTS_PER_STRAND] * len(strands))
    data.points.foreach_set("position", [coordinate for strand in strands for point in strand for coordinate in point])
    radius = data.attributes.new("radius", "FLOAT", "POINT")
    values = []
    for _strand in strands:
        for point_index in range(POINTS_PER_STRAND):
            t = point_index / (POINTS_PER_STRAND - 1)
            values.append(0.000075 * (1.0 - 0.72 * smoothstep(t)))
    radius.data.foreach_set("value", values)
    data.materials.append(material)
    obj = bpy.data.objects.new(GROOM, data)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_layer"] = "hair.guide_follow.target_native"
    obj["aevrynd_revision"] = "v249r976"
    obj["aevrynd_source"] = "Aevrynd generated from r962 target scalp"
    obj["aevrynd_runtime_dependency"] = "none"
    return obj


def render(scene, camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
points, normals, faces, surface = evaluated_surface(bpy.data.objects[BODY])
scalp, candidates = make_scalp(points, normals, faces)
scalp.data.materials.append(make_scalp_material())
guides = choose_guides(candidates)
strands = build_strands(guides, surface)
groom = make_groom(strands, make_hair_material())
for obj in (scalp, groom):
    world = obj.matrix_world.copy()
    obj.parent = bpy.data.objects[RIG]
    obj.parent_type = "OBJECT"
    obj.matrix_parent_inverse = obj.parent.matrix_world.inverted()
    obj.matrix_world = world

scene["aevrynd_mainline_revision"] = "v249r976-target-scalp-guide-groom"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "STATIC_GROOM_VISUAL_AND_COLLISION_AUDIT_REQUIRED"
scene["aevrynd_hair_layers"] = "hair.scalp.target_native|hair.guide_follow.target_native"
scene["aevrynd_website_promotion"] = "forbidden pending strict gates and user approval"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects.get("Aevrynd Review Camera")
if camera is None:
    camera = bpy.data.objects.new("Aevrynd R976 Review Camera", bpy.data.cameras.new("Aevrynd R976 Review Camera Data"))
    scene.collection.objects.link(camera)
scene.camera = camera
for args in (
    ("01-face-front", (0.0, -0.68, 1.49), (0.0, -0.055, 1.48), 88),
    ("02-face-three-quarter", (0.42, -0.58, 1.51), (0.0, -0.045, 1.48), 88),
    ("03-face-profile", (0.68, -0.02, 1.50), (0.0, -0.035, 1.48), 90),
    ("04-hair-back", (0.0, 0.76, 1.50), (0.0, -0.01, 1.48), 86),
    ("05-hair-top", (0.0, -0.18, 2.05), (0.0, -0.02, 1.57), 82),
):
    render(scene, camera, *args)

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "scalpVertices": len(scalp.data.vertices),
    "scalpPolygons": len(scalp.data.polygons),
    "guideCount": len(guides),
    "followersPerGuide": FOLLOWERS_PER_GUIDE,
    "strandCount": len(strands),
    "pointCount": len(strands) * POINTS_PER_STRAND,
    "rootClearanceM": ROOT_CLEARANCE,
    "headClearanceM": HEAD_CLEARANCE,
    "ownedAssetOnly": True,
    "runtimeDependency": "none",
    "secondaryMotion": False,
    "websitePromotionApproved": False,
    "status": "STRICT_VISUAL_AND_COLLISION_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R976_TARGET_SCALP_GUIDE_GROOM=" + json.dumps(report, sort_keys=True))
