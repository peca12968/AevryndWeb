import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-orbital-brow-refit-r526.blend"
OUT = ASSETS / "reviews/v249r560-lower-face-proportion-sweep"
REPORT = ASSETS / "female-v249-mainline-lower-face-proportion-r560.study.json"
BODY = "AevryndFemaleBodyBaseV118"
VARIANTS = (
    ("a-r526-control", 0.0, 0.0, 0.0),
    ("b-subtle", 1.5, 0.8, 1.5),
    ("c-balanced", 3.0, 1.4, 3.0),
    ("d-strong", 4.5, 2.0, 4.5),
)


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, label, location, target, lens=102):
    scene.frame_set(1)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(OUT / f"{label}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.image_settings.file_format = "PNG"
OUT.mkdir(parents=True, exist_ok=True)

for obj in bpy.data.objects:
    name = obj.name.lower()
    layer = str(obj.get("aevrynd_layer", "")).lower()
    if "hair" in name or layer.startswith("hair"):
        obj.hide_render = True
        obj.hide_viewport = True

body = bpy.data.objects[BODY]
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(depsgraph)
mesh = evaluated.to_mesh()
world_points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
evaluated.to_mesh_clear()
keys = list(body.data.shape_keys.key_blocks)
original = [[point.co.copy() for point in key.data] for key in keys]
inverse3 = body.matrix_world.inverted().to_3x3()


def build_deltas(jaw_mm, malar_mm, chin_mm):
    deltas = {}
    region_counts = {"jaw": 0, "malar": 0, "chin": 0}
    for index, point in enumerate(world_points):
        ax = abs(point.x)
        if ax > 0.110 or point.y > -0.010 or not (1.405 < point.z < 1.625):
            continue
        side = -1.0 if point.x < 0.0 else 1.0
        jaw = gaussian(ax, 0.071, 0.021) * gaussian(point.z, 1.477, 0.036) * gaussian(point.y, -0.055, 0.055)
        jaw *= 1.0 - gaussian(ax, 0.0, 0.032)
        malar = gaussian(ax, 0.057, 0.018) * gaussian(point.z, 1.574, 0.022) * gaussian(point.y, -0.100, 0.028)
        chin = gaussian(ax, 0.0, 0.032) * gaussian(point.z, 1.458, 0.026) * gaussian(point.y, -0.100, 0.042)
        delta = Vector((-side * jaw_mm * 0.001 * jaw,
                        -malar_mm * 0.001 * malar,
                        chin_mm * 0.001 * chin))
        if delta.length <= 0.000002:
            continue
        deltas[index] = delta
        if jaw > 0.02:
            region_counts["jaw"] += 1
        if malar > 0.02:
            region_counts["malar"] += 1
        if chin > 0.02:
            region_counts["chin"] += 1
    return deltas, region_counts


def apply(deltas):
    for key_index, key in enumerate(keys):
        for index, source in enumerate(original[key_index]):
            movement = deltas.get(index)
            key.data[index].co = source if movement is None else source + inverse3 @ movement
    body.data.update()


camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
variant_report = {}
for label, jaw_mm, malar_mm, chin_mm in VARIANTS:
    deltas, region_counts = build_deltas(jaw_mm, malar_mm, chin_mm)
    apply(deltas)
    for view, location, target, lens in (
        ("front", (0.0, -0.57, 1.565), (0.0, -0.040, 1.555), 104),
        ("three-quarter", (0.38, -0.54, 1.575), (0.0, -0.035, 1.555), 100),
        ("profile", (0.60, -0.02, 1.570), (0.0, -0.025, 1.550), 104),
    ):
        render(scene, camera, f"{label}-{view}", location, target, lens)
    variant_report[label] = {
        "jawNarrowMm": jaw_mm,
        "malarForwardMm": malar_mm,
        "chinRaiseMm": chin_mm,
        "affectedVertices": len(deltas),
        "regionVertexCounts": region_counts,
        "maximumMoveMm": max((movement.length for movement in deltas.values()), default=0.0) * 1000.0,
    }

report = {
    "source": str(SOURCE),
    "method": "apply smooth lateral-jaw narrowing, anterior malar support and lower-chin raise to every existing body shape key; hide hair only for unobstructed review",
    "shapeKeysMovedTogether": [key.name for key in keys],
    "variants": variant_report,
    "topologyChanged": False,
    "skinMaterialChanged": False,
    "status": "VISUAL_PROPORTION_SWEEP_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R560_LOWER_FACE_PROPORTION=" + json.dumps(report, sort_keys=True))
