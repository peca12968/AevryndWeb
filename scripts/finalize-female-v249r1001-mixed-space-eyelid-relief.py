"""Select r1000 strength 1.0 and validate the r1001 eyelid candidate."""

import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-mixed-space-eyelid-relief-r1000-study.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-mixed-space-eyelid-relief-r1001.blend"
AUDIT = ASSETS / "female-v249-mainline-cc0-mixed-space-eyelid-relief-r1001.collision-audit.json"
REVIEW_DIR = ROOT.parent / "Temp/female-realism/v249r1001-mixed-space-eyelid-relief"
BODY = "AevryndFemaleCC0Baseline_v259"
KEY = "Aevrynd_MixedSpaceEyelidRelief_R1000"
FRAMES = (1, 20, 33, 61)


def world_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def overlap(a, b):
    return len(world_tree(a).overlap(world_tree(b)))


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
body = bpy.data.objects[BODY]
key = body.data.shape_keys.key_blocks[KEY]
key.value = 1.0
bpy.context.view_layer.update()

frames = {}
failures = []
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    body_tree = world_tree(body)
    frame_result = {}
    for side in ("L", "R"):
        sclera = bpy.data.objects[f"Eye_{side}_Sclera"]
        cornea = bpy.data.objects[f"Eye_{side}_Cornea"]
        upper = bpy.data.objects[f"Eye_{side}_UpperLashes"]
        lower = bpy.data.objects[f"Eye_{side}_LowerLashes"]
        values = {
            "bodySclera": len(body_tree.overlap(world_tree(sclera))),
            "bodyCornea": len(body_tree.overlap(world_tree(cornea))),
            "bodyUpperLashes": len(body_tree.overlap(world_tree(upper))),
            "bodyLowerLashes": len(body_tree.overlap(world_tree(lower))),
            "upperSclera": overlap(upper, sclera),
            "lowerSclera": overlap(lower, sclera),
            "upperCornea": overlap(upper, cornea),
            "lowerCornea": overlap(lower, cornea),
            "upperLower": overlap(upper, lower),
        }
        frame_result[side] = values
        for layer, count in values.items():
            if count:
                failures.append({"frame": frame, "side": side, "pair": layer, "triangleOverlaps": count})
    frames[str(frame)] = frame_result

REVIEW_DIR.mkdir(parents=True, exist_ok=True)
scene.render.resolution_x = scene.render.resolution_y = 900
camera = scene.camera
camera.data.lens = 105
views = (
    ("front", 1, (0.0, -0.48, 1.485), (0.0, -0.060, 1.485)),
    ("three-quarter-left", 1, (0.155, -0.445, 1.485), (0.0, -0.060, 1.480)),
    ("three-quarter-right", 1, (-0.155, -0.445, 1.485), (0.0, -0.060, 1.480)),
    ("profile-left", 1, (0.315, -0.250, 1.482), (0.0, -0.060, 1.478)),
    ("profile-right", 1, (-0.315, -0.250, 1.482), (0.0, -0.060, 1.478)),
    ("front-frame20", 20, (0.0, -0.48, 1.485), (0.0, -0.060, 1.485)),
)
rendered = []
for label, frame, location, target in views:
    scene.frame_set(frame)
    camera.location = location
    look_at(camera, target)
    path = REVIEW_DIR / f"r1001-{label}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    rendered.append(str(path))

scene.frame_set(1)
key.value = 1.0
scene["aevrynd_mainline_revision"] = "v249r1001-mixed-space-eyelid-relief"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "TECHNICAL_CANDIDATE_VISUAL_HERO_FAIL"
scene["aevrynd_website_promotion"] = "forbidden"
scene["aevrynd_selected_eyelid_relief_strength"] = 1.0
report = {
    "source": str(SOURCE),
    "model": str(OUTPUT),
    "shapeKey": KEY,
    "selectedStrength": 1.0,
    "frames": frames,
    "failures": failures,
    "rendered": rendered,
    "status": "PASS" if not failures else "FAIL",
}
AUDIT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R1001_MIXED_SPACE_EYELID_RELIEF=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
