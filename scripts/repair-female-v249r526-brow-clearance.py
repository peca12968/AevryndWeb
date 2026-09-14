import json
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-orbital-optical-prune-r525.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-orbital-brow-refit-r526.blend"
REPORT = ASSETS / "female-v249-mainline-orbital-brow-refit-r526.build.json"
BODY = "AevryndFemaleBodyBaseV118"
BROWS = ("AevryndFemaleBrow_L_R480", "AevryndFemaleBrow_R_R480")
TARGET = 0.00013


def body_bvh(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(polygon.vertices) for polygon in mesh.polygons]
    return evaluated, mesh, BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
evaluated, mesh, surface = body_bvh(bpy.data.objects[BODY])
repairs = {}
for name in BROWS:
    obj = bpy.data.objects[name]
    inverse = obj.matrix_world.inverted()
    before, after = [], []
    moved = 0
    maximum_move = 0.0
    for spline in obj.data.splines:
        for point in spline.points:
            world = obj.matrix_world @ point.co.xyz
            nearest, normal, _index, _distance = surface.find_nearest(world)
            signed = (world - nearest).dot(normal)
            before.append(signed)
            if signed < TARGET:
                movement = TARGET - signed
                world += normal * movement
                point.co = (*(inverse @ world), 1.0)
                moved += 1
                maximum_move = max(maximum_move, movement)
            repaired = obj.matrix_world @ point.co.xyz
            nearest, normal, _index, _distance = surface.find_nearest(repaired)
            after.append((repaired - nearest).dot(normal))
    obj["aevrynd_revision"] = "v249r526"
    obj["aevrynd_clearance_method"] = "all curve controls projected to r525 evaluated body normal at frame 1"
    repairs[name] = {
        "controlPoints": len(before),
        "movedControlPoints": moved,
        "minimumSignedBeforeMm": min(before) * 1000.0,
        "minimumSignedAfterMm": min(after) * 1000.0,
        "maximumMoveMm": maximum_move * 1000.0,
    }
evaluated.to_mesh_clear()
scene["aevrynd_character_revision"] = "v249r526-orbital-brow-refit"
scene["aevrynd_character_status"] = "offline technical candidate; audits pending"
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "targetControlPointClearanceMm": TARGET * 1000.0,
    "repairs": repairs,
    "geometryChangedOutsideBrows": False,
    "status": "BUILT_AUDITS_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R526_BROW_REFIT=" + json.dumps(report, sort_keys=True))
