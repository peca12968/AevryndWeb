import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hair-cleanup-r84.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-hair-clump-density-r85-sweep"
MAIN = "AevryndFemaleGuideBob_v249r25"
POINTS = 20
FAMILY_SIZE = 25


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def smoothstep(value):
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def selected_front_families(data):
    selected = []
    for family in range(len(data.curves) // FAMILY_SIZE):
        representative = family * FAMILY_SIZE
        curve = data.curves[representative]
        root = data.points[curve.first_point_index].position
        tip = data.points[curve.first_point_index + curve.points_length - 1].position
        if root.y < -0.075 and root.z > 1.60 and tip.x > 0.075:
            selected.append((family, root.x, root.y, root.z))
    return [entry[0] for entry in sorted(selected, key=lambda entry: (entry[1], entry[2], entry[3]))]


def apply_density(data, radius, original, families, strength):
    for index, value in enumerate(original):
        radius.data[index].value = value
    if strength == 0.0:
        data.update_tag()
        return
    if strength < 0.0:
        for family in families:
            for follow in range(FAMILY_SIZE):
                curve = data.curves[family * FAMILY_SIZE + follow]
                for point_index in range(curve.points_length):
                    radius.data[curve.first_point_index + point_index].value = 1.0e-8
        data.update_tag()
        return
    total = max(1, len(families) - 1)
    for rank, family in enumerate(families):
        # Nine broad bundles vary the opacity of the fringe without changing
        # roots or paths. Boundaries remain present as fine fibers rather than
        # opening bald slots.
        phase = rank / total * math.pi * 9.0
        macro = 0.28 + 0.72 * (0.5 + 0.5 * math.cos(phase)) ** 0.62
        macro = 1.0 + (macro - 1.0) * strength
        for follow in range(FAMILY_SIZE):
            curve_index = family * FAMILY_SIZE + follow
            curve = data.curves[curve_index]
            micro_distance = abs((follow % 5) - 2) / 2.0
            micro = 1.0 - strength * 0.58 * smoothstep(micro_distance)
            deterministic = 0.92 + 0.08 * math.sin(curve_index * 2.399963)
            scale = max(0.12, macro * micro * deterministic)
            for point_index in range(curve.points_length):
                flat = curve.first_point_index + point_index
                t = point_index / max(1, curve.points_length - 1)
                # Keep roots readable and taper the final third more strongly.
                local = 1.0 + (scale - 1.0) * smoothstep((t - 0.05) / 0.42)
                local *= 1.0 - strength * 0.18 * smoothstep((t - 0.72) / 0.28)
                radius.data[flat].value = original[flat] * max(0.08, local)
    data.update_tag()


def render(camera, name, location, target, lens):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
hair = bpy.data.objects[MAIN]
radius = hair.data.attributes.get("radius")
if radius is None or radius.domain != "POINT":
    raise RuntimeError("Expected POINT radius attribute on main groom")
original = [item.value for item in radius.data]
families = selected_front_families(hair.data)

views = (
    ("face", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("three-quarter", (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82),
    ("top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78),
)
for label, strength in (("control", 0.0), ("medium", 0.50), ("strong", 0.82), ("maximum", 1.0), ("removed", -1.0)):
    apply_density(hair.data, radius, original, families, strength)
    for view, location, target, lens in views:
        render(camera, f"{label}-{view}", location, target, lens)

report = {
    "source": str(SOURCE),
    "selected_front_families": families,
    "family_count": len(families),
    "curve_count": len(families) * FAMILY_SIZE,
    "strengths": {"control": 0.0, "medium": 0.50, "strong": 0.82, "maximum": 1.0, "removed": -1.0},
    "geometry_changed": False,
    "method": "nine macro density bundles plus five-follow micro-clump taper on the existing collision-safe paths",
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249_HAIR_CLUMP_DENSITY_R85_SWEEP=" + json.dumps(report, sort_keys=True))
