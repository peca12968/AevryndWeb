import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-pruned-dynamic-outliers-r298.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-surface-baby-hairs-r299.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-surface-baby-hairs-r299.build-report.json"
AUDIT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-surface-baby-hairs-r299.audit.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r299-surface-baby-hairs"
BODY = "AevryndFemaleBody_CC0_R249"
RIG = "AevryndFemaleRig"
HAIRLINE = "AevryndFemaleHairlineMicroFibers_R299"
OLD_HAIRLINE = "AevryndFemaleHairlineTransitionCards_R285"
MATERIAL = "Aevrynd_PrincipledHair_CC0_R264"
POINTS = 12
PER_SIDE = 42
CLEARANCE = 0.0018
FRAMES = (1, 33, 61)


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def evaluated_body_tree(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def surface_point(tree, x, z):
    hit = tree.ray_cast(Vector((x, -0.30, z)), Vector((0.0, 1.0, 0.0)), 0.50)
    if hit[0] is None or hit[1] is None:
        nearest = tree.find_nearest(Vector((x, -0.11, z)), 0.12)
        if nearest is None or nearest[0] is None or nearest[1] is None:
            raise RuntimeError(f"hairline surface sample failed: x={x}, z={z}")
        return nearest[0], nearest[1].normalized()
    return hit[0], hit[1].normalized()


def build_hairline(body):
    tree = evaluated_body_tree(body)
    rng = random.Random(299084)
    strands = []
    metadata = []
    for side in (-1.0, 1.0):
        for index in range(PER_SIDE):
            fraction = (index + 0.55) / PER_SIDE
            x0 = side * (0.0045 + fraction * 0.077) + rng.uniform(-0.0013, 0.0013)
            edge_z = 1.6865 - 0.047 * (abs(x0) / 0.088) ** 1.52 + rng.uniform(-0.0018, 0.0018)
            # Center hairs stay very short; temple hairs carry a few longer,
            # irregular wisps instead of a uniform painted fringe.
            length = rng.uniform(0.008, 0.016) + 0.010 * smoothstep((abs(x0) - 0.030) / 0.050)
            if index % 9 == 0:
                length *= 1.28
            outward = side * rng.uniform(0.0015, 0.0065)
            phase = rng.uniform(-math.pi, math.pi)
            strand = []
            for point_index in range(POINTS):
                t = point_index / (POINTS - 1)
                z = edge_z - length * t
                x = x0 + outward * t + side * rng.uniform(0.0002, 0.00065) * math.sin(math.pi * t + phase)
                position, normal = surface_point(tree, x, z)
                # Slightly increase clearance at the free end so the visible
                # radius does not visually sink into forehead skin.
                strand.append(position + normal * (CLEARANCE + 0.00035 * smoothstep(t)))
            strands.append(strand)
            metadata.append({"side": "L" if side < 0 else "R", "rootX": x0, "edgeZ": edge_z, "lengthM": length})
    data = bpy.data.hair_curves.new("AevryndFemaleHairlineMicroFibersTopology_R299")
    data.add_curves([POINTS] * len(strands))
    data.points.foreach_set("position", [coordinate for strand in strands for point in strand for coordinate in point])
    radius = data.attributes.new("radius", "FLOAT", "POINT")
    values = []
    for _strand in strands:
        for point_index in range(POINTS):
            t = point_index / (POINTS - 1)
            values.append(0.000026 * (1.0 - smoothstep((t - 0.38) / 0.62)))
    radius.data.foreach_set("value", values)
    data.materials.append(bpy.data.materials[MATERIAL])
    obj = bpy.data.objects.new(HAIRLINE, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = bpy.data.objects[RIG]
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = Matrix.Identity(4)
    obj["aevrynd_layer"] = "hair.hairline_microfibers.head_bound"
    obj["aevrynd_revision"] = "v249r299"
    obj["aevrynd_clearance_m"] = CLEARANCE
    obj["aevrynd_ownership"] = "procedurally authored in-project from current head surface"
    return obj, metadata


def audit(scene, body, layer):
    frames = {}
    failures = []
    for frame in FRAMES:
        scene.frame_set(frame)
        tree = evaluated_body_tree(body)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        evaluated = layer.evaluated_get(depsgraph)
        values = []
        for point in evaluated.data.points:
            world = evaluated.matrix_world @ point.position
            hit = tree.find_nearest(world, 0.08)
            if hit is not None and hit[1] is not None:
                values.append((world - hit[0]).dot(hit[1].normalized()))
        penetrating = sum(value < -1e-7 for value in values)
        frames[str(frame)] = {"samples": len(values), "minimumSignedM": min(values), "maximumSignedM": max(values), "penetratingPoints": penetrating}
        if penetrating:
            failures.append({"frame": frame, "penetratingPoints": penetrating})
    return frames, failures


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, frame, name, location):
    scene.frame_set(frame)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.location = location
    camera.data.lens = 82
    look_at(camera, (0.0, 0.0, 1.56))
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
hairline, metadata = build_hairline(body)
bpy.data.objects[OLD_HAIRLINE].hide_render = True
frames, failures = audit(scene, body, hairline)
scene["aevrynd_mainline_revision"] = "v249r299-surface-baby-hairs"
scene["aevrynd_hair_layers"] = "scalp_underlayer|authored_primary_guides|authored_secondary_fibers|authored_hairline_microfibers|authored_flyaways|runtime_card_proxy.hidden"
scene["aevrynd_release_state"] = "HAIRLINE_VISUAL_REVIEW_PENDING" if not failures else "HAIRLINE_COLLISION_FAIL"
AUDIT.write_text(json.dumps({"model": str(OUTPUT), "object": HAIRLINE, "frames": frames, "failures": failures, "status": "PASS" if not failures else "FAIL"}, indent=2), encoding="utf-8")
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
for frame, name, location in ((1, "front-f01", (0.0, -0.90, 1.59)), (33, "front-f33", (0.0, -0.90, 1.59)), (1, "left-f01", (-0.72, -0.55, 1.59)), (1, "right-f01", (0.72, -0.55, 1.59)), (1, "back-f01", (0.0, 0.90, 1.59)), (33, "back-f33", (0.0, 0.90, 1.59))):
    render(camera, frame, name, location)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "hairlineObject": HAIRLINE,
    "curves": len(metadata), "pointsPerCurve": POINTS, "totalPoints": len(hairline.data.points),
    "clearanceM": CLEARANCE, "oldRuntimeHairlinePreservedHidden": OLD_HAIRLINE,
    "audit": str(AUDIT), "auditStatus": "PASS" if not failures else "FAIL",
    "failures": failures, "metadata": metadata, "ownedAssetOnly": True,
    "renderDirectory": str(RENDER_DIR), "status": "VISUAL_REVIEW_PENDING" if not failures else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R299_SURFACE_BABY_HAIRS=" + json.dumps({key: value for key, value in report.items() if key != "metadata"}, sort_keys=True))
if failures:
    raise SystemExit(2)
