import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-collision-safe-curve-motion-r294.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-dynamic-curve-envelope-r295.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-dynamic-curve-envelope-r295.build-report.json"
AUDIT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-dynamic-curve-envelope-r295.audit.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r295-dynamic-curve-envelope"
BODY = "AevryndFemaleBody_CC0_R249"
LAYERS = ("AevryndFemalePrimaryClumps_R264", "AevryndFemaleSecondaryFill_R264", "AevryndFemaleFlyaways_R264")
POINTS = 24
FRAMES = (1, 33, 61)
TARGET = 0.0020


def body_tree(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def repair_rest_envelope(scene, body, objects):
    scene.frame_set(1)
    tree = body_tree(body)
    results = {}
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
                maximum = max(maximum, (corrected - world).length)
                point.position = inverse @ corrected
                moved += 1
        obj.data.update_tag()
        results[obj.name] = {"moved": moved, "maximumCorrectionM": maximum}
    return results


def percentile(values, fraction):
    values = sorted(values)
    return values[min(len(values) - 1, int((len(values) - 1) * fraction))]


def run_audit(scene, body, objects):
    snapshots = {}
    collision = {}
    failures = []
    for frame in FRAMES:
        scene.frame_set(frame)
        tree = body_tree(body)
        snapshots[frame] = {}
        collision[str(frame)] = {}
        for obj in objects:
            depsgraph = bpy.context.evaluated_depsgraph_get()
            depsgraph.update()
            evaluated = obj.evaluated_get(depsgraph)
            local = [point.position.copy() for point in evaluated.data.points]
            world = [evaluated.matrix_world @ point for point in local]
            snapshots[frame][obj.name] = local
            signed_values = []
            for point in world:
                hit = tree.find_nearest(point, 0.20)
                if hit is not None and hit[1] is not None:
                    signed_values.append((point - hit[0]).dot(hit[1].normalized()))
            penetrating = sum(value < -1e-7 for value in signed_values)
            collision[str(frame)][obj.name] = {
                "samples": len(signed_values), "minimumSignedM": min(signed_values), "penetratingVertices": penetrating,
            }
            if penetrating:
                failures.append({"frame": frame, "object": obj.name, "penetratingVertices": penetrating})
    motion = {}
    all_peak, all_settle, all_roots = [], [], []
    for obj in objects:
        rest = snapshots[1][obj.name]
        peak = snapshots[33][obj.name]
        settled = snapshots[61][obj.name]
        peak_delta = [(b - a).length for a, b in zip(rest, peak)]
        settle_delta = [(b - a).length for a, b in zip(rest, settled)]
        root_delta = [peak_delta[index] for index in range(0, len(peak_delta), POINTS)]
        all_peak.extend(peak_delta)
        all_settle.extend(settle_delta)
        all_roots.extend(root_delta)
        motion[obj.name] = {
            "peakMeanM": sum(peak_delta) / len(peak_delta), "peakP95M": percentile(peak_delta, 0.95),
            "peakMaximumM": max(peak_delta), "rootMaximumM": max(root_delta), "settleMaximumM": max(settle_delta),
        }
    summary = {
        "peakMeanM": sum(all_peak) / len(all_peak), "peakP95M": percentile(all_peak, 0.95),
        "peakMaximumM": max(all_peak), "rootMaximumM": max(all_roots), "settleMaximumM": max(all_settle),
    }
    if summary["peakP95M"] < 0.0020:
        failures.append({"motion": "peak P95 below 2mm", "valueM": summary["peakP95M"]})
    if summary["rootMaximumM"] > 0.00002:
        failures.append({"motion": "root drift above 0.02mm", "valueM": summary["rootMaximumM"]})
    if summary["settleMaximumM"] > 0.00005:
        failures.append({"motion": "frame 61 not settled", "valueM": summary["settleMaximumM"]})
    return collision, motion, summary, failures


def look_at(obj, target):
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
repair = repair_rest_envelope(scene, body, objects)
collision, motion, summary, failures = run_audit(scene, body, objects)
for obj in objects:
    obj["aevrynd_revision"] = "v249r295"
    obj["aevrynd_dynamic_clearance_envelope_m"] = TARGET
scene["aevrynd_mainline_revision"] = "v249r295-dynamic-curve-envelope"
scene["aevrynd_release_state"] = "DYNAMIC_CURVE_GROOM_VISUAL_REVIEW_PENDING" if not failures else "DYNAMIC_CURVE_GROOM_FAIL"
AUDIT.write_text(json.dumps({
    "model": str(OUTPUT), "targetRestEnvelopeM": TARGET, "frames": list(FRAMES),
    "collision": collision, "motion": motion, "motionSummary": summary,
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
    "source": str(SOURCE), "output": str(OUTPUT), "restEnvelopeM": TARGET,
    "repair": repair, "audit": str(AUDIT), "auditStatus": "PASS" if not failures else "FAIL",
    "motionSummary": summary, "failures": failures, "topologyChanged": False,
    "runtimeCardProxyPreserved": "AevryndFemaleRuntimeHairCards_R276", "ownedAssetOnly": True,
    "renderDirectory": str(RENDER_DIR), "status": "VISUAL_REVIEW_PENDING" if not failures else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R295_DYNAMIC_CURVE_ENVELOPE=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
