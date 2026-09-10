import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r31.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cloth-r35.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-cloth-r35"
OUT.mkdir(parents=True, exist_ok=True)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def woven_material(name, base_color, weave_scale, roughness, sheen):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (680, 40)
    shader = nodes.new("ShaderNodeBsdfPrincipled")
    shader.location = (400, 40)
    shader.inputs["Base Color"].default_value = (*base_color, 1.0)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Specular IOR Level"].default_value = 0.24
    shader.inputs["Sheen Weight"].default_value = sheen
    shader.inputs["Sheen Roughness"].default_value = 0.38

    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.location = (-720, 0)
    warp = nodes.new("ShaderNodeTexNoise")
    warp.location = (-510, 190)
    warp.noise_dimensions = "3D"
    warp.inputs["Scale"].default_value = 7.0
    warp.inputs["Detail"].default_value = 3.0
    warp.inputs["Roughness"].default_value = 0.65

    weave = nodes.new("ShaderNodeTexVoronoi")
    weave.location = (-260, 60)
    weave.voronoi_dimensions = "3D"
    weave.distance = "EUCLIDEAN"
    weave.feature = "DISTANCE_TO_EDGE"
    weave.inputs["Scale"].default_value = weave_scale

    bump = nodes.new("ShaderNodeBump")
    bump.location = (160, -120)
    bump.inputs["Strength"].default_value = 0.19
    bump.inputs["Distance"].default_value = 0.00014
    bump.invert = True

    variation = nodes.new("ShaderNodeMixRGB")
    variation.location = (110, 150)
    variation.blend_type = "MULTIPLY"
    variation.inputs[0].default_value = 0.16
    variation.inputs[1].default_value = (*base_color, 1.0)

    links.new(texcoord.outputs["Generated"], warp.inputs["Vector"])
    links.new(texcoord.outputs["Generated"], weave.inputs["Vector"])
    links.new(warp.outputs["Fac"], variation.inputs[2])
    links.new(variation.outputs["Color"], shader.inputs["Base Color"])
    links.new(weave.outputs["Distance"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    links.new(shader.outputs["BSDF"], output.inputs["Surface"])
    material["aevrynd_material_schema"] = "aevrynd.fabric.woven.v1"
    material["aevrynd_revision"] = "v249-mainline-cloth-r35"
    material["aevrynd_weave_scale"] = weave_scale
    return material


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
navy = woven_material("Aevrynd_Fabric_Navy_Woven_v249r35", (0.026, 0.095, 0.205), 310.0, 0.58, 0.18)
navy_binding = woven_material("Aevrynd_Fabric_Navy_Binding_v249r35", (0.018, 0.062, 0.135), 360.0, 0.61, 0.14)
charcoal = woven_material("Aevrynd_Fabric_Charcoal_Woven_v249r35", (0.035, 0.040, 0.052), 285.0, 0.64, 0.12)
navy_seam = woven_material("Aevrynd_Thread_Navy_v249r35", (0.052, 0.145, 0.275), 420.0, 0.70, 0.10)
charcoal_seam = woven_material("Aevrynd_Thread_Charcoal_v249r35", (0.070, 0.076, 0.090), 420.0, 0.72, 0.08)

assignments = {
    "Clothing_Bandeau_v160": navy,
    "Clothing_BandeauBinding_v162": navy_binding,
    "Clothing_BodyFitShorts_v135": charcoal,
    "Clothing_TopSeams_v139": navy_seam,
    "Clothing_ShortsSeams_v139": charcoal_seam,
    "Clothing_InnerTop": navy_binding,
    "Clothing_InnerShorts": charcoal,
}
for name, material in assignments.items():
    obj = bpy.data.objects[name]
    obj.data.materials.clear()
    obj.data.materials.append(material)
    obj["aevrynd_layer"] = str(obj.get("aevrynd_layer", "clothing"))
    obj["aevrynd_material_revision"] = "v249-mainline-cloth-r35"

scene["aevrynd_mainline_baseline"] = "v249"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_clothing_candidate"] = "v249-mainline-cloth-r35"
scene["aevrynd_release_state"] = "WOVEN_CLOTH_PENDING_STRICT_VISUAL_AND_COLLISION_REVIEW"
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("01-full-front", 1, (0.0, -4.0, 0.90), (0.0, 0.0, 0.86), 70, (900, 1200)),
    ("02-full-three-quarter", 1, (2.35, -3.30, 0.95), (0.0, 0.0, 0.86), 70, (900, 1200)),
    ("03-torso-front", 1, (0.0, -1.55, 1.16), (0.0, 0.0, 1.12), 78, (1000, 1000)),
    ("04-torso-three-quarter", 1, (0.92, -1.34, 1.17), (0.0, 0.0, 1.12), 78, (1000, 1000)),
    ("05-pose-front", 20, (0.0, -3.7, 0.98), (0.0, 0.0, 0.90), 70, (900, 1200)),
)
for name, frame, location, target, lens, resolution in views:
    scene.frame_set(frame)
    scene.render.resolution_x, scene.render.resolution_y = resolution
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "geometry_changed": False,
    "assignments": {name: material.name for name, material in assignments.items()},
    "layers": ["outer top", "top binding", "top seams", "inner top", "outer shorts", "shorts seams", "inner shorts"],
    "status": "STRICT_VISUAL_REVIEW_REQUIRED",
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_MAINLINE_CLOTH_R35=" + json.dumps(report, sort_keys=True))
