import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-integrated-caruncle-r340.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-canthus-fitted-wedge-r345.build-report.json"
AUDIT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-canthus-fitted-wedge-r345.collision-audit.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r345-canthus-fitted-wedge"
BODY = "AevryndFemaleBody_CC0_R249"
TAPER = 0.25
ADDITIONAL_MEDIAL_SHIFT = 0.00250


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def world_bvh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph); mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear(); return tree


def wedge(side, obj):
    sign = 1.0 if side == "L" else -1.0
    maximum = 0.0
    obj.data = obj.data.copy()
    for vertex in obj.data.vertices:
        source = vertex.co.copy()
        u = max(-1.0, min(1.0, sign * source.x / 0.00058))
        cross = 1.0 - TAPER * (u + 1.0) * 0.5
        vertex.co.y *= cross; vertex.co.z *= cross
        vertex.co.x -= sign * TAPER * 0.00008 * (1.0 - u * u)
        maximum = max(maximum, (vertex.co - source).length)
    obj.data.update()
    obj.matrix_world.translation.x += -ADDITIONAL_MEDIAL_SHIFT if side == "L" else ADDITIONAL_MEDIAL_SHIFT
    obj["aevrynd_revision"] = "v249r345-canthus-fitted-wedge"
    obj["aevrynd_lateral_taper"] = TAPER
    obj["aevrynd_additional_medial_shift_m"] = ADDITIONAL_MEDIAL_SHIFT
    return maximum


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene; scene.frame_set(1)
displacement = {}
for side in ("L", "R"):
    displacement[side] = wedge(side, bpy.data.objects[f"AevryndEye_{side}_Caruncle_R258"])

collision = {"frames": {}, "violations": []}
for frame in (1, 20):
    scene.frame_set(frame); bpy.context.view_layer.update(); depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = world_bvh(bpy.data.objects[BODY], depsgraph); collision["frames"][str(frame)] = {}
    for side in ("L", "R"):
        eye_tree = world_bvh(bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"], depsgraph)
        caruncle_tree = world_bvh(bpy.data.objects[f"AevryndEye_{side}_Caruncle_R258"], depsgraph)
        counts = {"bodyVsIntegratedEye": len(body_tree.overlap(eye_tree)), "bodyVsCaruncle": len(body_tree.overlap(caruncle_tree)), "integratedEyeVsCaruncle": len(eye_tree.overlap(caruncle_tree))}
        collision["frames"][str(frame)][side] = counts
        for pair, count in counts.items():
            if count: collision["violations"].append({"frame": frame, "side": side, "pair": pair, "triangleOverlaps": count})
collision["status"] = "PASS" if not collision["violations"] else "FAIL"
AUDIT.write_text(json.dumps(collision, indent=2), encoding="utf-8")

scene.render.engine = "BLENDER_EEVEE"; scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"; scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True); camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    (1, "front-f01", (0.0, -0.90, 1.59), (0.0, 0.0, 1.56), 82), (20, "front-f20", (0.0, -0.90, 1.59), (0.0, 0.0, 1.56), 82),
    (1, "face-close-f01", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92), (1, "eyes-close-f01", (0.0, -0.46, 1.615), (0.0, -0.035, 1.610), 105),
    (1, "three-quarter-f01", (0.45, -0.62, 1.62), (0.0, -0.02, 1.605), 90), (1, "left-f01", (-0.72, -0.55, 1.59), (0.0, 0.0, 1.56), 82),
    (1, "right-f01", (0.72, -0.55, 1.59), (0.0, 0.0, 1.56), 82), (1, "back-f01", (0.0, 0.90, 1.59), (0.0, 0.0, 1.56), 82),
)
for frame, name, location, target, lens in views:
    scene.frame_set(frame); bpy.context.view_layer.update(); camera.location = location; camera.data.lens = lens; look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 1000; scene.render.filepath = str(RENDER_DIR / f"{name}.png"); bpy.ops.render.render(write_still=True)

scene.frame_set(1); scene["aevrynd_mainline_revision"] = "v249r345-canthus-fitted-wedge"
scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_PENDING" if collision["status"] == "PASS" else "COLLISION_FAIL"
bpy.context.preferences.filepaths.save_version = 0; bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {"source": str(SOURCE), "output": str(OUTPUT), "renderDirectory": str(RENDER_DIR), "lateralTaper": TAPER, "maximumLocalDisplacementM": displacement, "additionalMedialShiftM": ADDITIONAL_MEDIAL_SHIFT, "totalMedialShiftFromR337M": 0.00285, "collisionAudit": str(AUDIT), "collisionStatus": collision["status"], "ownedAssetOnly": True, "status": "TECHNICAL_PASS_VISUAL_REVIEW_PENDING" if collision["status"] == "PASS" else "COLLISION_FAIL"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R345_CANTHUS_FITTED_WEDGE=" + json.dumps(report, sort_keys=True))
if collision["status"] != "PASS": raise SystemExit(2)
