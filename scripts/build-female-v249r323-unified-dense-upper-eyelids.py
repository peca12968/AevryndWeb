import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-collision-safe-optical-stack-r318.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-unified-dense-upper-eyelids-r323.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-unified-dense-upper-eyelids-r323.build-report.json"
AUDIT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-unified-dense-upper-eyelids-r323.collision-audit.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r323-unified-dense-upper-eyelids"
BODY = "AevryndFemaleBody_CC0_R249"
EYES = {"L": (0.034528, 1.607765, 1.0), "R": (-0.034443, 1.607765, -1.0)}
SOURCE_APERTURE = 0.0027
APERTURE = 0.0022
SCLERA_RECESS = 0.0003
FRONT_OPTICAL_ADVANCE = 0.0009
SCLERA_CLEARANCE = 0.00012
FRAMES = (1, 20)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def lid_height(side, x, aperture):
    cx, cz, anatomical_sign = EYES[side]
    u = max(-1.0, min(1.0, (x - cx) / 0.01035))
    edge = math.sqrt(max(0.0, 1.0 - u * u))
    return cz + aperture * edge - 0.00032 * anatomical_sign * u * edge


def world_bvh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def apply_multires(body):
    modifier = next((item for item in body.modifiers if item.type == "MULTIRES"), None)
    if modifier is None:
        raise RuntimeError("Body Multires modifier is missing")
    before = len(body.data.vertices)
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    body.select_set(False)
    return {"beforeVertices": before, "afterVertices": len(body.data.vertices), "appliedModifier": modifier.name}


def sculpt_upper_lids(body, sclera_trees):
    inverse = body.matrix_world.inverted()
    moved = {"L": 0, "R": 0}
    maximum_delta = 0.0
    for vertex in body.data.vertices:
        world = body.matrix_world @ vertex.co
        side = "L" if world.x >= 0 else "R"
        cx, cz, _ = EYES[side]
        u = (world.x - cx) / 0.01035
        if abs(u) >= 1.04:
            continue
        edge = math.sqrt(max(0.0, 1.0 - min(1.0, u * u)))
        target = lid_height(side, world.x, APERTURE)
        if world.z <= target or world.z >= cz + 0.0125:
            continue
        nearest = sclera_trees[side].find_nearest(world, 0.012)
        if nearest is None or nearest[0] is None or nearest[3] is None:
            continue
        location, normal, _index, distance = nearest
        if distance > 0.006:
            continue
        proximity = max(0.0, min(1.0, (0.006 - distance) / 0.0055))
        vertical = max(0.0, min(1.0, (cz + 0.0105 - world.z) / 0.009))
        weight = (proximity ** 1.35) * (vertical ** 0.8) * (edge ** 0.45)
        if weight < 0.02:
            continue
        before = world.copy()
        world.z += (target - world.z) * weight
        hit = sclera_trees[side].find_nearest(world, 0.003)
        if hit is not None and hit[0] is not None and hit[1] is not None:
            location, normal, _index, _distance = hit
            normal = normal.normalized()
            signed = (world - location).dot(normal)
            if signed < SCLERA_CLEARANCE:
                world = location + normal * SCLERA_CLEARANCE
        vertex.co = inverse @ world
        moved[side] += 1
        maximum_delta = max(maximum_delta, (world - before).length)
    body.data.update()
    return {"movedVertices": moved, "maximumDisplacementM": maximum_delta}


def shift_attached_curves():
    moved = {}
    for side in EYES:
        for name in (f"AevryndEye_{side}_UpperLidMargin_R258", f"AevryndFemaleUpperLashes_{side}_R256"):
            obj = bpy.data.objects.get(name)
            if obj is None or obj.type != "CURVE":
                continue
            obj.data = obj.data.copy()
            count = 0
            for spline in obj.data.splines:
                for point in spline.points:
                    point.co.z += lid_height(side, point.co.x, APERTURE) - lid_height(side, point.co.x, SOURCE_APERTURE)
                    count += 1
            obj["aevrynd_revision"] = "v249r323"
            moved[name] = count
    return moved


def overlap_count(a, b, depsgraph):
    return len(world_bvh(a, depsgraph).overlap(world_bvh(b, depsgraph)))


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
body = bpy.data.objects[BODY]
sclera_trees = {side: world_bvh(bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"], depsgraph) for side in EYES}

removed_overlays = []
for side in EYES:
    overlay = bpy.data.objects.get(f"AevryndEye_{side}_UpperLidSurface_R308")
    if overlay:
        removed_overlays.append(overlay.name)
        bpy.data.objects.remove(overlay, do_unlink=True)

multires = apply_multires(body)
sculpt = sculpt_upper_lids(body, sclera_trees)
body["aevrynd_revision"] = "v249r323"
body["aevrynd_unified_dense_upper_lid"] = True
body["aevrynd_upper_lid_aperture_m"] = APERTURE
curve_moves = shift_attached_curves()

eye_offsets = {}
for side in EYES:
    eye_offsets[side] = {}
    for part in ("Sclera_R249", "Cornea_R252", "Limbal_R253", "Iris_R253", "Pupil_R253"):
        obj = bpy.data.objects[f"AevryndEye_{side}_{part}"]
        matrix = obj.matrix_world.copy()
        offset = SCLERA_RECESS if part == "Sclera_R249" else -FRONT_OPTICAL_ADVANCE
        matrix.translation.y += offset
        obj.matrix_world = matrix
        obj["aevrynd_revision"] = "v249r323"
        obj["aevrynd_depth_offset_m"] = offset
        eye_offsets[side][part] = offset

audit = {"frames": {}, "violations": []}
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    rows = {}
    for side in EYES:
        objects = {part: bpy.data.objects[f"AevryndEye_{side}_{part}"] for part in ("Sclera_R249", "Cornea_R252", "Limbal_R253", "Iris_R253", "Pupil_R253")}
        body_rows = {part: overlap_count(body, obj, depsgraph) for part, obj in objects.items()}
        internal = {
            "corneaVsLimbal": overlap_count(objects["Cornea_R252"], objects["Limbal_R253"], depsgraph),
            "corneaVsIris": overlap_count(objects["Cornea_R252"], objects["Iris_R253"], depsgraph),
            "corneaVsPupil": overlap_count(objects["Cornea_R252"], objects["Pupil_R253"], depsgraph),
            "irisVsPupil": overlap_count(objects["Iris_R253"], objects["Pupil_R253"], depsgraph),
        }
        rows[side] = {"body": body_rows, "internal": internal}
        for group, values in rows[side].items():
            for pair, count in values.items():
                if count:
                    audit["violations"].append({"frame": frame, "side": side, "group": group, "pair": pair, "triangleOverlaps": count})
    audit["frames"][str(frame)] = rows
audit["status"] = "PASS" if not audit["violations"] else "FAIL"
AUDIT.write_text(json.dumps(audit, indent=2), encoding="utf-8")

scene["aevrynd_mainline_revision"] = "v249r323-unified-dense-upper-eyelids"
scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_PENDING" if audit["status"] == "PASS" else "COLLISION_FAIL"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    (1, "front-f01", (0.0, -0.90, 1.59), (0.0, 0.0, 1.56), 82),
    (20, "front-f20", (0.0, -0.90, 1.59), (0.0, 0.0, 1.56), 82),
    (1, "face-close-f01", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
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
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
unweighted = sum(1 for vertex in body.data.vertices if not vertex.groups)
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "removedTransitionalOverlays": removed_overlays,
    "apertureM": APERTURE, "scleraRecessM": SCLERA_RECESS, "frontOpticalAdvanceM": FRONT_OPTICAL_ADVANCE,
    "multires": multires, "sculpt": sculpt, "curveMoves": curve_moves, "eyeOffsets": eye_offsets,
    "bodyVertexGroups": len(body.vertex_groups), "unweightedBodyVertices": unweighted,
    "remainingBodyModifiers": [{"name": item.name, "type": item.type} for item in body.modifiers],
    "collisionAudit": str(AUDIT), "collisionStatus": audit["status"], "renderDirectory": str(RENDER_DIR),
    "ownedAssetOnly": True, "status": "TECHNICAL_PASS_VISUAL_REVIEW_PENDING" if audit["status"] == "PASS" else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R323_UNIFIED_DENSE_UPPER_EYELIDS=" + json.dumps(report, sort_keys=True))
if audit["status"] != "PASS" or unweighted:
    raise SystemExit(2)
