import hashlib
import json
import struct
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-converged-upper-lid-r210.blend"
MATERIAL_SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-layered-optical-stack-r420.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-open-topology-physical-skin-r446.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-open-topology-physical-skin-r446.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r446-open-topology-physical-skin"
BODY = "AevryndFemaleBodyBaseV118"
SKIN = "Aevrynd_Skin_Physical_R252"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def geometry_hash(obj):
    digest = hashlib.sha256()
    for vertex in obj.data.vertices:
        digest.update(struct.pack("<3d", *vertex.co))
    for polygon in obj.data.polygons:
        digest.update(struct.pack("<I", len(polygon.vertices)))
        for index in polygon.vertices:
            digest.update(struct.pack("<I", index))
    return digest.hexdigest()


def neutral_lights(scene):
    for obj in list(bpy.data.objects):
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)
    target = (0.0, -0.025, 1.60)
    for name, location, energy, size in (
        ("Aevrynd Neutral Key R446", (-0.42, -0.82, 1.82), 13.5, 0.56),
        ("Aevrynd Neutral Fill R446", (0.48, -0.62, 1.70), 8.4, 0.68),
        ("Aevrynd Neutral Top R446", (0.0, -0.08, 2.28), 7.7, 0.52),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.color, data.shape, data.size = energy, (1.0, 1.0, 1.0), "DISK", size
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
        obj.location = location
        look_at(obj, target)
    scene.world.use_nodes = True
    background = next(node for node in scene.world.node_tree.nodes if node.type == "BACKGROUND")
    background.inputs["Color"].default_value = (0.018, 0.018, 0.018, 1.0)
    background.inputs["Strength"].default_value = 0.12


def is_large_hair(obj):
    name = obj.name.lower()
    if any(token in name for token in ("brow", "lash", "lid", "tear", "caruncle", "eye")):
        return False
    materials = getattr(obj.data, "materials", ()) if hasattr(obj, "data") else ()
    material_names = " ".join(material.name.lower() for material in materials if material)
    return obj.type in {"MESH", "CURVES", "CURVE"} and any(token in name or token in material_names for token in ("hair", "scalp", "groom", "flyaway", "root", "lock", "fiber"))


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
before_hash = geometry_hash(body)
with bpy.data.libraries.load(str(MATERIAL_SOURCE), link=False) as (data_from, data_to):
    if SKIN not in data_from.materials:
        raise RuntimeError("Physical skin material not found")
    data_to.materials = [SKIN]
skin = data_to.materials[0]
body.data.materials.clear()
body.data.materials.append(skin)
after_hash = geometry_hash(body)
if before_hash != after_hash:
    raise RuntimeError("Material-only transfer changed body geometry")
body["aevrynd_revision"] = "v249r446"
body["aevrynd_skin_material_source"] = str(MATERIAL_SOURCE)

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
neutral_lights(scene)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
hair = {obj.name: obj.hide_render for obj in bpy.data.objects if is_large_hair(obj)}
for name in hair:
    bpy.data.objects[name].hide_render = True
views = (
    ("face", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92, (1000, 1000)),
    ("eyes", (0.0, -0.46, 1.615), (0.0, -0.035, 1.610), 105, (1200, 760)),
    ("three-quarter", (0.44, -0.63, 1.62), (0.0, -0.02, 1.595), 88, (1000, 1000)),
)
for name, location, target, lens, size in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(RENDER_DIR / f"r446-{name}-no-hair.png")
    bpy.ops.render.render(write_still=True)
for name, hidden in hair.items():
    bpy.data.objects[name].hide_render = hidden
camera.location = (0.0, -0.68, 1.605)
camera.data.lens = 92
look_at(camera, (0.0, -0.035, 1.606))
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.filepath = str(RENDER_DIR / "r446-face-with-hair.png")
bpy.ops.render.render(write_still=True)

status = "RETAINED_OPEN_TOPOLOGY_BASELINE_COLLISION_REVALIDATION_REQUIRED"
scene["aevrynd_open_topology_physical_skin"] = "v249r446"
scene["aevrynd_release_state"] = status
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "materialSource": str(MATERIAL_SOURCE),
    "output": str(OUTPUT),
    "renderDirectory": str(RENDER_DIR),
    "body": BODY,
    "material": skin.name,
    "geometrySha256Before": before_hash,
    "geometrySha256After": after_hash,
    "geometryIdentical": before_hash == after_hash,
    "inheritedR210RigAndCollisionGeometry": True,
    "strictVisualFinding": "Natural open eyelid continuity is retained and the physical skin avoids the r210 overbright response. Nose and midface depth, brows, hairline and groom remain below hero quality.",
    "strictFaceScore100": 50,
    "derivedOnlyFromOwnedCC0Mainline": True,
    "websitePromotionApproved": False,
    "colorManagement": {"viewTransform": "Standard", "look": "None", "exposureEV": 0.0, "neutralWhiteLights": True},
    "status": status,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R446_OPEN_TOPOLOGY_PHYSICAL_SKIN=" + json.dumps(report, sort_keys=True))
