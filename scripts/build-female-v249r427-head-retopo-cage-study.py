import json
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-layered-optical-stack-r420.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-head-retopo-cage-r427-study.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-head-retopo-cage-r427.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r427-head-retopo-cage-study"
BODY = "AevryndFemaleBody_CC0_R249"
NECK_CUT_Z = 1.405
TARGET_FACES = 18000


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def hide_large_hair():
    for obj in bpy.data.objects:
        name = obj.name.lower()
        if any(token in name for token in ("brow", "lash", "lid", "tear", "caruncle", "eye")):
            continue
        materials = getattr(obj.data, "materials", ()) if hasattr(obj, "data") else ()
        material_names = " ".join(material.name.lower() for material in materials if material)
        if obj.type in {"MESH", "CURVES", "CURVE"} and any(token in name or token in material_names for token in ("hair", "scalp", "groom", "flyaway", "root", "lock", "fiber")):
            obj.hide_render = True


def mesh_stats(obj):
    polygons = list(obj.data.polygons)
    return {
        "vertices": len(obj.data.vertices),
        "edges": len(obj.data.edges),
        "polygons": len(polygons),
        "triangles": sum(max(1, len(polygon.vertices) - 2) for polygon in polygons),
        "quads": sum(1 for polygon in polygons if len(polygon.vertices) == 4),
        "ngons": sum(1 for polygon in polygons if len(polygon.vertices) > 4),
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
source_body = bpy.data.objects[BODY]
depsgraph = bpy.context.evaluated_depsgraph_get()
evaluated = source_body.evaluated_get(depsgraph)
mesh = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=True, depsgraph=depsgraph)
cage = bpy.data.objects.new("AevryndFemaleHeadRetopoCage_R427", mesh)
bpy.context.scene.collection.objects.link(cage)
cage.matrix_world = source_body.matrix_world.copy()
cage["aevrynd_layer"] = "body.head.retopology_cage.study"
cage["aevrynd_revision"] = "v249r427-study"
cage["aevrynd_source"] = SOURCE.name

bm = bmesh.new()
bm.from_mesh(mesh)
remove = [vertex for vertex in bm.verts if (cage.matrix_world @ vertex.co).z < NECK_CUT_Z]
bmesh.ops.delete(bm, geom=remove, context="VERTS")
bm.to_mesh(mesh)
bm.free()
mesh.update()
before = mesh_stats(cage)

for obj in bpy.context.selected_objects:
    obj.select_set(False)
cage.select_set(True)
bpy.context.view_layer.objects.active = cage
bpy.ops.object.quadriflow_remesh(
    use_mesh_symmetry=True,
    use_preserve_sharp=False,
    use_preserve_boundary=True,
    preserve_attributes=False,
    smooth_normals=True,
    mode="FACES",
    target_faces=TARGET_FACES,
    seed=7,
)
cage.name = "AevryndFemaleHeadRetopoCage_R427"
cage.data.name = "AevryndFemaleHeadRetopoCage_R427Geometry"
after = mesh_stats(cage)
if source_body.data.materials:
    cage.data.materials.clear()
    cage.data.materials.append(source_body.data.materials[0])
for polygon in cage.data.polygons:
    polygon.use_smooth = True

source_body.hide_render = True
hide_large_hair()
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Base Contrast"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
scene.camera = camera
views = (
    ("front", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
    ("three-quarter", (0.44, -0.63, 1.62), (0.0, -0.02, 1.595), 88),
    ("profile", (0.72, -0.20, 1.60), (0.0, -0.02, 1.595), 88),
)
for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.filepath = str(RENDER_DIR / f"r427-{name}.png")
    bpy.ops.render.render(write_still=True)

scene["aevrynd_head_retopology_study"] = "v249r427"
scene["aevrynd_release_state"] = "RETOPOLOGY_CAGE_VISUAL_AND_TOPOLOGY_REVIEW_PENDING"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "renderDirectory": str(RENDER_DIR),
    "neckCutWorldZ": NECK_CUT_Z, "targetFaces": TARGET_FACES,
    "beforeQuadriflow": before, "afterQuadriflow": after,
    "derivedOnlyFromOwnedCC0Mainline": True,
    "rigTransferred": False, "shapeKeysCreated": False, "websitePromotionApproved": False,
    "status": "RETOPOLOGY_CAGE_VISUAL_AND_TOPOLOGY_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R427_HEAD_RETOPO_CAGE=" + json.dumps(report, sort_keys=True))
