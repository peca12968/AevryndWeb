import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-integrated-eyelid-clearance-r472.blend"
REPORT = ASSETS / "female-v249-mainline-r473.nasal-midface-plane-sweep.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r473-nasal-midface-plane-sweep"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-nasal-midface-planes-r473.blend"
REVIEW_DIR = ASSETS / "reviews/v249r473-nasal-midface-planes"
BODY = "AevryndFemaleBodyBaseV118"
SELECTED_STRENGTH = 1.25


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, directory, label, location, target, lens, size, frame=1):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(directory / f"{label}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
body = bpy.data.objects[BODY]
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = body.evaluated_get(depsgraph)
evaluated_mesh = evaluated.to_mesh()
world_points = [evaluated.matrix_world @ vertex.co for vertex in evaluated_mesh.vertices]
evaluated.to_mesh_clear()

key_blocks = list(body.data.shape_keys.key_blocks)
original = [[point.co.copy() for point in block.data] for block in key_blocks]
inverse3 = body.matrix_world.inverted().to_3x3()
deltas = {}
regions = {name: 0 for name in (
    "dorsum", "radix", "sidewall", "supratip", "tip", "alar_wing", "alar_groove", "columella", "medial_midface",
)}
for index, point in enumerate(world_points):
    if abs(point.x) > 0.072 or not (1.520 < point.z < 1.635) or point.y > -0.070:
        continue
    ax = abs(point.x)
    side = -1.0 if point.x < 0.0 else 1.0
    delta = Vector()
    contributions = {}

    # Build a continuous nasal pyramid: a defined radix and narrow dorsum,
    # rather than a single spherical tip displacement.
    dorsum_gate = gaussian(ax, 0.0, 0.0105) * gaussian(point.z, 1.585, 0.026) * gaussian(point.y, -0.108, 0.036)
    contributions["dorsum"] = Vector((0.0, -0.00155, 0.0)) * dorsum_gate
    radix_gate = gaussian(ax, 0.0, 0.0120) * gaussian(point.z, 1.612, 0.012) * gaussian(point.y, -0.094, 0.026)
    contributions["radix"] = Vector((0.0, -0.00062, -0.00010)) * radix_gate

    sidewall_gate = gaussian(ax, 0.0165, 0.0080) * gaussian(point.z, 1.581, 0.025) * gaussian(point.y, -0.105, 0.035)
    contributions["sidewall"] = Vector((-side * 0.00072, 0.00018, 0.0)) * sidewall_gate

    # Preserve a subtle supratip break before projecting the lobule.
    supratip_gate = gaussian(ax, 0.0, 0.0130) * gaussian(point.z, 1.570, 0.0080) * gaussian(point.y, -0.132, 0.018)
    contributions["supratip"] = Vector((0.0, 0.00042, -0.00008)) * supratip_gate
    tip_gate = gaussian(ax, 0.0, 0.0150) * gaussian(point.z, 1.557, 0.0110) * gaussian(point.y, -0.137, 0.018)
    contributions["tip"] = Vector((0.0, -0.00145, 0.00028)) * tip_gate

    alar_gate = gaussian(ax, 0.0255, 0.0075) * gaussian(point.z, 1.548, 0.0110) * gaussian(point.y, -0.126, 0.022)
    contributions["alar_wing"] = Vector((side * 0.00068, -0.00062, 0.00006)) * alar_gate
    groove_gate = gaussian(ax, 0.0335, 0.0055) * gaussian(point.z, 1.552, 0.0140) * gaussian(point.y, -0.112, 0.026)
    contributions["alar_groove"] = Vector((-side * 0.00008, 0.00092, 0.00003)) * groove_gate

    columella_gate = gaussian(ax, 0.0, 0.0095) * gaussian(point.z, 1.539, 0.0090) * gaussian(point.y, -0.122, 0.024)
    contributions["columella"] = Vector((0.0, -0.00092, -0.00030)) * columella_gate

    # Add restrained maxillary support so the projected nose does not float
    # in front of a flat central face.
    midface_gate = gaussian(ax, 0.041, 0.014) * gaussian(point.z, 1.568, 0.021) * gaussian(point.y, -0.093, 0.030)
    eye_guard = 1.0 - gaussian(point.z, 1.6078, 0.010)
    contributions["medial_midface"] = Vector((-side * 0.00010, -0.00042, 0.00004)) * midface_gate * eye_guard

    # The body shell sits immediately behind independent lip and wet-line layers.
    # Fade all nasal edits to zero below the columella so the nose pass cannot
    # push the perioral body shell through those authored layers.
    perioral_guard = smoothstep((point.z - 1.543) / 0.011)
    for name, contribution in contributions.items():
        if contribution.length > 0.000015:
            delta += contribution * perioral_guard
            regions[name] += 1
    if delta.length > 0.000002:
        deltas[index] = delta


def apply_strength(strength):
    for block_index, block in enumerate(key_blocks):
        for index, source in enumerate(original[block_index]):
            world_delta = deltas.get(index)
            block.data[index].co = source if world_delta is None else source + inverse3 @ (world_delta * strength)
    body.data.update()


scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
views = (
    ("front", (0.0, -0.58, 1.575), (0.0, -0.040, 1.565), 96, (1000, 1000)),
    ("three-quarter", (0.40, -0.57, 1.58), (0.0, -0.030, 1.56), 92, (1000, 1000)),
    ("profile", (0.62, -0.02, 1.575), (0.0, -0.020, 1.555), 98, (1000, 1000)),
)
for label, strength in (("a-control", 0.0), ("b-balanced-080", 0.80), ("c-defined-100", 1.00), ("d-strong-125", 1.25)):
    apply_strength(strength)
    for view_name, location, target, lens, size in views:
        render(scene, camera, RENDER_DIR, f"{label}-{view_name}", location, target, lens, size)

apply_strength(SELECTED_STRENGTH)
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
selected_views = (
    ("01-front-f01", (0.0, -0.58, 1.575), (0.0, -0.040, 1.565), 96, (1000, 1000), 1),
    ("02-three-quarter-f01", (0.40, -0.57, 1.58), (0.0, -0.030, 1.56), 92, (1000, 1000), 1),
    ("03-profile-f01", (0.62, -0.02, 1.575), (0.0, -0.020, 1.555), 98, (1000, 1000), 1),
    ("04-three-quarter-f20", (0.40, -0.57, 1.58), (0.0, -0.030, 1.56), 92, (1000, 1000), 20),
)
for label, location, target, lens, size, frame in selected_views:
    render(scene, camera, REVIEW_DIR, label, location, target, lens, size, frame)

scene.frame_set(1)
body["aevrynd_face_revision"] = "r473-nasal-midface-planes"
body["aevrynd_nasal_midface_strength"] = SELECTED_STRENGTH
scene["aevrynd_character_revision"] = "v249r473"
scene["aevrynd_review_exposure"] = 0.0
scene["aevrynd_review_view_transform"] = "Standard"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "affectedVertices": len(deltas),
    "maximumNominalDisplacementM": max(delta.length for delta in deltas.values()),
    "shapeKeysMovedTogether": [block.name for block in key_blocks],
    "regionVertexCounts": regions,
    "variants": {"a-control": 0.0, "b-balanced-080": 0.80, "c-defined-100": 1.00, "d-strong-125": 1.25},
    "method": "continuous nasal pyramid, tip/alar/columella and restrained medial-midface fields applied identically to every shape key",
    "renderDirectory": str(RENDER_DIR),
    "selectedStrength": SELECTED_STRENGTH,
    "selectedOutput": str(OUTPUT),
    "selectedReviewDirectory": str(REVIEW_DIR),
    "selectionReason": "strongest tested setting remained plausible and gave the clearest nasal pyramid, supratip, tip and alar read at normal distance",
    "reviewColorManagement": {"viewTransform": "Standard", "look": "None", "exposure": 0.0},
    "status": "SELECTED_PENDING_COLLISION_AUDIT",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R473_NASAL_MIDFACE_SWEEP=" + json.dumps(report, sort_keys=True))
