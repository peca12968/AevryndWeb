import json
from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-layered-optical-stack-r420.blend"
DONOR = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-eyelid-r78.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-open-eyelid-hybrid-r443-study.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-open-eyelid-hybrid-r443.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r443-open-eyelid-topology-hybrid"
CURRENT_BODY = "AevryndFemaleBody_CC0_R249"
DONOR_BODY = "AevryndFemaleBodyBaseV118"
RIG = "AevryndFemaleRig"
EYE_LAYERS = ("ScleraOpen", "LimbalAnnulus", "IrisConcave", "PupilRecessed", "CorneaConvex")


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def world_bvh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def topology_stats(obj):
    edge_faces = defaultdict(int)
    for polygon in obj.data.polygons:
        vertices = list(polygon.vertices)
        for index, vertex in enumerate(vertices):
            edge_faces[tuple(sorted((vertex, vertices[(index + 1) % len(vertices)])))] += 1
    return {
        "vertices": len(obj.data.vertices),
        "edges": len(obj.data.edges),
        "faces": len(obj.data.polygons),
        "quads": sum(len(polygon.vertices) == 4 for polygon in obj.data.polygons),
        "triangles": sum(len(polygon.vertices) == 3 for polygon in obj.data.polygons),
        "boundaryEdges": sum(count == 1 for count in edge_faces.values()),
    }


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
current = bpy.data.objects[CURRENT_BODY]
skin = current.data.materials[0]
with bpy.data.libraries.load(str(DONOR), link=False) as (data_from, data_to):
    if DONOR_BODY not in data_from.objects:
        raise RuntimeError("Open-eyelid donor body not found")
    data_to.objects = [DONOR_BODY]
donor = data_to.objects[0]
scene.collection.objects.link(donor)
donor.name = "AevryndFemaleBody_OpenEyelid_R443"
donor.data.name = "AevryndFemaleBody_OpenEyelid_R443Geometry"
donor.data.materials.clear()
donor.data.materials.append(skin)
for modifier in donor.modifiers:
    if modifier.type == "ARMATURE":
        modifier.object = bpy.data.objects[RIG]
donor["aevrynd_layer"] = "body.skin.open_eyelid_topology.study"
donor["aevrynd_revision"] = "v249r443-study"
donor["aevrynd_geometry_source"] = str(DONOR)
current.hide_render = True
donor.hide_render = False

hair_visibility = {obj.name: obj.hide_render for obj in bpy.data.objects if is_large_hair(obj)}
for name in hair_visibility:
    bpy.data.objects[name].hide_render = True

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
scene.camera = camera
views = (
    ("face", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92, (1000, 1000)),
    ("eyes", (0.0, -0.46, 1.615), (0.0, -0.035, 1.610), 105, (1200, 760)),
    ("three-quarter", (0.44, -0.63, 1.62), (0.0, -0.02, 1.595), 88, (1000, 1000)),
    ("profile", (0.68, -0.05, 1.61), (0.0, -0.01, 1.595), 88, (1000, 1000)),
)
for name, location, target, lens, size in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(RENDER_DIR / f"r443-{name}-no-hair.png")
    bpy.ops.render.render(write_still=True)

for name, hidden in hair_visibility.items():
    bpy.data.objects[name].hide_render = hidden
camera.location = (0.0, -0.68, 1.605)
camera.data.lens = 92
look_at(camera, (0.0, -0.035, 1.606))
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.filepath = str(RENDER_DIR / "r443-face-with-hair.png")
bpy.ops.render.render(write_still=True)

bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
body_tree = world_bvh(donor, depsgraph)
overlaps = {
    side: {
        kind: len(body_tree.overlap(world_bvh(bpy.data.objects[f"AevryndEye_{side}_{kind}_R420"], depsgraph)))
        for kind in EYE_LAYERS
    }
    for side in ("L", "R")
}
collision_pass = all(value == 0 for side in overlaps.values() for value in side.values())
stats = topology_stats(donor)
status = "OPEN_EYELID_HYBRID_COLLISION_PASS_VISUAL_REVIEW_PENDING" if collision_pass else "REJECTED_OPEN_EYELID_HYBRID_COLLISION_FAIL"
scene["aevrynd_open_eyelid_hybrid_study"] = "v249r443"
scene["aevrynd_release_state"] = status
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "topologyDonor": str(DONOR),
    "output": str(OUTPUT),
    "renderDirectory": str(RENDER_DIR),
    "method": "Use the earlier owned open-eyelid continuous body topology with the r420 skin material, rig, optical eye stack and current hair for a reversible compatibility study.",
    "bodyTopology": stats,
    "frame1BodyOpticalTriangleOverlaps": overlaps,
    "gates": {"frame1BodyOpticalCollisionPass": collision_pass},
    "sameRigName": RIG,
    "derivedOnlyFromOwnedCC0Mainline": True,
    "websitePromotionApproved": False,
    "colorManagement": {"viewTransform": "Standard", "look": "None", "exposureEV": 0.0, "inheritedR420Lights": True},
    "status": status,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R443_OPEN_EYELID_HYBRID=" + json.dumps(report, sort_keys=True))
