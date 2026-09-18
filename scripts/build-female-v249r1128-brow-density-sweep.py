"""Increase the existing owned eyebrow foundation density without adding geometry."""
from pathlib import Path
import json

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-rear-contour-r1123-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-brow-density-r1128-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1128-brow-density-sweep.study.json"
OUT = ROOT.parent / "Temp" / "female-realism" / "v249r1128-brow-density-sweep"
BODY = "AevryndFemaleCC0PalpebralClosure_R1097"
HAIR = "AevryndFemaleGradedHairlineGroom_R1081"
SCALP = "AevryndFemaleTargetScalp_R976"
BROWS = ("Brow_L", "Brow_R", "Brow_L_Density", "Brow_R_Density")
FRAMES = (1, 20, 33, 61)
VARIANTS = (("a-soft", 0.24), ("b-balanced", 0.32), ("c-defined", 0.40))
SELECTED = "b-balanced"


def body_tree(body, depsgraph):
    evaluated = body.evaluated_get(depsgraph); mesh = evaluated.to_mesh()
    tree = BVHTree.FromPolygons([evaluated.matrix_world @ v.co for v in mesh.vertices],
                                [tuple(p.vertices) for p in mesh.polygons], all_triangles=False)
    evaluated.to_mesh_clear(); return tree


def tune_density(alpha):
    material = bpy.data.materials["Aevrynd_Brow_Density_v39"]
    bsdf = next(n for n in material.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
    bsdf.inputs["Alpha"].default_value = alpha
    bsdf.inputs["Roughness"].default_value = 0.72
    bsdf.inputs["Specular IOR Level"].default_value = 0.14
    material.surface_render_method = "DITHERED"
    return {"material": material.name, "alpha": alpha, "roughness": 0.72, "specularIORLevel": 0.14}


def brow_collision(scene, body):
    result = {}
    for frame in FRAMES:
        scene.frame_set(frame); depsgraph = bpy.context.evaluated_depsgraph_get(); depsgraph.update(); tree = body_tree(body, depsgraph)
        frame_result = {}
        for name in BROWS:
            obj = bpy.data.objects[name].evaluated_get(depsgraph); signed = []
            for vertex in obj.data.vertices:
                world = obj.matrix_world @ vertex.co; hit = tree.find_nearest(world)
                if hit and hit[1] is not None: signed.append((world - hit[0]).dot(hit[1].normalized()))
            frame_result[name] = {"verticesTested": len(signed), "minimumSignedClearanceM": min(signed),
                                  "penetratingVertices": sum(v < -0.00005 for v in signed)}
        result[str(frame)] = frame_result
    scene.frame_set(1); return result


def look_at(camera, target): camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, label, view, frame=1):
    scene.frame_set(frame); camera = scene.camera
    views = {"portrait": ((0.0, -1.05, 1.43), (0.0, 0.0, 1.40), 72, (1000, 1000)),
             "face": ((0.0, -0.64, 1.47), (0.0, -0.035, 1.445), 100, (1200, 1000)),
             "oblique": ((0.26, -0.62, 1.48), (0.0, -0.035, 1.445), 100, (1200, 1000)),
             "brow": ((0.0, -0.46, 1.51), (0.0, -0.055, 1.485), 125, (1200, 700))}
    camera.location, target, camera.data.lens, size = views[view]; look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size; scene.render.resolution_percentage = 100
    path = OUT / f"{label}-{view}-f{frame:02d}.png"; scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True); return str(path)


OUT.mkdir(parents=True, exist_ok=True); variants = []
for label, alpha in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene; body = bpy.data.objects[BODY]
    bpy.data.objects[HAIR].hide_render = bpy.data.objects[HAIR].hide_viewport = False
    bpy.data.objects[SCALP].hide_render = bpy.data.objects[SCALP].hide_viewport = False
    material = tune_density(alpha); collision = brow_collision(scene, body)
    passed = all(item["penetratingVertices"] == 0 for frame in collision.values() for item in frame.values())
    renders = [render(scene, label, view, 1) for view in ("portrait", "face", "oblique", "brow")]
    renders.append(render(scene, label, "face", 33))
    variants.append({"label": label, "material": material, "collisionAudit": collision,
                     "technicalStatus": "TECHNICAL_PASS" if passed else "TECHNICAL_FAIL", "renders": renders})
    if label == SELECTED and passed:
        for name in BROWS: bpy.data.objects[name]["aevrynd_revision"] = "v249r1128-brow-density"
        scene["aevrynd_release_state"] = "VISUAL_REVIEW_PENDING"; scene["aevrynd_website_promotion"] = "forbidden"
        scene.frame_set(1); bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

selected = next((v for v in variants if v["label"] == SELECTED and v["technicalStatus"] == "TECHNICAL_PASS"), None)
report = {"revision": "v249r1128-brow-density-sweep", "source": str(SOURCE), "output": str(OUTPUT) if selected else None,
          "method": "raise only the existing owned brow foundation alpha while retaining separate strand meshes and proving four-frame surface clearance",
          "variants": variants, "selectedVariant": SELECTED if selected else None, "websitePromotionApproved": False,
          "candidateStatus": "VISUAL_REVIEW_PENDING" if selected else "TECHNICAL_FAIL_DIAGNOSTIC_ONLY"}
REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print("AEVRYND_R1128=" + json.dumps({"variants": [{"label": v["label"], "alpha": v["material"]["alpha"],
      "penetrating": sum(i["penetratingVertices"] for f in v["collisionAudit"].values() for i in f.values()),
      "minimumMm": min(i["minimumSignedClearanceM"] for f in v["collisionAudit"].values() for i in f.values()) * 1000,
      "status": v["technicalStatus"]} for v in variants]}, sort_keys=True))
