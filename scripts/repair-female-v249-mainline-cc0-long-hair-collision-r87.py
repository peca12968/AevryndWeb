import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-long-hair-fit-r86.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-long-hair-collision-r87.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-cc0-long-hair-collision-r87"
BODY = "AevryndFemaleBodyBaseV118"
HAIR = (
    "AevryndFemaleCC0LongHairFitMain_v249r86",
    "AevryndFemaleCC0LongHairFitFlyaway_v249r86",
)
TARGET = 0.0015
NEAR = 0.030


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def evaluated_tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def signed_hit(tree, world):
    hit = tree.find_nearest(world)
    if hit is None or hit[1] is None or hit[3] > NEAR:
        return None
    normal = hit[1].normalized()
    return hit[0], normal, (world - hit[0]).dot(normal)


def repair(obj, tree):
    inverse = obj.matrix_world.inverted()
    before = 0
    maximum = 0.0
    displacement = [Vector((0.0, 0.0, 0.0)) for _ in obj.data.points]
    for index, point in enumerate(obj.data.points):
        world = obj.matrix_world @ point.position
        hit = signed_hit(tree, world)
        if hit is None or hit[2] >= TARGET:
            continue
        before += hit[2] < -0.0005
        delta = hit[1] * (TARGET - hit[2])
        displacement[index] = delta
        maximum = max(maximum, delta.length)

    # Spread the contact correction over adjacent samples to preserve continuous
    # locks instead of creating one-point kinks.
    for _pass in range(2):
        smoothed = list(displacement)
        for curve in obj.data.curves:
            for local in range(1, curve.points_length - 1):
                index = curve.first_point_index + local
                neighbor = (displacement[index - 1] + displacement[index] * 2.0 + displacement[index + 1]) * 0.25
                if neighbor.length > smoothed[index].length:
                    smoothed[index] = neighbor
        displacement = smoothed
    for index, delta in enumerate(displacement):
        if delta.length_squared:
            world = obj.matrix_world @ obj.data.points[index].position
            obj.data.points[index].position = inverse @ (world + delta)

    # Hard final projection enforces the collision invariant after smoothing.
    remaining = 0
    final_max = maximum
    for index, point in enumerate(obj.data.points):
        world = obj.matrix_world @ point.position
        hit = signed_hit(tree, world)
        if hit is None or hit[2] >= TARGET:
            continue
        delta = hit[1] * (TARGET - hit[2])
        point.position = inverse @ (world + delta)
        final_max = max(final_max, delta.length)
        check = signed_hit(tree, obj.matrix_world @ point.position)
        if check is not None and check[2] < -0.0005:
            remaining += 1
    obj.data.update_tag()
    obj["aevrynd_revision"] = "v249-mainline-cc0-long-hair-collision-r87"
    obj["aevrynd_collision_clearance_m"] = TARGET
    return {"penetrating_before": before, "penetrating_after_immediate": remaining, "max_correction_mm": final_max * 1000.0}


def render(camera, name, location, target, lens, resolution=(1000, 1000)):
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = resolution
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
scene.frame_set(1)
tree = evaluated_tree(bpy.data.objects[BODY], bpy.context.evaluated_depsgraph_get())
repairs = {name: repair(bpy.data.objects[name], tree) for name in HAIR}
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "cc0-long-hair-collision-r87"
scene["aevrynd_release_state"] = "R87_VISUAL_STATIC_AND_DYNAMIC_REVIEW_REQUIRED"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("01-front", (0.0, -2.15, 1.55), (0.0, 0.0, 1.55), 82, (1000, 1000)),
    ("02-three-quarter", (1.28, -1.72, 1.57), (0.0, 0.0, 1.55), 82, (1000, 1000)),
    ("03-profile", (2.15, 0.0, 1.57), (0.0, 0.0, 1.55), 86, (1000, 1000)),
    ("04-back", (0.0, 2.10, 1.56), (0.0, 0.02, 1.54), 82, (1000, 1000)),
    ("05-top", (0.0, -0.30, 2.35), (0.0, 0.0, 1.66), 78, (1000, 1000)),
    ("06-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000)),
)
for args in views:
    render(camera, *args)

report = {
    "source": str(SOURCE), "output": str(OUTPUT), "target_clearance_m": TARGET,
    "repairs": repairs, "status": "STATIC_REAUDIT_REQUIRED",
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_CC0_LONG_HAIR_COLLISION_R87=" + json.dumps(report, sort_keys=True))
