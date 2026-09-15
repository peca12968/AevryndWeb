import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-orbital-brow-refit-r526.blend"
OUT = ASSETS / "reviews/v249r563-outer-canthus-wedge-sweep"
REPORT = ASSETS / "female-v249-mainline-outer-canthus-wedge-r563.study.json"
BODY = "AevryndFemaleBodyBaseV118"
EYES = {"L": 0.03453, "R": -0.03444}
CENTER_Z = 1.60805
VARIANTS = (("a-r526-control", 0.0), ("b-soft-0p40", 0.40), ("c-balanced-0p70", 0.70), ("d-strong-1p00", 1.00))


def gaussian(value, sigma):
    return math.exp(-0.5 * (value / sigma) ** 2)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, label, location, target, lens=120):
    scene.frame_set(1)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = 1300
    scene.render.resolution_y = 700
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

base_deltas = {}
per_eye = {side: 0 for side in EYES}
for index, point in enumerate(world_points):
    if point.y > -0.074 or not (1.604 < point.z < 1.618):
        continue
    for side, center_x in EYES.items():
        outward = 1.0 if center_x > 0.0 else -1.0
        outer_x = center_x + outward * 0.0112
        upper_z = CENTER_Z + 0.0040
        gate = gaussian(point.x - outer_x, 0.0040) * gaussian(point.z - upper_z, 0.0038) * gaussian(point.y + 0.0895, 0.0060)
        if gate < 0.012:
            continue
        # Collapse the raised triangular wedge into the lateral almond taper.
        # X/Z-only movement avoids pushing the lid toward the optical stack.
        movement = Vector((-outward * 0.00105 * gate, 0.0, -0.00175 * gate))
        if movement.length > 0.000002:
            base_deltas[index] = movement
            per_eye[side] += 1
        break


def apply(strength):
    for key_index, key in enumerate(keys):
        for index, source in enumerate(original[key_index]):
            movement = base_deltas.get(index)
            key.data[index].co = source if movement is None else source + inverse3 @ (movement * strength)
    body.data.update()


camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
variant_report = {}
for label, strength in VARIANTS:
    apply(strength)
    camera.location = (0.0, -0.48, 1.608)
    camera.data.lens = 120
    look_at(camera, (0.0, -0.055, 1.608))
    render(scene, camera, label, camera.location, (0.0, -0.055, 1.608), 120)
    variant_report[label] = {
        "strength": strength,
        "affectedVertices": len(base_deltas),
        "perEyeVertices": per_eye,
        "maximumMoveMm": max((movement.length for movement in base_deltas.values()), default=0.0) * strength * 1000.0,
    }

report = {
    "source": str(SOURCE),
    "method": "smooth symmetric X/Z contraction of the raised outer-canthus wedge on the continuous body; optical, lash, tear and iris objects remain unchanged",
    "shapeKeysMovedTogether": [key.name for key in keys],
    "variants": variant_report,
    "topologyChanged": False,
    "status": "VISUAL_CANTHUS_SWEEP_ONLY",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R563_OUTER_CANTHUS=" + json.dumps(report, sort_keys=True))
