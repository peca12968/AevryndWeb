import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-continuous-upper-lower-eyelids-r334.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-natural-sclera-r337.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-natural-sclera-r337.build-report.json"
AUDIT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-natural-sclera-r337.collision-audit.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r337-natural-sclera"
BODY = "AevryndFemaleBody_CC0_R249"
LOW = (0.18, 0.14, 0.13, 1.0)
HIGH = (0.42, 0.36, 0.32, 1.0)


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
for side in ("L", "R"):
    material = bpy.data.materials[f"Aevrynd_IntegratedEye_{side}_R328"]
    ramps = [node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeValToRGB"]
    sclera = next(node for node in ramps if node.color_ramp.elements[0].color[0] > 0.05)
    sclera.color_ramp.elements[0].color = LOW
    sclera.color_ramp.elements[1].color = HIGH
    shader = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    shader.inputs["Coat Weight"].default_value = 0.10
    shader.inputs["Coat Roughness"].default_value = 0.20
    material["aevrynd_revision"] = "v249r337-natural-sclera"
    material["aevrynd_sclera_tone"] = "warm-low-clipping"

body = bpy.data.objects[BODY]
collision = {"frames": {}, "violations": []}
for frame in (1, 20):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = world_bvh(body, depsgraph)
    collision["frames"][str(frame)] = {}
    for side in ("L", "R"):
        eye = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
        count = len(body_tree.overlap(world_bvh(eye, depsgraph)))
        collision["frames"][str(frame)][side] = {"bodyVsIntegratedEye": count}
        if count:
            collision["violations"].append({"frame": frame, "side": side, "triangleOverlaps": count})
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
scene["aevrynd_mainline_revision"] = "v249r337-natural-sclera"
scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_PENDING" if collision["status"] == "PASS" else "COLLISION_FAIL"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "renderDirectory": str(RENDER_DIR),
    "scleraRamp": {"low": list(LOW), "high": list(HIGH)},
    "coatWeight": 0.10, "coatRoughness": 0.20, "fixedExposureEV": 0.0,
    "r334NearClipPercentOfBrightEyeBand": 40.68529607451763,
    "r337NearClipPercentOfBrightEyeBand": 10.798533630857508,
    "collisionAudit": str(AUDIT), "collisionStatus": collision["status"],
    "ownedAssetOnly": True,
    "status": "TECHNICAL_PASS_VISUAL_REVIEW_PENDING" if collision["status"] == "PASS" else "COLLISION_FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R337_NATURAL_SCLERA=" + json.dumps(report, sort_keys=True))
if collision["status"] != "PASS":
    raise SystemExit(2)
