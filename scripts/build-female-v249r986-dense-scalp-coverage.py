"""Replace the sparse r976 scalp with a dense target-surface coverage shell."""

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-coherent-clump-waves-r981.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-dense-scalp-coverage-r986.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-dense-scalp-coverage-r986.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r986-dense-scalp-coverage"
BODY = "AevryndFemaleCC0Baseline_v259"
RIG = "AevryndFemaleRig"
OLD_SCALP = "AevryndFemaleTargetScalp_R976"
SCALP = "AevryndFemaleDenseScalpCoverage_R986"
OFFSET = 0.00145


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def smoothstep(v):
    v = clamp(v)
    return v * v * (3.0 - 2.0 * v)


def front_hairline(x):
    u = abs(x) / 0.105
    # A low centre, small temporal recession, then a soft temple join.
    return 1.524 + 0.014 * smoothstep(u / 0.62) - 0.013 * smoothstep((u - 0.78) / 0.22)


def selected(point):
    if abs(point.x) > 0.112 or point.z < 1.475 or point.y > 0.115:
        return False
    if point.y < -0.060:
        return point.z >= front_hairline(point.x)
    # Continue the shell down the back so no skin-colored holes appear between locks.
    rear = smoothstep((point.y + 0.060) / 0.155)
    return point.z >= 1.500 - 0.024 * rear


def make_shell(body):
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = ev.to_mesh()
    world = ev.matrix_world
    normal_matrix = world.to_3x3()
    points = [world @ v.co for v in mesh.vertices]
    normals = [(normal_matrix @ v.normal).normalized() for v in mesh.vertices]
    faces = [tuple(p.vertices) for p in mesh.polygons]
    ev.to_mesh_clear()
    keep = [f for f in faces if all(selected(points[i]) for i in f)]
    used = sorted({i for f in keep for i in f})
    remap = {old: new for new, old in enumerate(used)}
    verts = [points[i] + normals[i] * OFFSET for i in used]
    polys = [tuple(remap[i] for i in f) for f in keep]
    data = bpy.data.meshes.new(SCALP + "Data")
    data.from_pydata(verts, [], polys)
    data.update()
    obj = bpy.data.objects.new(SCALP, data)
    bpy.context.scene.collection.objects.link(obj)
    obj["aevrynd_layer"] = "hair.scalp.dense_coverage"
    obj["aevrynd_revision"] = "v249r986"
    obj["aevrynd_source"] = "Aevrynd generated from evaluated target head"
    obj["aevrynd_surface_offset_m"] = OFFSET
    return obj, len(verts), len(polys)


def material():
    mat = bpy.data.materials.new("Aevrynd_DenseScalpWarmBrown_R986")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.030, 0.0075, 0.0028, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.72
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.24
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return mat


def bind_head(obj, rig):
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


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
old = bpy.data.objects.get(OLD_SCALP)
if old:
    bpy.data.objects.remove(old, do_unlink=True)
scalp, vertex_count, polygon_count = make_shell(bpy.data.objects[BODY])
scalp.data.materials.append(material())
bind_head(scalp, bpy.data.objects[RIG])
scene["aevrynd_mainline_revision"] = "v249r986-dense-scalp-coverage"
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
    "source": str(SOURCE), "output": str(OUTPUT), "scalpObject": scalp.name,
    "vertexCount": vertex_count, "polygonCount": polygon_count, "surfaceOffsetM": OFFSET,
    "existingR981GroomChanged": False, "secondaryMotion": False,
    "websitePromotionApproved": False, "status": "STRICT_VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R986_DENSE_SCALP_COVERAGE=" + json.dumps(report, sort_keys=True))
