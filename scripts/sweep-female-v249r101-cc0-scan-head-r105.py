import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-scalp-foundation-r101.blend"
REFERENCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-cc0-base-v1.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r101-cc0-scan-head-r105-sweep"
BODY = "AevryndFemaleBodyBaseV118"
REFERENCE_BODY = "AevryndFemaleBodyBase"


def smooth(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    lower = obj.name.lower()
    return layer.startswith("hair.") or any(token in lower for token in ("hair", "groom", "scalp"))


def load_reference():
    with bpy.data.libraries.load(str(REFERENCE), link=False) as (data_from, data_to):
        if REFERENCE_BODY not in data_from.objects:
            raise RuntimeError(f"Missing reference object: {REFERENCE_BODY}")
        data_to.objects = [REFERENCE_BODY]
    obj = data_to.objects[0]
    if not obj.users_collection:
        bpy.context.scene.collection.objects.link(obj)
    obj.name = "AevryndCC0ScanHeadReference_v249r105"
    for modifier in obj.modifiers:
        if modifier.type == "MULTIRES":
            modifier.levels = 1
            modifier.sculpt_levels = 1
            modifier.render_levels = 1
    obj.hide_render = True
    return obj


def evaluated_tree(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False), len(vertices), len(faces)


def reference_targets(body, tree):
    inverse = body.matrix_world.inverted()
    records = []
    distances = []
    for vertex in body.data.vertices:
        source = vertex.co.copy()
        world = body.matrix_world @ source
        ax = abs(world.x)
        weight = 0.0
        target = source.copy()
        if ax <= 0.125 and 1.425 <= world.z <= 1.690 and world.y <= 0.035:
            eye_guard = 0.012 < ax < 0.090 and 1.575 < world.z < 1.650
            lip_guard = ax < 0.068 and 1.492 < world.z < 1.548
            if not eye_guard and not lip_guard:
                hit = tree.find_nearest(world)
                if hit and hit[0] is not None and hit[3] <= 0.020:
                    front = smooth((0.035 - world.y) / 0.080)
                    vertical = smooth((world.z - 1.425) / 0.030) * (1.0 - smooth((world.z - 1.665) / 0.025))
                    weight = front * vertical
                    target = inverse @ hit[0]
                    distances.append((target - source).length)
        records.append((source, target, weight))
    return records, distances


def apply_transfer(body, records, blend):
    changed = 0
    maximum = 0.0
    total = 0.0
    for vertex, (source, target, weight) in zip(body.data.vertices, records):
        factor = blend * weight
        candidate = source.lerp(target, factor)
        vertex.co = candidate
        distance = (candidate - source).length
        if distance > 1.0e-8:
            changed += 1
            maximum = max(maximum, distance)
            total += distance
    body.data.update()
    return {"changedVertices": changed, "maximumDisplacementM": maximum, "averageChangedDisplacementM": total / max(1, changed)}


def render(camera, variant, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{variant}-{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
for obj in bpy.data.objects:
    if is_hair(obj):
        obj.hide_render = True
body = bpy.data.objects[BODY]
body.data = body.data.copy()
reference = load_reference()
tree, reference_vertices, reference_faces = evaluated_tree(reference)
records, distances = reference_targets(body, tree)
camera = bpy.data.objects["Aevrynd Review Camera"]
report = {
    "source": str(SOURCE), "reference": str(REFERENCE),
    "referenceEvaluatedVertices": reference_vertices, "referenceEvaluatedFaces": reference_faces,
    "eligibleVertices": len(distances),
    "referenceDistanceM": {"maximum": max(distances), "average": sum(distances) / len(distances)},
    "variants": [],
}
for blend in (0.0, 0.25, 0.50, 0.75, 1.0):
    geometry = apply_transfer(body, records, blend)
    variant = f"{blend:.2f}"
    for name, location, target, lens in (
        ("front", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108),
        ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
        ("profile", (0.70, -0.03, 1.61), (0.0, -0.005, 1.595), 88),
        ("low-three-quarter", (0.34, -0.54, 1.50), (0.0, -0.015, 1.565), 96),
    ):
        render(camera, variant, name, location, target, lens)
    report["variants"].append({"blend": blend, "geometry": geometry})

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R105_CC0_SCAN_HEAD_SWEEP=" + json.dumps(report, sort_keys=True))
