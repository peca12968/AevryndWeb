"""Test the owned r446 lip topology as a donor for the retained r1033 face."""

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-lower-lip-rim-turn-r1033-study.blend"
DONOR = ASSETS / "aevrynd-female-authoring-v249-mainline-open-topology-physical-skin-r446.blend"
REPORT = ASSETS / "female-v249-mainline-r1045-mouth-donor-fit-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "v249r1045-mouth-donor-fit-sweep"
NAMES = ("Lip_Upper", "Lip_Lower", "Mouth_WetLine")
VARIANTS = (
    ("a-high", -0.1390, 1.00, 1.00, 0.0000),
    ("b-aligned", -0.1420, 1.00, 1.00, 0.0000),
    ("c-low", -0.1450, 1.00, 1.00, 0.0000),
    ("d-wide-soft", -0.1420, 1.06, 1.10, 0.0008),
    ("e-narrow-deep", -0.1420, 0.95, 0.92, 0.0020),
    ("f-front-4mm", -0.1420, 1.00, 1.00, -0.0040),
    ("g-front-8mm", -0.1420, 1.00, 1.00, -0.0080),
)


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def hide_large_hair(scene):
    hidden = []
    for obj in scene.objects:
        name = obj.name.lower()
        face_fibre = any(token in name for token in ("brow", "lash"))
        hair = obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "hairfiber", "haircard"))
        if hair and not face_fibre and not obj.hide_render:
            obj.hide_render = True
            hidden.append(obj.name)
    return hidden


def append_donors():
    with bpy.data.libraries.load(str(DONOR), link=False) as (data_from, data_to):
        data_to.objects = [name for name in NAMES if name in data_from.objects]
    result = []
    for obj in data_to.objects:
        if obj is None:
            continue
        bpy.context.scene.collection.objects.link(obj)
        obj.name = f"R1045_Donor_{obj.name}"
        obj.hide_render = False
        obj.hide_viewport = False
        result.append(obj)
    return result


def fit_donors(objects, z_shift, x_scale, z_scale, y_shift):
    centre = Vector((0.0, -0.1285, 1.5296))
    for obj in objects:
        obj.location.y += y_shift
        obj.location.z += z_shift
        for vertex in obj.data.vertices:
            world = obj.matrix_world @ vertex.co
            world.x = centre.x + (world.x - centre.x) * x_scale
            world.z = centre.z + (world.z - centre.z) * z_scale
            vertex.co = obj.matrix_world.inverted() @ world
        obj["aevrynd_role"] = "r446-owned-topology-donor-diagnostic"


def render(scene, label, location, target, lens, size):
    camera = scene.camera
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    path = RENDER_DIR / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    return str(path)


RENDER_DIR.mkdir(parents=True, exist_ok=True)
variants = []
for label, z_shift, x_scale, z_scale, y_shift in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    donors = append_donors()
    if len(donors) != len(NAMES):
        raise RuntimeError(f"Missing donor objects: {[obj.name for obj in donors]}")
    fit_donors(donors, z_shift, x_scale, z_scale, y_shift)
    hidden = hide_large_hair(scene)
    renders = [
        render(scene, f"{label}-mouth-front", (0.0, -0.43, 1.388), (0.0, -0.120, 1.386), 135, (1200, 700)),
        render(scene, f"{label}-mouth-oblique", (0.21, -0.39, 1.392), (0.0, -0.115, 1.386), 128, (1200, 700)),
        render(scene, f"{label}-face-front", (0.0, -0.72, 1.430), (0.0, -0.060, 1.420), 88, (900, 900)),
    ]
    body = bpy.data.objects.get("AevryndFemaleCC0Baseline_v259")
    if body:
        body.hide_render = True
        renders.append(render(scene, f"{label}-donor-isolation", (0.0, -0.43, 1.388), (0.0, -0.120, 1.386), 135, (1200, 700)))
        body.hide_render = False
    variants.append({
        "label": label,
        "zShiftM": z_shift,
        "xScale": x_scale,
        "zScale": z_scale,
        "yShiftM": y_shift,
        "donorObjects": [obj.name for obj in donors],
        "renders": renders,
        "collisionStatus": "NOT_A_CANDIDATE_DETACHED_OVERLAY",
    })
    for name in hidden:
        bpy.data.objects[name].hide_render = False

report = {
    "revision": "v249r1045-mouth-donor-fit-sweep",
    "source": str(SOURCE),
    "donor": str(DONOR),
    "license": "same owned CC0-derived Aevrynd mainline",
    "method": "visual topology donor alignment only; no website promotion and no detached overlay acceptance",
    "variants": variants,
    "status": "DIAGNOSTIC_ONLY_PENDING_STRICT_VISUAL_REVIEW",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1045_DONOR_SWEEP=" + json.dumps({"report": str(REPORT), "variants": len(variants)}, sort_keys=True))
