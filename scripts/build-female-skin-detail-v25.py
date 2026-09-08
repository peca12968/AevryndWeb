import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v21.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v25.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v25.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v25-lod1.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "skin-detail-v25"


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def gaussian(x, center, radius):
    delta = (x - center) / radius
    return math.exp(-0.5 * delta * delta)


def zone(co, x, z, rx, rz):
    return gaussian(abs(co.x), x, rx) * gaussian(co.z, z, rz)


def update_skin_tone(body):
    attribute = body.data.color_attributes.get("AevryndSkinTone")
    if not attribute:
        attribute = body.data.color_attributes.new(
            name="AevryndSkinTone", type="BYTE_COLOR", domain="POINT"
        )
    changed = 0
    face_vertices = 0
    for index, vertex in enumerate(body.data.vertices):
        co = vertex.co
        # Low amplitude deterministic variation prevents a perfectly uniform mannequin surface.
        grain = 0.006 * math.sin(co.x * 913.0 + co.y * 571.0 + co.z * 733.0)
        r = 0.992 + grain
        g = 0.992 + grain
        b = 0.992 + grain
        front = clamp((-co.y - 0.020) / 0.085)
        face = front * clamp((co.z - 1.405) / 0.075) * clamp((1.675 - co.z) / 0.075)
        if face > 0.001:
            face_vertices += 1
            cheek = zone(co, 0.047, 1.535, 0.024, 0.032) * face
            nose = gaussian(co.x, 0.0, 0.021) * gaussian(co.z, 1.545, 0.042) * face
            under_eye = zone(co, 0.034, 1.585, 0.021, 0.015) * face
            temple = zone(co, 0.072, 1.585, 0.020, 0.035) * face
            chin = gaussian(co.x, 0.0, 0.038) * gaussian(co.z, 1.455, 0.022) * face
            # Warm blood-rich areas, a restrained cool under-eye zone, and temple variation.
            g -= 0.047 * cheek + 0.026 * nose + 0.017 * chin
            b -= 0.066 * cheek + 0.040 * nose + 0.023 * chin
            r -= 0.030 * under_eye + 0.012 * temple
            g -= 0.016 * under_eye + 0.010 * temple
            b -= 0.006 * under_eye
        rgba = (clamp(r), clamp(g), clamp(b), 1.0)
        previous = tuple(attribute.data[index].color_srgb)
        attribute.data[index].color_srgb = rgba
        if max(abs(previous[channel] - rgba[channel]) for channel in range(3)) > 1e-4:
            changed += 1
    return changed, face_vertices


def update_skin_shader(material):
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = nodes["Principled BSDF"]
    normal_map = nodes["Aevrynd Runtime Normal Map"]
    bump = nodes["Aevrynd Skin Micro Bump"]
    micro = nodes["Aevrynd Skin Microstructure"]
    roughness_image = nodes["Aevrynd Runtime Roughness"]

    micro.inputs["Scale"].default_value = 235.0
    micro.inputs["Detail"].default_value = 4.0
    micro.inputs["Roughness"].default_value = 0.67
    bump.inputs["Strength"].default_value = 0.18
    bump.inputs["Distance"].default_value = 0.000095

    for link in list(bsdf.inputs["Normal"].links):
        links.remove(link)
    for link in list(bump.inputs["Normal"].links):
        links.remove(link)
    links.new(normal_map.outputs["Normal"], bump.inputs["Normal"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    roughness_noise = nodes.get("Aevrynd Pore Roughness v25") or nodes.new("ShaderNodeTexNoise")
    roughness_noise.name = "Aevrynd Pore Roughness v25"
    roughness_noise.inputs["Scale"].default_value = 145.0
    roughness_noise.inputs["Detail"].default_value = 2.7
    roughness_noise.inputs["Roughness"].default_value = 0.62
    map_range = nodes.get("Aevrynd Roughness Range v25") or nodes.new("ShaderNodeMapRange")
    map_range.name = "Aevrynd Roughness Range v25"
    map_range.inputs["From Min"].default_value = 0.0
    map_range.inputs["From Max"].default_value = 1.0
    map_range.inputs["To Min"].default_value = -0.045
    map_range.inputs["To Max"].default_value = 0.050
    add = nodes.get("Aevrynd Roughness Add v25") or nodes.new("ShaderNodeMath")
    add.name = "Aevrynd Roughness Add v25"
    add.operation = "ADD"
    add.use_clamp = True
    for link in list(bsdf.inputs["Roughness"].links):
        links.remove(link)
    links.new(roughness_noise.outputs["Factor"], map_range.inputs["Value"])
    links.new(roughness_image.outputs["Color"], add.inputs[0])
    links.new(map_range.outputs["Result"], add.inputs[1])
    links.new(add.outputs[0], bsdf.inputs["Roughness"])

    bsdf.inputs["Subsurface Weight"].default_value = 0.075
    bsdf.inputs["Subsurface Scale"].default_value = 0.0032
    bsdf.inputs["Specular IOR Level"].default_value = 0.22
    bsdf.inputs["Coat Weight"].default_value = 0.008
    return {
        "micro_scale": micro.inputs["Scale"].default_value,
        "bump_strength": bump.inputs["Strength"].default_value,
        "bump_distance": bump.inputs["Distance"].default_value,
        "subsurface_weight": bsdf.inputs["Subsurface Weight"].default_value,
    }


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target, lens=92):
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.data.lens = lens
    camera.location = location
    look_at(camera, target)
    for obj in bpy.data.objects:
        if obj.get("aevrynd_role") == "cornea":
            obj.hide_render = False
    bpy.ops.render.render(write_still=True)


def export_runtime(path, rig, excluded=()):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.data.objects:
        if obj.type in {"MESH", "ARMATURE"} and obj.name not in excluded:
            obj.hide_render = False
            obj.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format="GLB", use_selection=True,
        export_apply=True, export_yup=True, export_extras=True,
        export_animations=True, export_frame_range=True,
        export_attributes=True, export_vertex_color="ACTIVE",
    )


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
bpy.context.scene.frame_set(1)
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BUILD.parent.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]
rig = bpy.data.objects["AevryndFemaleRig"]
changed_vertices, face_vertices = update_skin_tone(body)
shader = update_skin_shader(bpy.data.materials["Aevrynd_Skin_Clay"])
bpy.context.scene["aevrynd_skin_revision"] = 25
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))

camera = bpy.data.objects["Aevrynd Review Camera"]
render(camera, "female-skin-front", (0.0, -0.67, 1.565), (0.0, -0.004, 1.555))
render(camera, "female-skin-three-quarter", (0.25, -0.60, 1.57), (0.0, 0.0, 1.55))
render(camera, "female-skin-side", (0.62, -0.05, 1.57), (0.0, 0.0, 1.545))
render(camera, "female-skin-neck", (0.15, -0.59, 1.48), (0.0, -0.005, 1.48))

multires = next(modifier for modifier in body.modifiers if modifier.type == "MULTIRES")
old_levels = (multires.levels, multires.sculpt_levels, multires.render_levels)
multires.levels = multires.sculpt_levels = multires.render_levels = 0
export_runtime(BUILD, rig)
export_runtime(LOD1, rig, {"HairMain", "HairFlyaways"})
multires.levels, multires.sculpt_levels, multires.render_levels = old_levels

print("AEVRYND_SKIN_DETAIL_V25_REPORT=" + json.dumps({
    "state": "AUTHORING",
    "changed_vertices": changed_vertices,
    "face_vertices": face_vertices,
    "shader": shader,
    "runtime_glb": str(BUILD),
    "lod1_glb": str(LOD1),
}))
