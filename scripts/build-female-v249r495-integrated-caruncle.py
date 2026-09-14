import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-clipped-optical-fronts-r493.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-integrated-caruncle-r495.blend"
REPORT = ASSETS / "female-v249-mainline-integrated-caruncle-r495.build-report.json"
AUDIT = ASSETS / "female-v249-mainline-integrated-caruncle-r495.local-collision-audit.json"
REVIEW_DIR = ASSETS / "reviews/v249r495-integrated-caruncle"
BODY = "AevryndFemaleBodyBaseV118"
SHAPE = {"towardEyeScale": 3.50, "medialScale": 0.65, "verticalScale": 0.72}
MATERIAL = {
    "baseColor": (0.120, 0.034, 0.027, 1.0),
    "roughness": 0.56,
    "specularIorLevel": 0.16,
    "subsurfaceWeight": 0.025,
    "coatWeight": 0.02,
}


def tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, frame, name, location, target, lens, size):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(REVIEW_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
for side in ("L", "R"):
    obj = bpy.data.objects[f"Eye_{side}_Caruncle"]
    obj.data = obj.data.copy()
    points = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
    center = sum(points, Vector()) / len(points)
    inverse = obj.matrix_world.inverted()
    eye_sign = 1.0 if side == "L" else -1.0
    for vertex, source in zip(obj.data.vertices, points):
        point = source.copy()
        anatomical = (point.x - center.x) * eye_sign
        point.x = center.x + (point.x - center.x) * (SHAPE["towardEyeScale"] if anatomical >= 0.0 else SHAPE["medialScale"])
        point.z = center.z + (point.z - center.z) * SHAPE["verticalScale"]
        vertex.co = inverse @ point
    obj.data.update()
    obj["aevrynd_revision"] = "v249r495-integrated-caruncle"
    obj["aevrynd_shape"] = "asymmetric-medial-canthus-wedge"

material = bpy.data.materials["Aevrynd_Caruncle_v37"]
shader = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
shader.inputs["Base Color"].default_value = MATERIAL["baseColor"]
shader.inputs["Roughness"].default_value = MATERIAL["roughness"]
shader.inputs["Specular IOR Level"].default_value = MATERIAL["specularIorLevel"]
shader.inputs["Subsurface Weight"].default_value = MATERIAL["subsurfaceWeight"]
shader.inputs["Coat Weight"].default_value = MATERIAL["coatWeight"]
material["aevrynd_revision"] = "v249r495-warm-muted-mucosa"
material["aevrynd_ownership"] = "procedural-in-project"

collision = {"frames": {}, "violations": []}
for frame in (1, 20):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = tree(bpy.data.objects[BODY], depsgraph)
    collision["frames"][str(frame)] = {}
    for side in ("L", "R"):
        caruncle_tree = tree(bpy.data.objects[f"Eye_{side}_Caruncle"], depsgraph)
        counts = {
            "body": len(body_tree.overlap(caruncle_tree)),
            "sclera": len(tree(bpy.data.objects[f"Eye_{side}_Sclera"], depsgraph).overlap(caruncle_tree)),
            "cornea": len(tree(bpy.data.objects[f"Eye_{side}_Cornea"], depsgraph).overlap(caruncle_tree)),
            "tearMeniscus": len(tree(bpy.data.objects[f"Eye_{side}_TearMeniscus"], depsgraph).overlap(caruncle_tree)),
        }
        collision["frames"][str(frame)][side] = counts
        for layer, count in counts.items():
            if count:
                collision["violations"].append({"frame": frame, "side": side, "layer": layer, "triangleOverlaps": count})
collision["status"] = "PASS" if not collision["violations"] else "FAIL"
AUDIT.write_text(json.dumps(collision, indent=2), encoding="utf-8")

scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.image_settings.file_format = "PNG"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
for values in (
    (1, "01-eye-close-f01", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700)),
    (1, "02-face-front-f01", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000)),
    (1, "03-three-quarter-f01", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84, (1000, 1000)),
    (20, "04-eye-close-f20", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700)),
):
    render(scene, camera, *values)

scene.frame_set(1)
scene["aevrynd_mainline_revision"] = "v249r495-integrated-caruncle"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_PENDING" if collision["status"] == "PASS" else "COLLISION_FAIL"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "shape": SHAPE,
    "material": {key: list(value) if key == "baseColor" else value for key, value in MATERIAL.items()},
    "collisionAudit": str(AUDIT),
    "collisionStatus": collision["status"],
    "reviewDirectory": str(REVIEW_DIR),
    "ownedAssetOnly": True,
    "status": scene["aevrynd_release_state"],
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R495_INTEGRATED_CARUNCLE=" + json.dumps(report, sort_keys=True))
if collision["status"] != "PASS":
    raise SystemExit(2)
