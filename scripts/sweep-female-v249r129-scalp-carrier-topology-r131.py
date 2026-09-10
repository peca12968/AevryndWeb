import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-owned-hair-material-r129.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r129-scalp-carrier-topology-r131-sweep"
SCALP = "AevryndFemaleAnatomicalScalpFoundation_v249r101"
ATTRIBUTE = "aevrynd_root_density"


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    bpy.context.scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


def make_filtered(source, name, keep):
    world = source.matrix_world
    faces = []
    for polygon in source.data.polygons:
        center = world @ polygon.center
        if keep(center):
            faces.append(tuple(polygon.vertices))
    data = bpy.data.meshes.new(name + "Data")
    data.from_pydata([vertex.co.copy() for vertex in source.data.vertices], [], faces)
    data.update()
    source_attribute = source.data.attributes[ATTRIBUTE]
    attribute = data.attributes.new(ATTRIBUTE, "FLOAT", "POINT")
    for index, item in enumerate(source_attribute.data):
        attribute.data[index].value = item.value
    for material in source.data.materials:
        data.materials.append(material)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = world
    obj["aevrynd_layer"] = "hair.scalp.topology_ablation"
    return obj, len(faces)


def front_root_threshold(point):
    side = min(1.0, abs(point.x) / 0.112)
    return 1.696 + 0.027 * side ** 1.65


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scalp = bpy.data.objects[SCALP]
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
    ("top", (0.0, -0.25, 2.15), (0.0, 0.015, 1.66), 78),
)
report = {"source": str(SOURCE), "variants": []}

for suffix, location, target, lens in views:
    render(camera, f"a-baseline-{suffix}", location, target, lens)
report["variants"].append({"name": "a-baseline", "faces": len(scalp.data.polygons)})

scalp.hide_render = True
for suffix, location, target, lens in views:
    render(camera, f"b-no-scalp-{suffix}", location, target, lens)
report["variants"].append({"name": "b-no-scalp", "faces": 0})

crown, crown_faces = make_filtered(
    scalp,
    "AevryndScalpCarrierCrownOnly_v249r131",
    lambda point: point.y > -0.035,
)
for suffix, location, target, lens in views:
    render(camera, f"c-crown-only-{suffix}", location, target, lens)
report["variants"].append({"name": "c-crown-only", "faces": crown_faces})
crown.hide_render = True

root_backline, root_faces = make_filtered(
    scalp,
    "AevryndScalpCarrierRootBackline_v249r131",
    lambda point: point.y > -0.035 or point.z >= front_root_threshold(point),
)
for suffix, location, target, lens in views:
    render(camera, f"d-root-backline-{suffix}", location, target, lens)
report["variants"].append({"name": "d-root-backline", "faces": root_faces})

(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R131_SCALP_TOPOLOGY=" + json.dumps(report, sort_keys=True))
