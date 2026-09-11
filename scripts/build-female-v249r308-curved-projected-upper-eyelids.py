import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-recessed-natural-eyes-r301.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-curved-projected-upper-eyelids-r308.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-curved-projected-upper-eyelids-r308.build-report.json"
AUDIT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-curved-projected-upper-eyelids-r308.collision-audit.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r308-curved-projected-upper-eyelids"
BODY = "AevryndFemaleBody_CC0_R249"
RIG = "AevryndFemaleRig"
EYES = {"L": (0.034528, 1.607765, 1.0), "R": (-0.034443, 1.607765, -1.0)}
APERTURE = 0.0027
OUTER_CLEARANCE = 0.00010
CORNER_RECEDE = 0.0035
PROJECTION_POWER = 0.65


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def lid_height(side, x):
    cx, cz, anatomical_sign = EYES[side]
    u = max(-1.0, min(1.0, (x - cx) / 0.01035))
    edge = math.sqrt(max(0.0, 1.0 - u * u))
    return cz + APERTURE * edge - 0.00032 * anatomical_sign * u * edge


def shift_attached_curves(side):
    cx, cz, _ = EYES[side]
    moved = {}
    for name in (f"AevryndEye_{side}_UpperLidMargin_R258", f"AevryndFemaleUpperLashes_{side}_R256"):
        obj = bpy.data.objects.get(name)
        if obj is None or obj.type != "CURVE":
            continue
        obj.data = obj.data.copy()
        count = 0
        for spline in obj.data.splines:
            for point in spline.points:
                u = max(-1.0, min(1.0, (point.co.x - cx) / 0.01035))
                edge = math.sqrt(max(0.0, 1.0 - u * u))
                point.co.z += lid_height(side, point.co.x) - (cz + 0.00525 * edge)
                count += 1
        obj["aevrynd_revision"] = "v249r308"
        moved[name] = count
    return moved


def make_lid(side, material, rig, body_bvh):
    cx, cz, anatomical_sign = EYES[side]
    count = 41
    rows = 5
    vertices = []
    projection = []
    for row in range(rows):
        v = row / (rows - 1)
        for index in range(count):
            u = -0.985 + 1.97 * index / (count - 1)
            edge = math.sqrt(max(0.0, 1.0 - u * u))
            outer = anatomical_sign * u
            inner_z = cz + APERTURE * edge - 0.00032 * outer * edge
            inner_y = -0.14072 + CORNER_RECEDE * (abs(u) ** 2.15)
            point = Vector((cx + 0.01035 * u, inner_y - 0.00024 * math.sin(v * math.pi), inner_z + (0.0048 * edge + 0.00035) * v))
            nearest, normal, _index, distance = body_bvh.find_nearest(point)
            if nearest is not None:
                projected = nearest + normal.normalized() * OUTER_CLEARANCE
                point = point.lerp(projected, v ** PROJECTION_POWER)
                projection.append(distance)
            vertices.append(tuple(point))
    faces = []
    for row in range(rows - 1):
        for index in range(count - 1):
            a = row * count + index
            faces.append((a, a + 1, a + count + 1, a + count))
    mesh = bpy.data.meshes.new(f"AevryndEye_{side}_UpperLidSurface_R308Geometry")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(f"AevryndEye_{side}_UpperLidSurface_R308", mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world
    obj["aevrynd_layer"] = f"eye.{side.lower()}.upper_lid_surface"
    obj["aevrynd_binding"] = "rig.head"
    obj["aevrynd_revision"] = "v249r308"
    obj["aevrynd_outer_clearance_m"] = OUTER_CLEARANCE
    return obj, {"vertices": len(vertices), "faces": len(faces), "projectedVertices": len(projection), "maximumProjectionDistanceM": max(projection) if projection else 0.0}


def overlap_count(a, b, depsgraph):
    return len(BVHTree.FromObject(a, depsgraph).overlap(BVHTree.FromObject(b, depsgraph)))


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
body = bpy.data.objects[BODY]
body_bvh = BVHTree.FromObject(body, depsgraph)
rig = bpy.data.objects[RIG]
skin_material = body.data.materials[0]
created = {}
curve_moves = {}
for side in EYES:
    curve_moves.update(shift_attached_curves(side))
    lid, metrics = make_lid(side, skin_material, rig, body_bvh)
    created[side] = {"object": lid.name, **metrics}

scene["aevrynd_mainline_revision"] = "v249r308-curved-projected-upper-eyelids"
scene["aevrynd_release_state"] = "TECHNICAL_AND_VISUAL_REVIEW_PENDING"
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

collision = {"frames": {}, "violations": []}
for frame in (1, 20):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    frame_rows = {}
    for side in EYES:
        lid = bpy.data.objects[created[side]["object"]]
        rows = {"Body": overlap_count(lid, body, depsgraph)}
        if rows["Body"]:
            collision["violations"].append({"frame": frame, "side": side, "part": "Body", "triangleOverlaps": rows["Body"]})
        for part in ("Sclera_R249", "Cornea_R252", "Limbal_R253", "Iris_R253", "Pupil_R253"):
            eye = bpy.data.objects[f"AevryndEye_{side}_{part}"]
            rows[part] = overlap_count(lid, eye, depsgraph)
            if rows[part]:
                collision["violations"].append({"frame": frame, "side": side, "part": part, "triangleOverlaps": rows[part]})
        frame_rows[side] = rows
    collision["frames"][str(frame)] = frame_rows
collision["status"] = "PASS" if not collision["violations"] else "FAIL"
AUDIT.write_text(json.dumps(collision, indent=2), encoding="utf-8")

scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "apertureHeightM": APERTURE,
    "outerClearanceM": OUTER_CLEARANCE, "cornerRecedeM": CORNER_RECEDE,
    "projectionPower": PROJECTION_POWER, "createdLayers": created, "movedCurves": curve_moves,
    "collisionAudit": str(AUDIT), "collisionStatus": collision["status"],
    "renderDirectory": str(RENDER_DIR), "ownedAssetOnly": True,
    "status": "TECHNICAL_PASS_VISUAL_REVIEW_PENDING" if collision["status"] == "PASS" else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R308_CURVED_PROJECTED_UPPER_EYELIDS=" + json.dumps(report, sort_keys=True))
if collision["status"] != "PASS":
    raise SystemExit(2)
