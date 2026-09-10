import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-curly-root-coverage-r158.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-curly-scalp-foundation-r159.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-curly-scalp-foundation-r159.build-report.json"
BODY = "AevryndFemaleBodyBaseV118"
SCALP = "AevryndFemaleAnatomicalScalpFoundation_v249r101"
FRAMES = (1, 20)
TARGET = 0.0010
NEAR = 0.030


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


def project_scalp(obj, scene):
    inverse = obj.matrix_world.inverted()
    maximum = 0.0
    operations = 0
    logs = []
    for pass_index in range(6):
        pass_operations = 0
        pass_maximum = 0.0
        for frame in FRAMES:
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            tree = evaluated_tree(bpy.data.objects[BODY], bpy.context.evaluated_depsgraph_get())
            for vertex in obj.data.vertices:
                world = obj.matrix_world @ vertex.co
                hit = signed_hit(tree, world)
                if hit is None or hit[2] >= TARGET:
                    continue
                delta = hit[1] * (TARGET - hit[2])
                vertex.co = inverse @ (world + delta)
                pass_operations += 1
                pass_maximum = max(pass_maximum, delta.length)
        obj.data.update()
        logs.append({"pass": pass_index + 1, "operations": pass_operations, "maxCorrectionMm": pass_maximum * 1000.0})
        operations += pass_operations
        maximum = max(maximum, pass_maximum)
        if pass_operations == 0:
            break
    return operations, maximum, logs


def make_material():
    material = bpy.data.materials.get("AevryndOwnedCurlyScalpFoundationMaterial_v249r159")
    if material is None:
        material = bpy.data.materials.new("AevryndOwnedCurlyScalpFoundationMaterial_v249r159")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Base Color"].default_value = (0.020, 0.0065, 0.0032, 1.0)
    shader.inputs["Roughness"].default_value = 0.72
    shader.inputs["Specular IOR Level"].default_value = 0.25
    shader.inputs["Coat Weight"].default_value = 0.02
    material.node_tree.links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material["aevrynd_revision"] = "v249r159"
    material["aevrynd_runtime_dependency"] = "none"
    return material


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scalp = bpy.data.objects[SCALP]
scalp.hide_render = False
scalp.hide_viewport = False
scalp.name = "AevryndFemaleOwnedCurlyScalpFoundation_v249r159"
scalp.data.name = scalp.name + "Data"
scalp.data.materials.clear()
scalp.data.materials.append(make_material())
operations, maximum, logs = project_scalp(scalp, scene)
scalp["aevrynd_layer"] = "hair.scalp.foundation"
scalp["aevrynd_revision"] = "v249r159"
scalp["aevrynd_source"] = "Aevrynd-owned anatomical scalp foundation with owned procedural material"
scalp["aevrynd_runtime_dependency"] = "none"
scalp["aevrynd_collision_clearance_m"] = TARGET
scalp["aevrynd_collision_status"] = "PENDING_STRICT_AUDIT"
scene["aevrynd_revision"] = "v249r159"
scene["aevrynd_candidate_status"] = "COLLISION_AND_VISUAL_REVIEW_PENDING"
scene["aevrynd_hair_layers"] = ["hair.scalp.foundation", "hair.root.coverage.curly", "hair.follow.curly.main"]
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "scalp": scalp.name,
    "layer": "hair.scalp.foundation",
    "vertices": len(scalp.data.vertices),
    "faces": len(scalp.data.polygons),
    "targetClearanceM": TARGET,
    "projectionOperations": operations,
    "maxSingleCorrectionMm": maximum * 1000.0,
    "passes": logs,
    "runtimeDependency": "none",
    "status": "COLLISION_AND_VISUAL_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R159_BUILD=" + json.dumps({
    "output": str(OUTPUT), "projectionOperations": operations,
    "maxSingleCorrectionMm": maximum * 1000.0, "status": report["status"]
}, sort_keys=True))
