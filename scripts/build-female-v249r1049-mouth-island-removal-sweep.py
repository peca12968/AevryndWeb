"""Remove proven detached mouth islands before rebuilding the inner lip."""

import json
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-depth-cleanup-r1046-study.blend"
COMPONENTS = ASSETS / "female-v249-mainline-r1049-mouth-face-components.inspect.json"
BOUNDARIES = ASSETS / "female-v249-mainline-r1048-removal-boundaries.inspect.json"
REPORT = ASSETS / "female-v249-mainline-r1049-mouth-island-removal-sweep.study.json"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "v249r1049-mouth-island-removal-sweep"
BODY = "AevryndFemaleCC0Baseline_v259"
VARIANTS = (
    ("a-central5", (143, 144, 146, 149, 150)),
    ("b-central6", (84, 143, 144, 146, 149, 150)),
    ("c-central-side", (20, 21, 22, 23, 24, 25, 84, 143, 144, 146, 149, 150)),
    ("d-all-small-mouth", tuple(range(10, 26)) + (84, 143, 144, 146, 149, 150)),
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


component_report = json.loads(COMPONENTS.read_text(encoding="utf-8"))
by_index = {item["component"]: item for item in component_report["components"]}
strip = set(json.loads(BOUNDARIES.read_text(encoding="utf-8"))["stripFaces"])
RENDER_DIR.mkdir(parents=True, exist_ok=True)
variants = []
for label, component_ids in VARIANTS:
    island_faces = {face for component in component_ids for face in by_index[component]["faceIndices"]}
    removed = strip | island_faces
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    scene.frame_set(1)
    body = bpy.data.objects[BODY]
    delete_faces(body, removed)
    for obj in scene.objects:
        name = obj.name.lower()
        if obj.type == "CURVES" or any(token in name for token in ("groom", "scalp", "haircard", "hairfiber")):
            if not any(token in name for token in ("brow", "lash")):
                obj.hide_render = True
    renders = [render(scene, f"{label}-neutral"), render(scene, f"{label}-mouth-open", "open"), render(scene, f"{label}-smile", "smile")]
    variants.append({
        "label": label,
        "removedComponents": list(component_ids),
        "removedStripFaces": len(strip),
        "removedIslandFaces": len(island_faces),
        "totalRemovedFaces": len(removed),
        "renders": renders,
        "status": "VISUAL_DIAGNOSTIC",
    })

report = {
    "revision": "v249r1049-mouth-island-removal-sweep",
    "source": str(SOURCE),
    "componentInspection": str(COMPONENTS),
    "method": "remove eight main-component strip faces plus successively broader sets of genuinely face-disconnected internal islands",
    "variants": variants,
    "websitePromotionApproved": False,
    "status": "PENDING_STRICT_VISUAL_REVIEW",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1049_ISLANDS=" + json.dumps({"variants": [{"label": item["label"], "islandFaces": item["removedIslandFaces"], "total": item["totalRemovedFaces"]} for item in variants]}, sort_keys=True))
