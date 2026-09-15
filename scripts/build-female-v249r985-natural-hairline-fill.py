"""Add a target-native, collision-cleared frontal hairline fill to r981.

This is a visual study only.  It keeps the audited r981 groom unchanged and adds
short, swept fibres rooted directly on the evaluated r962-derived head surface.
"""

import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-coherent-clump-waves-r981.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-natural-hairline-fill-r985.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-natural-hairline-fill-r985.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r985-natural-hairline-fill"
BODY = "AevryndFemaleCC0Baseline_v259"
RIG = "AevryndFemaleRig"
FILL = "AevryndFemaleNaturalHairlineFill_R985"
POINTS = 18
ROOTS = 74
FOLLOWERS = 12
CLEARANCE = 0.00165


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def smoothstep(v):
    v = clamp(v)
    return v * v * (3.0 - 2.0 * v)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def surface_data(obj):
    ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = ev.to_mesh()
    verts = [ev.matrix_world @ v.co for v in mesh.vertices]
    faces = [tuple(p.vertices) for p in mesh.polygons]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, faces, all_triangles=False)


def nearest_clear(tree, point):
    hit = tree.find_nearest(point, 0.10)
    if hit is None or hit[1] is None:
        return point
    nearest, normal, _face, _distance = hit
    normal.normalize()
    signed = (point - nearest).dot(normal)
    return nearest + normal * CLEARANCE if signed < CLEARANCE else point


def hairline_z(x):
    # Soft widow-free oval: lower centre, mild corner recession, low temple join.
    u = abs(x) / 0.101
    centre_to_corner = 0.015 * math.sin(min(1.0, u) * math.pi * 0.72)
    temple_drop = 0.013 * smoothstep((u - 0.72) / 0.28)
    return 1.526 + centre_to_corner - temple_drop


def root_on_head(tree, x, z):
    # Cast from in front of the face toward the back of the skull.
    hit = tree.ray_cast(Vector((x, -0.22, z)), Vector((0.0, 1.0, 0.0)), 0.30)
    if hit[0] is None or hit[1] is None:
        hit = tree.find_nearest(Vector((x, -0.105, z)), 0.055)
    if hit is None or hit[0] is None or hit[1] is None:
        raise RuntimeError(f"No frontal head hit at x={x:.4f}, z={z:.4f}")
    return hit[0] + hit[1].normalized() * CLEARANCE, hit[1].normalized()


def bezier(a, b, c, d, t):
    u = 1.0 - t
    return a * u ** 3 + b * 3.0 * u * u * t + c * 3.0 * u * t * t + d * t ** 3


def make_strands(tree):
    strands = []
    roots = []
    for root_index in range(ROOTS):
        rng = random.Random(985000 + root_index)
        x = -0.095 + 0.190 * root_index / (ROOTS - 1)
        x += rng.uniform(-0.0009, 0.0009)
        z = hairline_z(x) + rng.uniform(-0.0018, 0.0022)
        root, normal = root_on_head(tree, x, z)
        roots.append(root)
        side = -1.0 if x < 0.0 else 1.0
        centre = 1.0 - clamp(abs(x) / 0.101)
        # The first tangent follows the scalp upward/backward; the lock then joins
        # the side mass.  This avoids a horizontal fringe across the forehead.
        length = 0.105 + 0.075 * centre + rng.uniform(-0.012, 0.012)
        end = Vector((
            x + side * (0.034 + 0.040 * centre),
            root.y + 0.010 + 0.018 * centre,
            z - length,
        ))
        p1 = root + normal * 0.0025 + Vector((side * 0.012, 0.010, 0.017))
        p2 = Vector((end.x - side * 0.013, end.y + 0.006, end.z + 0.045))
        base = [bezier(root, p1, p2, end, i / (POINTS - 1)) for i in range(POINTS)]
        tangent = Vector((normal.z, 0.0, -normal.x)).normalized()
        bitangent = normal.cross(tangent).normalized()
        for follower in range(FOLLOWERS):
            angle = math.tau * ((follower * 0.61803398875 + rng.random() * 0.06) % 1.0)
            radius = 0.00025 if follower == 0 else 0.0007 + 0.0022 * math.sqrt(rng.random())
            offset = tangent * math.cos(angle) * radius + bitangent * math.sin(angle) * radius
            follower_root = nearest_clear(tree, root + offset)
            delta = follower_root - root
            strand = []
            phase = rng.uniform(0.0, math.tau)
            for i, source in enumerate(base):
                t = i / (POINTS - 1)
                w = smoothstep((t - 0.12) / 0.88)
                point = source + delta * (1.0 - 0.55 * w) + offset * (0.18 + 0.82 * w)
                point.x += side * math.sin(phase + t * math.pi * 1.3) * 0.0018 * w
                point.y += math.cos(phase + t * math.pi) * 0.0007 * w
                strand.append(nearest_clear(tree, point) if point.z > 1.36 else point)
            strands.append(strand)
    return strands, roots


def material():
    mat = bpy.data.materials.new("Aevrynd_HairlineMelanin_R985")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    hair = nodes.new("ShaderNodeBsdfHairPrincipled")
    hair.parametrization = "MELANIN"
    for name, value in (("Melanin", 0.68), ("Melanin Redness", 0.24), ("Roughness", 0.38), ("IOR", 1.55), ("Random Color", 0.10), ("Random Roughness", 0.08)):
        if name in hair.inputs:
            hair.inputs[name].default_value = value
    links.new(hair.outputs[0], output.inputs["Surface"])
    return mat


def make_hair(strands):
    data = bpy.data.hair_curves.new(FILL + "Data")
    data.add_curves([POINTS] * len(strands))
    data.points.foreach_set("position", [c for strand in strands for p in strand for c in p])
    radius = data.attributes.new("radius", "FLOAT", "POINT")
    values = []
    for _strand in strands:
        for i in range(POINTS):
            t = i / (POINTS - 1)
            values.append(0.000105 * (1.0 - 0.76 * smoothstep(t)))
    radius.data.foreach_set("value", values)
    data.materials.append(material())
    obj = bpy.data.objects.new(FILL, data)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_layer"] = "hair.hairline.short_swept_fill"
    obj["aevrynd_revision"] = "v249r985"
    obj["aevrynd_source"] = "Aevrynd generated from evaluated target head"
    obj["aevrynd_collision_clearance_m"] = CLEARANCE
    return obj


def bind_head(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


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
tree = surface_data(bpy.data.objects[BODY])
strands, roots = make_strands(tree)
fill = make_hair(strands)
bind_head(fill, bpy.data.objects[RIG])
scene["aevrynd_mainline_revision"] = "v249r985-natural-hairline-fill"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "VISUAL_STUDY_PENDING_STRICT_REVIEW"
scene["aevrynd_website_promotion"] = "forbidden pending dynamic collision and runtime gates"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
scene.render.resolution_x = scene.render.resolution_y = 900
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects.get("Aevrynd Review Camera") or scene.camera
scene.camera = camera
for args in (
    ("01-face-front", (0.0, -0.68, 1.49), (0.0, -0.055, 1.48), 88),
    ("02-face-three-quarter", (0.42, -0.58, 1.51), (0.0, -0.045, 1.48), 88),
    ("03-face-profile", (0.68, -0.02, 1.50), (0.0, -0.035, 1.48), 90),
    ("04-hair-back", (0.0, 0.76, 1.50), (0.0, -0.01, 1.48), 86),
    ("05-hair-top", (0.0, -0.18, 2.05), (0.0, -0.02, 1.57), 82),
    ("06-full-three-quarter", (1.10, -1.62, 1.22), (0.0, -0.01, 0.92), 58),
):
    render(scene, camera, *args)
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "hairlineObject": fill.name,
    "rootCount": len(roots), "strandCount": len(strands), "pointsPerStrand": POINTS,
    "pointCount": len(strands) * POINTS, "clearanceM": CLEARANCE,
    "existingR981GroomChanged": False, "secondaryMotion": False,
    "websitePromotionApproved": False, "status": "STRICT_VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R985_NATURAL_HAIRLINE_FILL=" + json.dumps(report, sort_keys=True))
