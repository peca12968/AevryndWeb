import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-integrated-eye-shader-r328.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-continuous-upper-lower-eyelids-r334.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-continuous-upper-lower-eyelids-r334.build-report.json"
AUDIT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-continuous-upper-lower-eyelids-r334.collision-audit.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r334-continuous-upper-lower-eyelids"
BODY = "AevryndFemaleBody_CC0_R249"
EYES = {"L": (0.034528, 1.607765), "R": (-0.034443, 1.607765)}
SOURCE_APERTURE = 0.00448
APERTURE = 0.0041
SCLERA_RECESS = 0.0002


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def lower_height(side, x, aperture):
    cx, cz = EYES[side]
    u = max(-1.0, min(1.0, (x - cx) / 0.01025))
    return cz - aperture * math.sqrt(max(0.0, 1.0 - u * u))


def world_bvh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def sculpt_lower_lids(body, sclera_trees):
    inverse = body.matrix_world.inverted()
    moved = {"L": 0, "R": 0}
    maximum = 0.0
    for vertex in body.data.vertices:
        world = body.matrix_world @ vertex.co
        side = "L" if world.x >= 0 else "R"
        cx, cz = EYES[side]
        u = (world.x - cx) / 0.01025
        if abs(u) >= 1.02:
            continue
        edge = math.sqrt(max(0.0, 1.0 - min(1.0, u * u)))
        target = lower_height(side, world.x, APERTURE)
        if world.z >= target or world.z <= cz - 0.012:
            continue
        hit = sclera_trees[side].find_nearest(world, 0.010)
        if hit is None or hit[0] is None or hit[3] is None or hit[3] > 0.0045:
            continue
        proximity = max(0.0, min(1.0, (0.0045 - hit[3]) / 0.0040))
        vertical = max(0.0, min(1.0, (world.z - (cz - 0.0105)) / 0.009))
        weight = (proximity ** 1.45) * (vertical ** 0.85) * (edge ** 0.5)
        if weight < 0.025:
            continue
        before = world.copy()
        world.z += (target - world.z) * weight
        vertex.co = inverse @ world
        moved[side] += 1
        maximum = max(maximum, (world - before).length)
    body.data.update()
    return {"movedVertices": moved, "maximumDisplacementM": maximum}


def move_attached_curves():
    moved = []
    for side in EYES:
        for name in (
            f"AevryndEye_{side}_LowerLidMargin_R258",
            f"AevryndEye_{side}_TearMeniscus_R258",
            f"AevryndFemaleLowerLashes_{side}_R256",
        ):
            obj = bpy.data.objects[name]
            obj.data = obj.data.copy()
            count = 0
            for spline in obj.data.splines:
                for point in spline.points:
                    point.co.z += lower_height(side, point.co.x, APERTURE) - lower_height(side, point.co.x, SOURCE_APERTURE)
                    count += 1
            obj["aevrynd_revision"] = "v249r334"
            moved.append({"object": name, "points": count})
    return moved


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
body = bpy.data.objects[BODY]
sclera_trees = {side: world_bvh(bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"], depsgraph) for side in EYES}
body.data = body.data.copy()
edit = sculpt_lower_lids(body, sclera_trees)
body["aevrynd_revision"] = "v249r334-continuous-upper-lower-eyelids"
body["aevrynd_lower_aperture_m"] = APERTURE
attached = move_attached_curves()
for side in EYES:
    sclera = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
    sclera.matrix_world.translation.y += SCLERA_RECESS
    sclera["aevrynd_revision"] = "v249r334-minimum-clearance"
    sclera["aevrynd_additional_recess_m"] = SCLERA_RECESS

collision = {"frames": {}, "violations": []}
for frame in (1, 20):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = world_bvh(body, depsgraph)
    collision["frames"][str(frame)] = {}
    for side in EYES:
        sclera = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
        count = len(body_tree.overlap(world_bvh(sclera, depsgraph)))
        collision["frames"][str(frame)][side] = {"bodyVsIntegratedEye": count}
        if count:
            collision["violations"].append({"frame": frame, "side": side, "triangleOverlaps": count})
collision["status"] = "PASS" if not collision["violations"] else "FAIL"
AUDIT.write_text(json.dumps(collision, indent=2), encoding="utf-8")

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
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
scene["aevrynd_mainline_revision"] = "v249r334-continuous-upper-lower-eyelids"
scene["aevrynd_release_state"] = "TECHNICAL_PASS_VISUAL_REVIEW_PENDING" if collision["status"] == "PASS" else "COLLISION_FAIL"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "renderDirectory": str(RENDER_DIR),
    "lowerApertureM": APERTURE, "additionalScleraRecessM": SCLERA_RECESS,
    "bodyEdit": edit, "attachedCurves": attached, "collisionAudit": str(AUDIT),
    "collisionStatus": collision["status"], "ownedAssetOnly": True,
    "status": "TECHNICAL_PASS_VISUAL_REVIEW_PENDING" if collision["status"] == "PASS" else "COLLISION_FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R334_CONTINUOUS_EYELIDS=" + json.dumps(report, sort_keys=True))
if collision["status"] != "PASS":
    raise SystemExit(2)
