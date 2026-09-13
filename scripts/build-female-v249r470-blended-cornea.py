import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-iris-r469-study.blend"
OUTPUT = ASSETS / "aevrynd-female-authoring-v249-mainline-clean-cornea-r470.blend"
REPORT = ASSETS / "female-v249-mainline-clean-cornea-r470.build-report.json"
REVIEW_DIR = ASSETS / "reviews/v249r470-clean-cornea"
EYE_OBJECTS = tuple(
    f"Eye_{side}_{part}"
    for side in ("L", "R")
    for part in ("Caruncle", "Cornea", "Iris", "Pupil", "Sclera", "TearMeniscus", "UpperLashes")
)


def mesh_hash(obj):
    digest = hashlib.sha256()
    for vertex in obj.data.vertices:
        digest.update(("%.9f,%.9f,%.9f;" % tuple(vertex.co)).encode())
    for polygon in obj.data.polygons:
        digest.update((",".join(map(str, polygon.vertices)) + ";").encode())
    return digest.hexdigest()


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, frame, name, location, target, lens, size):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(REVIEW_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
before_hashes = {name: mesh_hash(bpy.data.objects[name]) for name in EYE_OBJECTS}

source_material = bpy.data.materials["Aevrynd_Eye_Cornea_v249r175"]
material = source_material.copy()
material.name = "Aevrynd_Eye_Cornea_ClearBlend_R470"
material.surface_render_method = "BLENDED"
material.use_transparency_overlap = False
material["aevrynd_revision"] = "v249r470"
material["aevrynd_layer"] = "eye.cornea.clear_transmission"
material["aevrynd_change"] = "replace stochastic dithered alpha presentation with sorted blend; optical inputs unchanged"
nodes = material.node_tree.nodes
links = material.node_tree.links
shader = next(node for node in nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
output = next(node for node in nodes if node.bl_idname == "ShaderNodeOutputMaterial")
for link in list(output.inputs["Surface"].links):
    links.remove(link)
links.new(shader.outputs["BSDF"], output.inputs["Surface"])
shader.inputs["Base Color"].default_value = (0.93, 0.97, 1.0, 1.0)
shader.inputs["Roughness"].default_value = 0.024
shader.inputs["Specular IOR Level"].default_value = 0.50
shader.inputs["Coat Weight"].default_value = 0.28
shader.inputs["Transmission Weight"].default_value = 1.0
shader.inputs["Alpha"].default_value = 0.14
for name in ("Eye_L_Cornea", "Eye_R_Cornea"):
    obj = bpy.data.objects[name]
    obj.data.materials.clear()
    obj.data.materials.append(material)
    obj["aevrynd_revision"] = "v249r470"

after_hashes = {name: mesh_hash(bpy.data.objects[name]) for name in EYE_OBJECTS}
geometry_unchanged = before_hashes == after_hashes

scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
REVIEW_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects["Aevrynd Review Camera"]
scene.camera = camera
views = (
    (1, "01-eye-close-f01", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700)),
    (1, "02-front-f01", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88, (1000, 1000)),
    (1, "03-three-quarter-f01", (0.45, -0.66, 1.60), (0.0, -0.005, 1.56), 84, (1000, 1000)),
    (20, "04-eye-close-f20", (0.0, -0.49, 1.615), (0.0, -0.13, 1.610), 105, (1200, 700)),
)
for values in views:
    render(scene, camera, *values)

scene.frame_set(1)
scene["aevrynd_mainline_revision"] = "v249r470-clean-cornea"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "EYE_MATERIAL_TECHNICAL_CANDIDATE_COLLISION_AUDIT_REQUIRED"
scene["aevrynd_eye_layers"] = "sclera|iris_stroma|cornea|tear_meniscus|caruncle|upper_lashes"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "changedMaterial": material.name,
    "surfaceRenderMethodBefore": source_material.surface_render_method,
    "surfaceRenderMethodAfter": material.surface_render_method,
    "opticalInputs": {
        "roughness": 0.024,
        "specularIorLevel": 0.50,
        "coatWeight": 0.28,
        "transmissionWeight": 1.0,
        "alpha": 0.14,
    },
    "eyeGeometryHashesBefore": before_hashes,
    "eyeGeometryHashesAfter": after_hashes,
    "eyeGeometryUnchanged": geometry_unchanged,
    "renderDirectory": str(REVIEW_DIR),
    "status": "GEOMETRY_PARITY_PASS_COLLISION_AUDIT_REQUIRED" if geometry_unchanged else "FAIL_GEOMETRY_CHANGED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R470_CORNEA=" + json.dumps({"output": str(OUTPUT), "geometryUnchanged": geometry_unchanged}, sort_keys=True))
if not geometry_unchanged:
    raise SystemExit(2)
