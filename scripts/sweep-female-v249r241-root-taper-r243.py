import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-baked-root-veil-r241.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r243-root-taper-sweep"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-root-taper-r243.sweep-report.json"
VARIANTS = (
    ("a-r241-control", None),
    ("b-hybrid-material", 0),
    ("c-four-point-taper", 4),
    ("d-six-point-taper", 6),
)


def hair_objects():
    return [obj for obj in bpy.context.scene.objects if obj.type == "CURVES" and bool(obj.get("aevrynd_mainline_hair_collision"))]


def make_material(name, melanin, redness, roughness, radial, variation):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfHairPrincipled")
    shader.parametrization = "MELANIN"
    shader.inputs["Melanin"].default_value = melanin
    shader.inputs["Melanin Redness"].default_value = redness
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Radial Roughness"].default_value = radial
    shader.inputs["Coat"].default_value = 0.05
    shader.inputs["Random Color"].default_value = variation
    shader.inputs["Random Roughness"].default_value = 0.07
    links.new(shader.outputs[0], output.inputs["Surface"])
    return material


def assign_hybrid(objects):
    base = make_material("AevryndFemaleHairBase_v249r243", 0.82, 0.28, 0.46, 0.34, 0.10)
    overlay = make_material("AevryndFemaleHairOverlay_v249r243", 0.74, 0.34, 0.42, 0.30, 0.16)
    for obj in objects:
        obj.data.materials.clear()
        obj.data.materials.append(overlay if "overlay" in str(obj.get("aevrynd_layer", "")) else base)
    return base.name, overlay.name


def taper_roots(objects, count):
    changed = 0
    for obj in objects:
        radius = obj.data.attributes.get("radius")
        if radius is None:
            continue
        for curve in obj.data.curves:
            local_count = min(count, curve.points_length)
            for local_index in range(local_count):
                # Smoothly grow from 8% at the follicle to the authored width.
                t = (local_index + 1) / max(1, local_count)
                factor = 0.08 + 0.92 * t * t * (3.0 - 2.0 * t)
                index = curve.first_point_index + local_index
                radius.data[index].value *= factor
                changed += 1
        obj.data.update_tag()
    return changed


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, filename, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


OUT.mkdir(parents=True, exist_ok=True)
report = {"source": str(SOURCE), "positionGeometryChanged": False, "variants": {}}
for label, taper_count in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    objects = hair_objects()
    materials = None
    changed = 0
    if taper_count is not None:
        materials = assign_hybrid(objects)
        if taper_count:
            changed = taper_roots(objects, taper_count)
    camera = bpy.data.objects["Aevrynd Review Camera"]
    for view_name, location, target, lens in (
        ("01-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
        ("02-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
        ("03-back", (0.0, 0.72, 1.60), (0.0, 0.025, 1.595), 88),
        ("04-top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
    ):
        render(camera, f"{label}-{view_name}.png", location, target, lens)
    report["variants"][label] = {
        "rootTaperPointCount": taper_count,
        "radiusValuesChanged": changed,
        "materials": materials or "r241-control",
    }
report["status"] = "STRICT_VISUAL_SELECTION_PENDING"
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R243_ROOT_TAPER=" + json.dumps(report, sort_keys=True))
