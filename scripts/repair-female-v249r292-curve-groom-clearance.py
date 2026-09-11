import json
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-authored-curve-groom-r291.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-curve-clearance-r292.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-curve-clearance-r292.build-report.json"
AUDIT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-curve-clearance-r292.audit.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r292-curve-clearance"
BODY = "AevryndFemaleBody_CC0_R249"
LAYERS = ("AevryndFemalePrimaryClumps_R264", "AevryndFemaleSecondaryFill_R264", "AevryndFemaleFlyaways_R264")
TARGET = 0.00030
FRAMES = (1, 33, 61)


def body_tree(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def repair(scene, body, objects, passes=3):
    history = []
    for pass_index in range(passes):
        for frame in FRAMES:
            scene.frame_set(frame)
            tree = body_tree(body)
            for obj in objects:
                matrix = obj.matrix_world.copy()
                inverse = matrix.inverted()
                moved = 0
                maximum = 0.0
                for point in obj.data.points:
                    world = matrix @ point.position
                    hit = tree.find_nearest(world, 0.20)
                    if hit is None or hit[1] is None:
                        continue
                    normal = hit[1].normalized()
                    signed = (world - hit[0]).dot(normal)
                    if signed < TARGET:
                        corrected = hit[0] + normal * TARGET
                        delta = (corrected - world).length
                        point.position = inverse @ corrected
                        moved += 1
                        maximum = max(maximum, delta)
                obj.data.update_tag()
                history.append({"pass": pass_index + 1, "frame": frame, "object": obj.name, "moved": moved, "maximumCorrectionM": maximum})
    return history


def audit(scene, body, objects):
    frames = {}
    failures = []
    for frame in FRAMES:
        scene.frame_set(frame)
        tree = body_tree(body)
        current = {}
        for obj in objects:
            matrix = obj.matrix_world.copy()
            values = []
            for point in obj.data.points:
                world = matrix @ point.position
                hit = tree.find_nearest(world, 0.20)
                if hit is not None and hit[1] is not None:
                    values.append((world - hit[0]).dot(hit[1].normalized()))
            penetrating = sum(value < -1e-7 for value in values)
            current[obj.name] = {"samples": len(values), "minimumSignedM": min(values), "penetratingVertices": penetrating}
            if penetrating:
                failures.append({"frame": frame, "object": obj.name, "penetratingVertices": penetrating})
        frames[str(frame)] = current
    return frames, failures


def look_at(obj, target):
    from mathutils import Vector
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, frame, name, location):
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.location = location
    camera.data.lens = 82
    look_at(camera, (0.0, 0.0, 1.56))
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
objects = [bpy.data.objects[name] for name in LAYERS]
history = repair(scene, body, objects)
frames, failures = audit(scene, body, objects)
for obj in objects:
    obj["aevrynd_revision"] = "v249r292"
    obj["aevrynd_minimum_clearance_m"] = TARGET
scene["aevrynd_mainline_revision"] = "v249r292-curve-clearance"
scene["aevrynd_release_state"] = "CURVE_GROOM_VISUAL_REVIEW_PENDING" if not failures else "CURVE_GROOM_CLEARANCE_FAIL"
AUDIT.write_text(json.dumps({
    "model": str(OUTPUT), "targetClearanceM": TARGET, "frames": frames,
    "failures": failures, "status": "PASS" if not failures else "FAIL",
}, indent=2), encoding="utf-8")
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
for frame, name, location in (
    (1, "front-f01", (0.0, -0.90, 1.59)), (33, "front-f33", (0.0, -0.90, 1.59)),
    (1, "left-f01", (-0.72, -0.55, 1.59)), (1, "right-f01", (0.72, -0.55, 1.59)),
    (1, "back-f01", (0.0, 0.90, 1.59)), (33, "back-f33", (0.0, 0.90, 1.59)),
):
    render(camera, frame, name, location)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "targetClearanceM": TARGET,
    "repairHistory": history, "audit": str(AUDIT), "auditStatus": "PASS" if not failures else "FAIL",
    "failures": failures, "topologyChanged": False, "ownedAssetOnly": True,
    "renderDirectory": str(RENDER_DIR), "status": "VISUAL_REVIEW_PENDING" if not failures else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R292_CURVE_CLEARANCE=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
