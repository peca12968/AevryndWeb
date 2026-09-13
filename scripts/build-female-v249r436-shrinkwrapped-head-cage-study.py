import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-head-cage-scaffold-r435.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-shrinkwrapped-head-cage-r436-study.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-shrinkwrapped-head-cage-r436.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r436-shrinkwrapped-head-cage-study"
BODY = "AevryndFemaleBody_CC0_R249"
CAGE = "AevryndFemaleScaledQuadriflowHeadCage_R435"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def mesh_stats(obj):
    polygons = list(obj.data.polygons)
    quads = sum(1 for polygon in polygons if len(polygon.vertices) == 4)
    return {
        "vertices": len(obj.data.vertices),
        "edges": len(obj.data.edges),
        "polygons": len(polygons),
        "quads": quads,
        "quadRatio": quads / max(1, len(polygons)),
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
source_body = bpy.data.objects[BODY]
cage = bpy.data.objects[CAGE]
before_positions = [vertex.co.copy() for vertex in cage.data.vertices]
for obj in bpy.context.selected_objects:
    obj.select_set(False)
cage.select_set(True)
bpy.context.view_layer.objects.active = cage
modifier = cage.modifiers.new("Aevrynd R436 Surface Reprojection", "SHRINKWRAP")
modifier.target = source_body
modifier.wrap_method = "NEAREST_SURFACEPOINT"
modifier.wrap_mode = "ON_SURFACE"
modifier.offset = 0.0
bpy.ops.object.modifier_apply(modifier=modifier.name)
after_positions = [vertex.co.copy() for vertex in cage.data.vertices]
displacements = [(after - before).length for before, after in zip(before_positions, after_positions)]
cage.name = "AevryndFemaleShrinkwrappedHeadCage_R436"
cage.data.name = "AevryndFemaleShrinkwrappedHeadCage_R436Geometry"
cage["aevrynd_layer"] = "body.head.retopology_cage.shrinkwrapped.study"
cage["aevrynd_revision"] = "v249r436-study"
cage["aevrynd_source"] = SOURCE.name

source_body.hide_render = True
for obj in bpy.data.objects:
    if obj == cage or obj == source_body:
        continue
    name = obj.name.lower()
    if any(token in name for token in ("eye", "caruncle", "tear", "brow", "lash")):
        obj.hide_render = False
    elif obj.type in {"MESH", "CURVES", "CURVE"}:
        obj.hide_render = True

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
    scene.render.filepath = str(RENDER_DIR / f"r436-{name}.png")
    bpy.ops.render.render(write_still=True)

scene["aevrynd_head_retopology_study"] = "v249r436"
scene["aevrynd_release_state"] = "SURFACE_REPROJECTION_VISUAL_REVIEW_PENDING"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "renderDirectory": str(RENDER_DIR),
    "topology": mesh_stats(cage),
    "surfaceReprojection": {
        "method": "NEAREST_SURFACEPOINT",
        "meanDisplacementMeters": sum(displacements) / max(1, len(displacements)),
        "maximumDisplacementMeters": max(displacements) if displacements else 0.0,
    },
    "derivedOnlyFromOwnedCC0Mainline": True,
    "rigTransferred": False,
    "shapeKeysCreated": False,
    "websitePromotionApproved": False,
    "status": "SURFACE_REPROJECTION_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R436_SHRINKWRAPPED_HEAD_CAGE=" + json.dumps(report, sort_keys=True))
