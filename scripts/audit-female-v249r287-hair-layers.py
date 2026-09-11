import json
import math
from pathlib import Path

import bpy
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-matte-root-underlayer-r287.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-matte-root-underlayer-r287.layer-audit.json"
BODY = "AevryndFemaleBody_CC0_R249"
RIG = "AevryndFemaleRig"
MAIN = "AevryndFemaleRuntimeHairCards_R276"
SCALP = "AevryndFemaleScalpUnderlayer_R280"
HAIRLINE = "AevryndFemaleHairlineTransitionCards_R285"
FRAMES = (1, 33, 61)


def body_tree(depsgraph):
    evaluated = bpy.data.objects[BODY].evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def signed_clearance(obj, tree, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    values = []
    for vertex in mesh.vertices:
        world = evaluated.matrix_world @ vertex.co
        hit = tree.find_nearest(world, 0.05)
        if hit is not None and hit[1] is not None:
            values.append((world - hit[0]).dot(hit[1].normalized()))
    evaluated.to_mesh_clear()
    return {
        "samples": len(values), "minimumSignedM": min(values), "maximumSignedM": max(values),
        "penetratingVertices": sum(value < 0.0 for value in values),
    }


bpy.ops.wm.open_mainfile(filepath=str(MODEL))
scene = bpy.context.scene
failures = []
objects = {}
expected = {
    MAIN: {"vertices": 18432, "polygons": 8832, "material": "Aevrynd_RuntimeHairCards_DenseAlpha_R276", "layer": "hair.runtime_cards.dynamic.alpha.wide_clumps"},
    SCALP: {"vertices": 758, "polygons": 708, "material": "Aevrynd_ScalpUnderlayer_R280", "layer": "hair.scalp_underlayer.head_bound"},
    HAIRLINE: {"vertices": 768, "polygons": 352, "material": "Aevrynd_RuntimeHairCards_Alpha_R272", "layer": "hair.hairline_transition.head_bound"},
}
for name, contract in expected.items():
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        failures.append({"missingLayer": name})
        continue
    material_names = [material.name for material in obj.data.materials]
    objects[name] = {
        "vertices": len(obj.data.vertices), "polygons": len(obj.data.polygons),
        "materials": material_names, "layer": obj.get("aevrynd_layer"),
        "parent": obj.parent.name if obj.parent else None,
        "armatureModifiers": [modifier.object.name for modifier in obj.modifiers if modifier.type == "ARMATURE" and modifier.object],
        "vertexGroups": [group.name for group in obj.vertex_groups],
    }
    if len(obj.data.vertices) != contract["vertices"]:
        failures.append({"layer": name, "vertices": len(obj.data.vertices), "expected": contract["vertices"]})
    if len(obj.data.polygons) != contract["polygons"]:
        failures.append({"layer": name, "polygons": len(obj.data.polygons), "expected": contract["polygons"]})
    if contract["material"] not in material_names:
        failures.append({"layer": name, "missingMaterial": contract["material"]})
    if obj.get("aevrynd_layer") != contract["layer"]:
        failures.append({"layer": name, "layerTag": obj.get("aevrynd_layer"), "expected": contract["layer"]})
    if obj.parent != bpy.data.objects[RIG]:
        failures.append({"layer": name, "parent": obj.parent.name if obj.parent else None, "expected": RIG})
    if not any(modifier.type == "ARMATURE" and modifier.object == bpy.data.objects[RIG] for modifier in obj.modifiers):
        failures.append({"layer": name, "missingArmature": RIG})

clearance = {SCALP: {}, HAIRLINE: {}}
for frame in FRAMES:
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    tree = body_tree(depsgraph)
    for name in (SCALP, HAIRLINE):
        values = signed_clearance(bpy.data.objects[name], tree, depsgraph)
        clearance[name][str(frame)] = values
        if values["penetratingVertices"]:
            failures.append({"layer": name, "frame": frame, "penetratingVertices": values["penetratingVertices"]})

scalp_shader = next(node for node in bpy.data.materials["Aevrynd_ScalpUnderlayer_R280"].node_tree.nodes if node.type == "BSDF_PRINCIPLED")
scalp_material = {
    "baseColor": list(scalp_shader.inputs["Base Color"].default_value),
    "roughness": scalp_shader.inputs["Roughness"].default_value,
    "specularIorLevel": scalp_shader.inputs["Specular IOR Level"].default_value,
}
if abs(scalp_material["roughness"] - 1.0) > 1e-6 or abs(scalp_material["specularIorLevel"]) > 1e-6:
    failures.append({"scalpMaterial": scalp_material, "expected": {"roughness": 1.0, "specularIorLevel": 0.0}})

report = {
    "model": str(MODEL), "objects": objects, "clearance": clearance,
    "scalpMaterial": scalp_material, "frames": list(FRAMES),
    "failures": failures, "status": "FAIL" if failures else "PASS",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R287_HAIR_LAYER_AUDIT=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
