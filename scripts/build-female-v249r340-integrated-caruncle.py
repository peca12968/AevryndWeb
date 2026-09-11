import json
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-natural-sclera-r337.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-integrated-caruncle-r340.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-integrated-caruncle-r340.build-report.json"
AUDIT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-integrated-caruncle-r340.collision-audit.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r340-integrated-caruncle"
BODY = "AevryndFemaleBody_CC0_R249"
SCALE = (1.6, 1.15, 1.20)
MEDIAL_SHIFT = 0.00035
TISSUE_COLOR = (0.18, 0.070, 0.055, 1.0)


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


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
for side in ("L", "R"):
    obj = bpy.data.objects[f"AevryndEye_{side}_Caruncle_R258"]
    obj.matrix_world = obj.matrix_world.copy() @ Matrix.Diagonal((*SCALE, 1.0))
    obj.matrix_world.translation.x += -MEDIAL_SHIFT if side == "L" else MEDIAL_SHIFT
    obj["aevrynd_revision"] = "v249r340-integrated-caruncle"
    obj["aevrynd_layer"] = f"eye.{side.lower()}.caruncle.head_bound"

material = bpy.data.materials["Aevrynd_Caruncle_R258"]
shader = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
shader.inputs["Base Color"].default_value = TISSUE_COLOR
shader.inputs["Roughness"].default_value = 0.42
shader.inputs["Subsurface Weight"].default_value = 0.025
material["aevrynd_revision"] = "v249r340-muted-tissue"
material["aevrynd_ownership"] = "procedural in-project"

collision = {"frames": {}, "violations": []}
for frame in (1, 20):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = world_bvh(bpy.data.objects[BODY], depsgraph)
    collision["frames"][str(frame)] = {}
    for side in ("L", "R"):
        eye = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
        caruncle = bpy.data.objects[f"AevryndEye_{side}_Caruncle_R258"]
        eye_tree = world_bvh(eye, depsgraph)
        caruncle_tree = world_bvh(caruncle, depsgraph)
        counts = {
            "bodyVsIntegratedEye": len(body_tree.overlap(eye_tree)),
            "bodyVsCaruncle": len(body_tree.overlap(caruncle_tree)),
            "integratedEyeVsCaruncle": len(eye_tree.overlap(caruncle_tree)),
        }
        collision["frames"][str(frame)][side] = counts
        for pair, count in counts.items():
            if count:
                collision["violations"].append({"frame": frame, "side": side, "pair": pair, "triangleOverlaps": count})
collision["status"] = "PASS" if not collision["violations"] else "FAIL"
AUDIT.write_text(json.dumps(collision, indent=2), encoding="utf-8")

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    (1, "front-f01", (0.0, -0.90, 1.59), (0.0, 0.0, 1.56), 82),
    (20, "front-f20", (0.0, -0.90, 1.59), (0.0, 0.0, 1.56), 82),
    (1, "face-close-f01", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
    (1, "eyes-close-f01", (0.0, -0.46, 1.615), (0.0, -0.035, 1.610), 105),
    (1, "three-quarter-f01", (0.45, -0.62, 1.62), (0.0, -0.02, 1.605), 90),
    (1, "left-f01", (-0.72, -0.55, 1.59), (0.0, 0.0, 1.56), 82),
    (1, "right-f01", (0.72, -0.55, 1.59), (0.0, 0.0, 1.56), 82),
    (1, "back-f01", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
)
for frame, name, location, target, lens in views:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 1000
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)

scene.frame_set(1)
scene["aevrynd_mainline_revision"] = "v249r340-integrated-caruncle"
scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_PENDING" if collision["status"] == "PASS" else "COLLISION_FAIL"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "renderDirectory": str(RENDER_DIR),
    "caruncleScaleXYZ": list(SCALE), "caruncleMedialShiftM": MEDIAL_SHIFT,
    "caruncleWorldWidthM": 0.001855999, "tissueBaseColor": list(TISSUE_COLOR),
    "roughness": 0.42, "subsurfaceWeight": 0.025,
    "collisionAudit": str(AUDIT), "collisionStatus": collision["status"],
    "ownedAssetOnly": True,
    "status": "TECHNICAL_PASS_VISUAL_REVIEW_PENDING" if collision["status"] == "PASS" else "COLLISION_FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R340_INTEGRATED_CARUNCLE=" + json.dumps(report, sort_keys=True))
if collision["status"] != "PASS":
    raise SystemExit(2)
