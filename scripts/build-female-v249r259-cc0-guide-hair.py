import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-subtle-lid-wetline-r258.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-guide-hair-r259.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-cc0-guide-hair-r259.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r259-cc0-guide-hair"
BODY = "AevryndFemaleBody_CC0_R249"
RIG = "AevryndFemaleRig"
POINTS_PER_STRAND = 24
FOLLOW_PER_GUIDE = 12
CLEARANCE = 0.0020


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def fract(value):
    return value - math.floor(value)


def rnd(index, salt=0.0):
    return fract(math.sin(index * 12.9898 + salt * 78.233) * 43758.5453)


def part_x(y):
    return -0.018 + 0.013 * smoothstep((y + 0.105) / 0.180)


def bezier(p0, p1, p2, p3, t):
    u = 1.0 - t
    return p0 * (u ** 3) + p1 * (3.0 * u * u * t) + p2 * (3.0 * u * t * t) + p3 * (t ** 3)


def body_tree(frame):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = bpy.data.objects[BODY].evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def hair_material():
    material = bpy.data.materials.new("Aevrynd_PrincipledHair_CC0_R259")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    hair = nodes.new("ShaderNodeBsdfHairPrincipled")
    hair.parametrization = "COLOR"
    hair.inputs["Color"].default_value = (0.018, 0.0055, 0.0028, 1.0)
    hair.inputs["Roughness"].default_value = 0.40
    hair.inputs["Radial Roughness"].default_value = 0.55
    hair.inputs["Coat"].default_value = 0.035
    hair.inputs["IOR"].default_value = 1.52
    material.node_tree.links.new(hair.outputs["BSDF"], output.inputs["Surface"])
    material["aevrynd_layer"] = "material.hair.longitudinal_scattering"
    material["aevrynd_ownership"] = "procedural in-project"
    return material


def scalp_material():
    material = bpy.data.materials.new("Aevrynd_ScalpShadow_CC0_R259")
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = (0.012, 0.0038, 0.0020, 1.0)
    shader.inputs["Roughness"].default_value = 0.90
    shader.inputs["Specular IOR Level"].default_value = 0.16
    material["aevrynd_layer"] = "material.hair.scalp_shadow"
    return material


def make_scalp(body, material):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    normals = [(evaluated.matrix_world.to_3x3() @ vertex.normal).normalized() for vertex in mesh.vertices]
    selected = []
    for polygon in mesh.polygons:
        center = evaluated.matrix_world @ polygon.center
        if center.y < -0.045:
            threshold = 1.654 + 0.018 * clamp((-center.y - 0.045) / 0.090)
        else:
            threshold = 1.590
        if center.z >= threshold:
            selected.append(tuple(polygon.vertices))
    used = sorted({index for polygon in selected for index in polygon})
    remap = {old: new for new, old in enumerate(used)}
    cap_vertices = [vertices[index] + normals[index] * 0.00085 for index in used]
    cap_faces = [tuple(remap[index] for index in polygon) for polygon in selected]
    data = bpy.data.meshes.new("AevryndFemaleScalpCoverageTopology_R259")
    data.from_pydata(cap_vertices, [], cap_faces)
    data.materials.append(material)
    obj = bpy.data.objects.new("AevryndFemaleScalpCoverage_R259", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = bpy.data.objects[RIG]
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = Matrix.Identity(4)
    obj["aevrynd_layer"] = "hair.scalp.shadow"
    obj["aevrynd_revision"] = "v249r259"
    obj["aevrynd_clearance_m"] = 0.00085
    evaluated.to_mesh_clear()
    return obj, len(cap_vertices), len(cap_faces)


def create_hair(strands, guides, material):
    data = bpy.data.hair_curves.new("AevryndFemaleGuideHairTopology_R259")
    data.add_curves([POINTS_PER_STRAND] * len(strands))
    data.points.foreach_set("position", [coordinate for strand in strands for point in strand for coordinate in point])
    radius = data.attributes.new("radius", "FLOAT", "POINT")
    radii = []
    family = data.attributes.new("aevrynd_guide_family", "INT", "CURVE")
    family_values = []
    for strand_index, _strand in enumerate(strands):
        family_values.append(strand_index // FOLLOW_PER_GUIDE)
        for point_index in range(POINTS_PER_STRAND):
            t = point_index / (POINTS_PER_STRAND - 1)
            radii.append(0.000048 * (1.0 - 0.70 * smoothstep(t)))
    radius.data.foreach_set("value", radii)
    family.data.foreach_set("value", family_values)
    data.materials.append(material)
    obj = bpy.data.objects.new("AevryndFemaleGuideFollowHair_R259", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = bpy.data.objects[RIG]
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = Matrix.Identity(4)
    obj["aevrynd_layer"] = "hair.guide_follow.mass"
    obj["aevrynd_revision"] = "v249r259"
    obj["aevrynd_guide_count"] = guides
    obj["aevrynd_follow_per_guide"] = FOLLOW_PER_GUIDE
    obj["aevrynd_source"] = "procedurally authored in Aevrynd from current CC0 head surface"
    return obj


def solve_collision(obj, frames=(1, 20), iterations=3):
    counts = {}
    for iteration in range(iterations):
        for frame in frames:
            tree = body_tree(frame)
            matrix = obj.matrix_world.copy()
            inverse = matrix.inverted()
            moved = 0
            for point in obj.data.points:
                world = matrix @ point.position
                nearest = tree.find_nearest(world, 0.18)
                if nearest is None:
                    continue
                location, normal, _face, _distance = nearest
                if normal is None:
                    continue
                normal = normal.normalized()
                signed = (world - location).dot(normal)
                if signed < CLEARANCE:
                    point.position = inverse @ (location + normal * CLEARANCE)
                    moved += 1
            counts[f"iteration_{iteration + 1}_frame_{frame}"] = moved
            obj.data.update_tag()
    return counts


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, frame, location, target, lens):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY]
tree = body_tree(1)
fiber_mat = hair_material()
scalp, scalp_vertices, scalp_faces = make_scalp(body, scalp_material())

center = Vector((0.0, -0.010, 1.638))
radius_x, radius_y, radius_z = 0.083, 0.108, 0.097
guides = []
guide_meta = []
guide_index = 0
for row in range(22):
    y = -0.108 + row * (0.184 / 21.0)
    y_norm = (y - center.y) / radius_y
    half_x = radius_x * math.sqrt(max(0.05, 1.0 - y_norm * y_norm))
    columns = max(12, round(28 * half_x / radius_x))
    for column in range(columns):
        u = (column + 0.5 + (0.34 if row % 2 else 0.0)) / columns
        x = -half_x + 2.0 * half_x * u
        seam = part_x(y)
        if abs(x - seam) < 0.00115:
            continue
        x_norm = x / radius_x
        z = center.z + radius_z * math.sqrt(max(0.0, 1.0 - x_norm * x_norm - y_norm * y_norm))
        nearest = tree.find_nearest(Vector((x, y, z)), 0.055)
        if nearest is None:
            continue
        location, normal, _face, _distance = nearest
        if normal is None or normal.z < -0.08:
            continue
        normal = normal.normalized()
        root = location + normal * CLEARANCE
        side = -1.0 if x < seam else 1.0
        front = clamp((-y - 0.012) / 0.100)
        back = clamp((y - 0.005) / 0.085)
        crown = clamp((z - 1.672) / 0.070)
        length = 0.205 + 0.060 * crown + 0.032 * back + 0.026 * (rnd(guide_index, 1.0) - 0.5)
        end_z = root.z - length
        end_x = clamp(root.x + side * (0.044 + 0.040 * crown + 0.032 * front), -0.145, 0.145)
        end_y = root.y + 0.020 * back - 0.010 * front
        p0 = root
        p1 = root + normal * (0.008 + 0.004 * crown) + Vector((side * (0.016 + 0.010 * front), -0.0025 * front, 0.006))
        p2 = Vector((end_x - side * 0.012, end_y, end_z + 0.070))
        p3 = Vector((end_x, end_y, end_z))
        guide = []
        phase = rnd(guide_index, 2.0) * math.tau
        wave_amp = 0.0045 + 0.0065 * rnd(guide_index, 3.0)
        for point_index in range(POINTS_PER_STRAND):
            t = point_index / (POINTS_PER_STRAND - 1)
            point = bezier(p0, p1, p2, p3, t)
            weight = smoothstep((t - 0.20) / 0.80)
            point.x += side * wave_amp * math.sin(phase + t * math.tau * 0.78) * weight
            point.y += wave_amp * 0.42 * math.cos(phase + t * math.tau * 0.78) * weight
            if front > 0.18 and point_index >= 2:
                avoid = front * smoothstep((t - 0.08) / 0.48)
                safe_x = side * (0.078 + 0.032 * smoothstep(t))
                if side < 0.0:
                    point.x = min(point.x, point.x * (1.0 - avoid) + safe_x * avoid)
                else:
                    point.x = max(point.x, point.x * (1.0 - avoid) + safe_x * avoid)
            guide.append(point)
        guides.append(guide)
        guide_meta.append((root, normal, side, guide_index))
        guide_index += 1

strands = []
for guide, (_root, normal, side, index) in zip(guides, guide_meta):
    tangent = Vector((normal.z, 0.0, -normal.x)).normalized()
    bitangent = normal.cross(tangent).normalized()
    for follow in range(FOLLOW_PER_GUIDE):
        if follow == 0:
            strands.append([point.copy() for point in guide])
            continue
        angle = math.tau * rnd(index * 19 + follow, 5.0)
        radius = 0.0008 + 0.0034 * math.sqrt(rnd(index * 19 + follow, 6.0))
        offset = tangent * (math.cos(angle) * radius) + bitangent * (math.sin(angle) * radius)
        length_jitter = (rnd(index * 19 + follow, 7.0) - 0.5) * 0.024
        phase = rnd(index * 19 + follow, 8.0) * math.tau
        follow_points = []
        for point_index, base in enumerate(guide):
            t = point_index / (POINTS_PER_STRAND - 1)
            point = base + offset * (0.78 + 0.22 * smoothstep(t))
            point.z += length_jitter * smoothstep(t)
            fine = math.sin(phase + t * math.tau * 1.15) * 0.00075 * smoothstep(t)
            point.x += side * fine
            point.y += fine * 0.35
            follow_points.append(point)
        strands.append(follow_points)

hair = create_hair(strands, len(guides), fiber_mat)
collision_projection = solve_collision(hair)
scene.frame_set(1)
scene["aevrynd_mainline_revision"] = "v249r259-cc0-guide-hair"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_hair_layers"] = "scalp.shadow|guide_follow.mass"
scene["aevrynd_release_state"] = "HAIR_VISUAL_AND_COLLISION_AUDIT_PENDING"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    ("01-frame1-front", 1, (0.0, -0.82, 1.62), (0.0, -0.02, 1.60), 88),
    ("02-frame1-top", 1, (0.0, -0.25, 2.17), (0.0, 0.01, 1.67), 78),
    ("03-frame1-three-quarter", 1, (0.50, -0.75, 1.63), (0.0, -0.01, 1.59), 86),
    ("04-frame1-profile", 1, (0.78, -0.03, 1.62), (0.0, 0.0, 1.58), 90),
    ("05-frame1-back", 1, (0.0, 0.82, 1.62), (0.0, 0.01, 1.58), 88),
    ("06-frame20-three-quarter", 20, (0.50, -0.75, 1.63), (0.0, -0.01, 1.59), 86),
)
for args in views:
    render(camera, *args)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT),
    "guideCount": len(guides), "followPerGuide": FOLLOW_PER_GUIDE,
    "strandCount": len(strands), "pointsPerStrand": POINTS_PER_STRAND,
    "totalHairPoints": len(strands) * POINTS_PER_STRAND,
    "scalp": {"vertices": scalp_vertices, "faces": scalp_faces, "clearanceM": 0.00085},
    "hairClearanceM": CLEARANCE, "collisionProjection": collision_projection,
    "layers": ["hair.scalp.shadow", "hair.guide_follow.mass"],
    "secondaryMotion": False,
    "renderDirectory": str(RENDER_DIR),
    "status": "HAIR_VISUAL_AND_COLLISION_AUDIT_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R259_CC0_GUIDE_HAIR=" + json.dumps(report, sort_keys=True))
