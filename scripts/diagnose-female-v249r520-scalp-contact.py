from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
MODELS = (
    ASSETS / "aevrynd-female-authoring-v249-mainline-layered-front-locks-r517.blend",
    ASSETS / "aevrynd-female-authoring-v249-mainline-natural-eye-ratio-r520.blend",
)

for model in MODELS:
    bpy.ops.wm.open_mainfile(filepath=str(model))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    body = bpy.data.objects["AevryndFemaleBodyBaseV118"].evaluated_get(dg)
    mesh = body.to_mesh()
    points = [body.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(points, faces, all_triangles=False)
    body.to_mesh_clear()
    scalp = bpy.data.objects["AevryndFemaleRuntimeScalpCap_R467"].evaluated_get(dg)
    contacts = []
    for index, vertex in enumerate(scalp.data.vertices):
        point = scalp.matrix_world @ vertex.co
        hit = tree.find_nearest(point, 0.025)
        if hit is None or hit[1] is None:
            continue
        signed = (point - hit[0]).dot(hit[1].normalized())
        if signed < -0.0005:
            contacts.append((index, list(point), list(hit[0]), signed, hit[2]))
    print(model.name, contacts)
