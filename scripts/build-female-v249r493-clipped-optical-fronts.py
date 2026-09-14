import bmesh
import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-eye-aperture-r492.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-clipped-optical-fronts-r493.blend"
REPORT = ASSETS / "female-v249-mainline-clipped-optical-fronts-r493.build-report.json"
REVIEW_DIR = ASSETS / "reviews/v249r493-clipped-optical-fronts"
BODY = "AevryndFemaleBodyBaseV118"
CLIPPED = tuple(f"Eye_{side}_{part}" for side in ("L", "R") for part in ("Cornea", "Sclera"))


def geometry(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return points, faces


def tree(obj, depsgraph):
    points, faces = geometry(obj, depsgraph)
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, frame, name, location, target, lens, size):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(REVIEW_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
overlap_faces = {name: set() for name in CLIPPED}
overlap_by_frame = {}
for frame in (1, 20):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = tree(bpy.data.objects[BODY], depsgraph)
    overlap_by_frame[str(frame)] = {}
    for name in CLIPPED:
        pairs = body_tree.overlap(tree(bpy.data.objects[name], depsgraph))
        indices = {eye_face for _body_face, eye_face in pairs}
        overlap_faces[name].update(indices)
        overlap_by_frame[str(frame)][name] = len(indices)

removed = {}
scene.frame_set(1)
for name in CLIPPED:
    obj = bpy.data.objects[name]
    obj.data = obj.data.copy()
    before_faces = len(obj.data.polygons)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    doomed = [bm.faces[index] for index in sorted(overlap_faces[name])]
    bmesh.ops.delete(bm, geom=doomed, context="FACES")
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    obj["aevrynd_revision"] = "v249r493-clipped-optical-front"
    obj["aevrynd_removed_intersecting_faces"] = len(overlap_faces[name])
    obj["aevrynd_clip_frames"] = "1,20"
    removed[name] = {
        "beforeFaces": before_faces,
        "removedFaces": len(overlap_faces[name]),
        "afterFaces": len(obj.data.polygons),
        "removedOriginalFaceIndices": sorted(overlap_faces[name]),
    }

scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.image_settings.file_format = "PNG"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
for values in (
    (1, "01-eye-close-f01", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700)),
    (1, "02-face-front-f01", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000)),
    (1, "03-three-quarter-f01", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84, (1000, 1000)),
    (1, "04-profile-f01", (0.68, -0.05, 1.61), (0.0, -0.01, 1.595), 88, (1000, 1000)),
    (20, "05-eye-close-f20", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700)),
):
    render(scene, camera, *values)

scene.frame_set(1)
scene["aevrynd_mainline_revision"] = "v249r493-clipped-optical-fronts"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "CLIPPED_OPTICAL_VISUAL_CANDIDATE_COLLISION_AUDIT_REQUIRED"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "method": "remove only cornea and sclera faces that geometrically cross the continuous eyelids at frame 1 or 20; retain iris, pupil, materials and object transforms",
    "overlapFacesBeforeClip": overlap_by_frame,
    "removed": removed,
    "reviewDirectory": str(REVIEW_DIR),
    "collisionGate": "PENDING_FORMAL_AUDIT",
    "visualGate": "PENDING_STRICT_REVIEW",
    "websitePromotionApproved": False,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R493_CLIPPED_OPTICAL_FRONTS=" + json.dumps({
    "output": str(OUTPUT),
    "removed": {name: data["removedFaces"] for name, data in removed.items()},
    "status": "VISUAL_AND_COLLISION_REVIEW_REQUIRED",
}, sort_keys=True))
