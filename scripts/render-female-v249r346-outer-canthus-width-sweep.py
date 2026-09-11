import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-outer-canthus-width-r346.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r346-outer-canthus-width-sweep"
BODY = "AevryndFemaleBody_CC0_R249"
EYES = {"L": (0.034528, 1.607765, 1.0), "R": (-0.034443, 1.607765, -1.0)}
OLD_HALF = 0.01025
UPPER_APERTURE = 0.0022
LOWER_APERTURE = 0.0041
VARIANTS = (("a-10p0mm", 0.0100), ("b-9p6mm", 0.0096), ("c-9p2mm", 0.0092))

def look_at(obj, target): obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
def edge(dx, half): return math.sqrt(max(0.0, 1.0 - min(1.0, (abs(dx) / half) ** 2)))
def target_z(cz, dx, half, upper): return cz + (UPPER_APERTURE if upper else -LOWER_APERTURE) * edge(dx, half)

def world_bvh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph); mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ v.co for v in mesh.vertices]; faces = [tuple(p.vertices) for p in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False); evaluated.to_mesh_clear(); return tree

def make_body(source, name):
    mesh = source.data.copy(); obj = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(obj); obj.matrix_world = source.matrix_world.copy()
    return obj

def sculpt(body, half, eye_trees):
    inverse = body.matrix_world.inverted(); moved = {"L": 0, "R": 0}; maximum = 0.0
    for vertex in body.data.vertices:
        world = body.matrix_world @ vertex.co; side = "L" if world.x >= 0 else "R"; cx, cz, sign = EYES[side]
        dx = world.x - cx; lateral = sign * dx
        if lateral < 0.0045 or lateral > 0.0112 or abs(world.z - cz) > 0.0105: continue
        hit = eye_trees[side].find_nearest(world, 0.006)
        if hit is None or hit[3] is None or hit[3] > 0.0048: continue
        upper = world.z >= cz
        old = target_z(cz, dx, OLD_HALF, upper); new = target_z(cz, dx, half, upper)
        proximity = max(0.0, min(1.0, (0.0048 - hit[3]) / 0.0042))
        lateral_weight = max(0.0, min(1.0, (lateral - 0.0045) / 0.0040))
        weight = proximity ** 1.25 * lateral_weight ** 0.7
        before = world.copy(); world.z += (new - old) * weight; vertex.co = inverse @ world
        if (world - before).length > 1e-7: moved[side] += 1; maximum = max(maximum, (world - before).length)
    body.data.update(); return {"movedVertices": moved, "maximumDisplacementM": maximum}

def update_curves(half, originals):
    for name, points in originals.items():
        side = "L" if "_L_" in name else "R"; cx, cz, sign = EYES[side]; upper = "Upper" in name
        if "Lower" in name or "Meniscus" in name: upper = False
        i = 0; obj = bpy.data.objects[name]
        for spline in obj.data.splines:
            for point in spline.points:
                point.co = points[i].copy(); dx = point.co.x - cx; lateral = sign * dx
                if lateral > 0.0045:
                    blend = max(0.0, min(1.0, (lateral - 0.0045) / 0.0040))
                    point.co.z += (target_z(cz, dx, half, upper) - target_z(cz, dx, OLD_HALF, upper)) * blend
                    point.co.x = cx + dx * (1.0 - blend + blend * half / OLD_HALF)
                i += 1

bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); scene = bpy.context.scene; scene.frame_set(1); bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get(); source_body = bpy.data.objects[BODY]
eye_trees = {s: world_bvh(bpy.data.objects[f"AevryndEye_{s}_Sclera_R249"], depsgraph) for s in EYES}; source_body.hide_render = True
curve_names = [n for s in EYES for n in (f"AevryndEye_{s}_UpperLidMargin_R258", f"AevryndEye_{s}_LowerLidMargin_R258", f"AevryndEye_{s}_TearMeniscus_R258", f"AevryndFemaleUpperLashes_{s}_R256", f"AevryndFemaleLowerLashes_{s}_R256")]
originals = {}
for name in curve_names:
    obj = bpy.data.objects[name]; obj.data = obj.data.copy(); originals[name] = [p.co.copy() for spline in obj.data.splines for p in spline.points]

scene.render.engine = "BLENDER_EEVEE"; scene.render.resolution_percentage = 100; scene.render.image_settings.file_format = "PNG"; scene.view_settings.exposure = 0.0
RENDER_DIR.mkdir(parents=True, exist_ok=True); camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (("eyes", (0.0, -0.46, 1.615), (0.0, -0.035, 1.610), 105), ("face", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92), ("three-quarter", (0.45, -0.62, 1.62), (0.0, -0.02, 1.605), 90))
metrics = {}; previous = None
for label, half in VARIANTS:
    if previous: bpy.data.objects.remove(previous, do_unlink=True)
    body = make_body(source_body, f"AevryndFemaleOuterCanthus_{label}"); edit = sculpt(body, half, eye_trees); update_curves(half, originals); bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get(); body_tree = world_bvh(body, depsgraph)
    overlaps = {s: len(body_tree.overlap(world_bvh(bpy.data.objects[f"AevryndEye_{s}_Sclera_R249"], depsgraph))) for s in EYES}
    for view_name, location, target, lens in views:
        camera.location = location; camera.data.lens = lens; look_at(camera, target); scene.render.resolution_x = scene.render.resolution_y = 1000
        scene.render.filepath = str(RENDER_DIR / f"{label}-{view_name}.png"); bpy.ops.render.render(write_still=True)
    metrics[label] = {"halfWidthM": half, "fullNominalWidthM": half * 2, **edit, "bodyEyeTriangleOverlaps": overlaps}; previous = body

report = {"source": str(SOURCE), "renderDirectory": str(RENDER_DIR), "variants": metrics, "method": "Close only the lateral high-density eyelid skin toward narrower elliptical targets and synchronously move lid-margin, tear-film and lash curves.", "status": "VISUAL_AND_COLLISION_REVIEW_PENDING"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8"); print("AEVRYND_R346_OUTER_CANTHUS_WIDTH=" + json.dumps(report, sort_keys=True))
