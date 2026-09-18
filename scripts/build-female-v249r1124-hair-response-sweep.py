"""Add physical root-to-tip melanin and roughness variation to the r1123 groom."""
from pathlib import Path
import json

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-rear-contour-r1123-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-hair-response-r1124-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1124-hair-response-sweep.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1124-hair-response-sweep"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
HAIR = "AevryndFemaleGradedHairlineGroom_R1081"
SCALP = "AevryndFemaleTargetScalp_R976"
FRAMES = (1, 20, 33, 61)
# label, root melanin, tip melanin, root roughness, tip roughness, coat, random color
VARIANTS = (
    ("a-subtle", 0.68, 0.56, 0.36, 0.31, 0.04, 0.08),
    ("b-balanced", 0.72, 0.48, 0.38, 0.28, 0.07, 0.10),
    ("c-strong", 0.78, 0.38, 0.40, 0.24, 0.10, 0.12),
)
SELECTED = "b-balanced"


def body_tree(body, depsgraph):
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def tune_material(hair, values):
    root_melanin, tip_melanin, root_roughness, tip_roughness, coat, random_color = values
    material = hair.data.materials[0]
    tree = material.node_tree
    for node in list(tree.nodes):
        if node.get("aevrynd_r1124"):
            tree.nodes.remove(node)
    bsdf = next(node for node in tree.nodes if node.bl_idname == "ShaderNodeBsdfHairPrincipled")
    bsdf.parametrization = "MELANIN"
    info = tree.nodes.new("ShaderNodeHairInfo"); info.name = "Aevrynd Hair Intercept R1124"; info["aevrynd_r1124"] = True
    melanin = tree.nodes.new("ShaderNodeMapRange"); melanin.name = "Aevrynd Melanin Gradient R1124"; melanin["aevrynd_r1124"] = True
    roughness = tree.nodes.new("ShaderNodeMapRange"); roughness.name = "Aevrynd Roughness Gradient R1124"; roughness["aevrynd_r1124"] = True
    melanin.inputs["From Min"].default_value = 0.0; melanin.inputs["From Max"].default_value = 1.0
    melanin.inputs["To Min"].default_value = root_melanin; melanin.inputs["To Max"].default_value = tip_melanin
    roughness.inputs["From Min"].default_value = 0.0; roughness.inputs["From Max"].default_value = 1.0
    roughness.inputs["To Min"].default_value = root_roughness; roughness.inputs["To Max"].default_value = tip_roughness
    tree.links.new(info.outputs["Intercept"], melanin.inputs["Value"])
    tree.links.new(info.outputs["Intercept"], roughness.inputs["Value"])
    tree.links.new(melanin.outputs["Result"], bsdf.inputs["Melanin"])
    tree.links.new(roughness.outputs["Result"], bsdf.inputs["Roughness"])
    bsdf.inputs["Radial Roughness"].default_value = 0.27
    bsdf.inputs["Coat"].default_value = coat
    bsdf.inputs["Random Color"].default_value = random_color
    bsdf.inputs["Random Roughness"].default_value = 0.07
    info.location = (-520, 80); melanin.location = (-300, 130); roughness.location = (-300, -80)
    return {"material": material.name, "rootMelanin": root_melanin, "tipMelanin": tip_melanin,
            "rootRoughness": root_roughness, "tipRoughness": tip_roughness, "radialRoughness": 0.27,
            "coat": coat, "randomColor": random_color, "randomRoughness": 0.07}


def collision_audit(scene, hair, body):
    result = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get(); depsgraph.update()
        tree = body_tree(body, depsgraph); evaluated = hair.evaluated_get(depsgraph)
        signed = []
        for point in evaluated.data.points:
            world = evaluated.matrix_world @ point.position
            hit = tree.find_nearest(world)
            if hit and hit[1] is not None:
                signed.append((world - hit[0]).dot(hit[1].normalized()))
        result[str(frame)] = {"pointsTested": len(signed), "minimumSignedClearanceM": min(signed),
                              "penetratingPoints": sum(v < -0.00005 for v in signed),
                              "belowOneMmPoints": sum(v < 0.001 for v in signed)}
    scene.frame_set(1); return result


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, label, view, frame=1):
    scene.frame_set(frame); camera = scene.camera
    views = {"front": ((0.0, -1.05, 1.43), (0.0, 0.0, 1.40), 72, (1000, 1000)),
             "oblique": ((0.44, -0.92, 1.46), (0.0, -0.01, 1.40), 72, (1000, 1000)),
             "back": ((0.0, 1.02, 1.43), (0.0, 0.0, 1.40), 72, (1000, 1000)),
             "hairline": ((0.0, -0.53, 1.59), (0.0, -0.02, 1.55), 115, (1200, 850))}
    camera.location, target, camera.data.lens, size = views[view]; look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size; scene.render.resolution_percentage = 100
    path = OUT / f"{label}-{view}-f{frame:02d}.png"; scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True); return str(path)


OUT.mkdir(parents=True, exist_ok=True)
variants = []
for row in VARIANTS:
    label, *values = row
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene; body = bpy.data.objects[BODY]; hair = bpy.data.objects[HAIR]; scalp = bpy.data.objects[SCALP]
    hair.hide_render = hair.hide_viewport = scalp.hide_render = scalp.hide_viewport = False
    material = tune_material(hair, values)
    collision = collision_audit(scene, hair, body)
    passed = all(a["penetratingPoints"] == 0 for a in collision.values())
    renders = [render(scene, label, view, 1) for view in ("front", "oblique", "back", "hairline")]
    renders.append(render(scene, label, "front", 33))
    variants.append({"label": label, "material": material, "collisionAudit": collision,
                     "technicalStatus": "TECHNICAL_PASS" if passed else "TECHNICAL_FAIL", "renders": renders})
    if label == SELECTED and passed:
        hair["aevrynd_revision"] = "v249r1124-hair-response"
        hair["aevrynd_material_method"] = "intercept-driven melanin and longitudinal roughness response"
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"; scene["aevrynd_website_promotion"] = "forbidden"
        scene.frame_set(1); bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

selected = next((v for v in variants if v["label"] == SELECTED and v["technicalStatus"] == "TECHNICAL_PASS"), None)
report = {"revision": "v249r1124-hair-response-sweep", "source": str(SOURCE), "output": str(OUTPUT) if selected else None,
          "method": "drive melanin concentration and longitudinal roughness from the physical strand intercept while retaining bounded random color and roughness",
          "variants": variants, "selectedVariant": SELECTED if selected else None, "websitePromotionApproved": False,
          "candidateStatus": "VISUAL_REVIEW_PENDING" if selected else "TECHNICAL_FAIL_DIAGNOSTIC_ONLY"}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1124=" + json.dumps({"variants": [{"label": v["label"], "material": v["material"],
      "penetrating": {f: a["penetratingPoints"] for f, a in v["collisionAudit"].items()}, "status": v["technicalStatus"]}
      for v in variants]}, sort_keys=True))
