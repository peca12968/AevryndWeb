import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-baked-seam-clearance-r247.blend"
REFERENCE = ROOT / "assets-source/aevrynd-character/references/aevrynd-female-neutral-head-reference-r248.png"
OUT = ROOT.parent / "Temp/female-realism/v249r248-facial-structure-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-facial-structure-r248.sweep-report.json"
BODY = "AevryndFemaleBodyBaseV118"
VARIANTS = (("a-control", 0.0), ("b-conservative", 0.75), ("c-anatomical", 1.0), ("d-strong", 1.35))


def gaussian(value, center, sigma):
    return math.exp(-0.5 * ((value - center) / sigma) ** 2)


def consolidate(body):
    key = body.shape_key_add(name="Aevrynd_FacialStructure_R248", from_mix=True)
    previous = [old.name for old in body.data.shape_keys.key_blocks[1:-1]]
    for old in body.data.shape_keys.key_blocks[1:-1]:
        old.value = 0.0
    key.value = 1.0
    return key, previous


def sculpt(body, strength):
    key, previous = consolidate(body)
    region_names = (
        "supraorbital", "upper_lid_crease", "tear_trough", "malar", "mid_cheek",
        "alar_groove", "philtrum_groove", "philtrum_columns", "nasolabial",
        "mental_sulcus", "chin_pad", "jaw_taper",
    )
    counts = {name: 0 for name in region_names}
    maxima = {name: 0.0 for name in region_names}
    moved = 0
    maximum = 0.0
    for point in key.data:
        p = point.co.copy()
        ax = abs(p.x)
        side = -1.0 if p.x < 0.0 else 1.0
        front = gaussian(p.y, -0.112, 0.033)
        fields = {}

        fields["supraorbital"] = Vector((side * 0.00010, -0.00110, 0.00008)) * (
            gaussian(ax, 0.035, 0.020) * gaussian(p.z, 1.632, 0.010) * front
        )
        fields["upper_lid_crease"] = Vector((0.0, 0.00070, 0.00005)) * (
            gaussian(ax, 0.035, 0.022) * gaussian(p.z, 1.621, 0.0038) * gaussian(p.y, -0.118, 0.020)
        )
        fields["tear_trough"] = Vector((0.0, 0.00105, -0.00008)) * (
            gaussian(ax, 0.036, 0.019) * gaussian(p.z, 1.590, 0.0065) * front
        )
        fields["malar"] = Vector((side * 0.00022, -0.00155, 0.00015)) * (
            gaussian(ax, 0.055, 0.019) * gaussian(p.z, 1.570, 0.017) * front
        )
        fields["mid_cheek"] = Vector((side * 0.00015, -0.00065, -0.00005)) * (
            gaussian(ax, 0.068, 0.022) * gaussian(p.z, 1.535, 0.025) * front
        )
        fields["alar_groove"] = Vector((side * 0.00012, 0.00090, -0.00002)) * (
            gaussian(ax, 0.031, 0.0065) * gaussian(p.z, 1.550, 0.013) * gaussian(p.y, -0.122, 0.020)
        )
        fields["philtrum_groove"] = Vector((0.0, 0.00095, 0.00005)) * (
            gaussian(ax, 0.0, 0.0052) * gaussian(p.z, 1.540, 0.009) * gaussian(p.y, -0.124, 0.018)
        )
        fields["philtrum_columns"] = Vector((0.0, -0.00075, 0.00002)) * (
            gaussian(ax, 0.0085, 0.0038) * gaussian(p.z, 1.540, 0.009) * gaussian(p.y, -0.124, 0.018)
        )
        fold_x = 0.034 + 0.010 * max(0.0, min(1.0, (1.540 - p.z) / 0.038))
        fields["nasolabial"] = Vector((0.0, 0.00078, -0.00003)) * (
            gaussian(ax, fold_x, 0.0055) * gaussian(p.z, 1.517, 0.025) * front
        )
        fields["mental_sulcus"] = Vector((0.0, 0.00105, -0.00008)) * (
            gaussian(ax, 0.0, 0.027) * gaussian(p.z, 1.478, 0.0080) * front
        )
        fields["chin_pad"] = Vector((-side * 0.00018, -0.00145, 0.00016)) * (
            gaussian(ax, 0.016, 0.024) * gaussian(p.z, 1.456, 0.017) * gaussian(p.y, -0.094, 0.036)
        )
        fields["jaw_taper"] = Vector((-side * 0.00080, 0.00010, 0.0)) * (
            gaussian(ax, 0.072, 0.019) * gaussian(p.z, 1.472, 0.029) * gaussian(p.y, -0.075, 0.050)
        )

        delta = Vector()
        for name, component in fields.items():
            component *= strength
            if component.length <= 0.000020:
                continue
            delta += component
            counts[name] += 1
            maxima[name] = max(maxima[name], component.length)
        if delta.length > 0.000001:
            point.co += delta
            moved += 1
            maximum = max(maximum, delta.length)
    body.data.update()
    return {
        "shapeKey": key.name,
        "consolidatedShapeKeys": previous,
        "verticesMoved": moved,
        "maximumDeltaMm": maximum * 1000.0,
        "regions": counts,
        "componentMaxMm": {name: value * 1000.0 for name, value in maxima.items()},
    }


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, filename, location, target, lens, size=(1000, 1000)):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "reference": str(REFERENCE), "variants": {}, "status": "STRICT_VISUAL_SELECTION_PENDING"}
for label, strength in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    metrics = {"strength": strength}
    if strength:
        metrics.update(sculpt(bpy.data.objects[BODY], strength))
    camera = bpy.data.objects["Aevrynd Review Camera"]
    views = (
        ("01-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.585), 88),
        ("02-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.585), 88),
        ("03-face-profile", (0.70, -0.03, 1.60), (0.0, -0.010, 1.570), 92),
        ("04-lower-face", (0.0, -0.48, 1.515), (0.0, -0.045, 1.515), 105),
    )
    for view_name, location, target, lens in views:
        render(camera, f"{label}-{view_name}.png", location, target, lens)
    report["variants"][label] = metrics
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R248_FACIAL_STRUCTURE_SWEEP=" + json.dumps(report, sort_keys=True))
