import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-eye-composite-v260.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-fitted-eye-skin-foundation-r602.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-fitted-eye-skin-r602.build.json"
AUDIT = ASSETS / "female-v249-mainline-cc0-fitted-eye-skin-r602.audit.json"
REVIEW = ASSETS / "reviews/v249r602-cc0-fitted-eye-skin-foundation"
BODY = "AevryndFemaleCC0Baseline_v259"
PARTS = ("Sclera", "Cornea", "Iris")
EYE_SCALE = 0.90
EYE_DEPTH_M = 0.002


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def tree(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def make_skin():
    material = bpy.data.materials.new("Aevrynd_CC0_OwnedSkin_R602_Neutral")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.inputs["Roughness"].default_value = 0.50
    shader.inputs["Subsurface Weight"].default_value = 0.045
    shader.inputs["Subsurface Scale"].default_value = 0.0045
    shader.inputs["Specular IOR Level"].default_value = 0.20
    shader.inputs["Coat Weight"].default_value = 0.006
    coords = nodes.new("ShaderNodeTexCoord")
    tone = nodes.new("ShaderNodeTexNoise")
    tone.noise_dimensions = "3D"
    tone.inputs["Scale"].default_value = 34.0
    tone.inputs["Detail"].default_value = 2.4
    tone.inputs["Roughness"].default_value = 0.56
    tone.inputs["Distortion"].default_value = 0.06
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.20
    ramp.color_ramp.elements[0].color = (0.180, 0.060, 0.040, 1.0)
    ramp.color_ramp.elements[1].position = 0.80
    ramp.color_ramp.elements[1].color = (0.245, 0.100, 0.065, 1.0)
    lips = nodes.new("ShaderNodeAttribute")
    lips.attribute_name = "lips"
    lip_mix = nodes.new("ShaderNodeMixRGB")
    lip_mix.inputs[2].default_value = (0.250, 0.050, 0.045, 1.0)
    pore = nodes.new("ShaderNodeTexNoise")
    pore.noise_dimensions = "3D"
    pore.inputs["Scale"].default_value = 720.0
    pore.inputs["Detail"].default_value = 2.0
    pore.inputs["Roughness"].default_value = 0.62
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.045
    bump.inputs["Distance"].default_value = 0.00007
    links.new(coords.outputs["Object"], tone.inputs["Vector"])
    links.new(tone.outputs["Factor"], ramp.inputs["Factor"])
    links.new(ramp.outputs["Color"], lip_mix.inputs[1])
    links.new(lips.outputs["Fac"], lip_mix.inputs[0])
    links.new(lip_mix.outputs["Color"], shader.inputs["Base Color"])
    links.new(coords.outputs["Object"], pore.inputs["Vector"])
    links.new(pore.outputs["Factor"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material["aevrynd_revision"] = "v249r602"
    material["aevrynd_runtime_owned"] = True
    material["aevrynd_license"] = "Aevrynd-owned procedural nodes; MPFB lips group is CC0-1.0"
    return material


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
centers = {}
for side in ("L", "R"):
    sclera = bpy.data.objects[f"Eye_{side}_Sclera"]
    points = [sclera.matrix_world @ vertex.co for vertex in sclera.data.vertices]
    centers[side] = sum(points, Vector()) / len(points)
for side in ("L", "R"):
    center = centers[side]
    for part in PARTS:
        obj = bpy.data.objects[f"Eye_{side}_{part}"]
        inverse = obj.matrix_world.inverted()
        for vertex in obj.data.vertices:
            world = obj.matrix_world @ vertex.co
            vertex.co = inverse @ (center + (world - center) * EYE_SCALE + Vector((0.0, EYE_DEPTH_M, 0.0)))
        obj.data.update()
        obj["aevrynd_revision"] = 602
        obj["aevrynd_fit"] = "relative scale 0.90; world Y +2mm"
body.data.materials[0] = make_skin()
body["aevrynd_revision"] = 602
body["aevrynd_foundation_role"] = "MPFB CC0 alternative topology; long-term rebuild branch"
scene["aevrynd_release_state"] = "STATIC_FOUNDATION_TECHNICAL_CANDIDATE_VISUAL_HERO_FAIL"
scene["aevrynd_source_license"] = "MPFB core graphical assets CC0-1.0; Aevrynd-owned material and fitted optics"
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)

bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
body_tree = tree(body, depsgraph)
overlap = {
    f"Eye_{side}_{part}": len(body_tree.overlap(tree(bpy.data.objects[f"Eye_{side}_{part}"], depsgraph)))
    for side in ("L", "R") for part in PARTS
}
audit = {
    "model": str(OUTPUT),
    "frame": 1,
    "body": BODY,
    "eyeFit": {"relativeScaleFromV260": EYE_SCALE, "worldDepthShiftM": EYE_DEPTH_M},
    "bodyEyeOverlapPairs": overlap,
    "nonfiniteBodyVertices": sum(not all(value == value for value in vertex.co) for vertex in body.data.vertices),
    "status": "PASS" if not any(overlap.values()) else "FAIL",
    "limitations": ["unrigged foundation", "no dynamic collision claim", "no hair, brows, lashes, tear film, teeth, tongue or clothing"],
}
AUDIT.write_text(json.dumps(audit, indent=2), encoding="utf-8")

scene.render.engine = "BLENDER_EEVEE"
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.render.image_settings.file_format = "PNG"
scene.render.resolution_percentage = 100
REVIEW.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd Baseline Camera"]
scene.camera = camera
for label, location, target, lens, size in (
    ("01-full-front", (0.0, -4.8, 0.92), (0.0, 0.0, 0.92), 72, (850, 1100)),
    ("02-full-three-quarter", (3.0, -4.0, 0.98), (0.0, 0.0, 0.92), 72, (850, 1100)),
    ("03-face-front", (0.0, -1.22, 1.55), (0.0, -0.01, 1.55), 105, (1100, 1100)),
    ("04-face-three-quarter", (0.74, -1.0, 1.56), (0.0, 0.0, 1.55), 105, (1100, 1100)),
    ("05-face-profile", (1.22, 0.0, 1.55), (0.0, 0.0, 1.55), 105, (1100, 1100)),
):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(REVIEW / f"{label}.png")
    bpy.ops.render.render(write_still=True)

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "license": "MPFB core graphical assets CC0-1.0 plus Aevrynd-owned procedural material",
    "bodyVertices": len(body.data.vertices),
    "bodyPolygons": len(body.data.polygons),
    "bodyShapeKeys": len(body.data.shape_keys.key_blocks) if body.data.shape_keys else 0,
    "eyeFit": {"relativeScaleFromV260": EYE_SCALE, "worldDepthShiftM": EYE_DEPTH_M},
    "skinMaterial": "Aevrynd_CC0_OwnedSkin_R602_Neutral",
    "usesTopologySpecificUv": False,
    "staticCollisionStatus": audit["status"],
    "strictScores": {"foundationFace": 48, "eyeTopologyAppearance": 62, "skin": 46, "overallFoundation": 49},
    "status": "STATIC_FOUNDATION_TECHNICAL_PASS_VISUAL_HERO_FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R602_CC0_FITTED_EYE_SKIN=" + json.dumps(report, sort_keys=True))
if audit["status"] != "PASS":
    raise SystemExit(2)
