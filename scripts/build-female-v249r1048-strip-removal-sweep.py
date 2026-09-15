"""Render exact r1047 strip-face removal sets before attempting a welded bridge."""

import json
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-depth-cleanup-r1046-study.blend"
INSPECTION = ASSETS / "female-v249-mainline-r1048-removal-boundaries.inspect.json"
REPORT = ASSETS / "female-v249-mainline-r1048-strip-removal-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "v249r1048-strip-removal-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
VARIANTS = (
    ("a-strip8", "strip8"),
    ("b-strip8-rear", "strip8_plus_rear"),
    ("c-strip8-neighbors", "strip8_plus_interior_neighbors"),
    ("d-strip8-all", "strip8_plus_rear_and_interior_neighbors"),
)


def delete_faces(body, indices):
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(body.data)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[index] for index in sorted(indices)], context="FACES_ONLY")
    bmesh.update_edit_mesh(body.data, loop_triangles=True, destructive=True)
    bpy.ops.object.mode_set(mode="OBJECT")


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, label, expression=None):
    body = bpy.data.objects[BODY]
    keys = body.data.shape_keys.key_blocks
    keys["Aevrynd_MouthOpenTest_R1030"].value = 1.0 if expression == "open" else 0.0
    keys["Aevrynd_SmileTest_R1030"].value = 1.0 if expression == "smile" else 0.0
    camera = scene.camera
    camera.location = (0.0, -0.43, 1.388)
    camera.data.lens = 135
    look_at(camera, (0.0, -0.105, 1.386))
    scene.render.resolution_x, scene.render.resolution_y = 1200, 700
    scene.render.resolution_percentage = 100
    path = RENDER_DIR / f"{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    keys["Aevrynd_MouthOpenTest_R1030"].value = 0.0
    keys["Aevrynd_SmileTest_R1030"].value = 0.0
    return str(path)


inspection = json.loads(INSPECTION.read_text(encoding="utf-8"))
RENDER_DIR.mkdir(parents=True, exist_ok=True)
variants = []
for label, source_set in VARIANTS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    body = bpy.data.objects[BODY]
    faces = inspection["variants"][source_set]["removedFaces"]
    delete_faces(body, faces)
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")):
                obj.hide_render = True
    renders = [render(scene, f"{label}-neutral"), render(scene, f"{label}-mouth-open", "open"), render(scene, f"{label}-smile", "smile")]
    variants.append({"label": label, "sourceSet": source_set, "removedFaces": faces, "renders": renders, "status": "VISUAL_DIAGNOSTIC"})

report = {
    "revision": "v249r1048-strip-removal-sweep",
    "source": str(SOURCE),
    "inspection": str(INSPECTION),
    "variants": variants,
    "websitePromotionApproved": False,
    "status": "PENDING_STRICT_VISUAL_REVIEW",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1048_REMOVAL=" + json.dumps({"variants": [{"label": item["label"], "removed": len(item["removedFaces"])} for item in variants]}, sort_keys=True))
