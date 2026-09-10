import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-scalp-foundation-r101.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r101-eye-optics-r108-sweep"
VARIANTS = (
    ("a-control", False, False, False),
    ("b-no-fake-catchlight", True, False, False),
    ("c-no-overlay-helpers", True, True, False),
    ("d-physical-optics", True, True, True),
)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    lower = obj.name.lower()
    return layer.startswith("hair.") or any(token in lower for token in ("hair", "groom", "scalp"))


def bsdf(material):
    return next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")


def tune_materials():
    sclera = bpy.data.materials["Aevrynd_Eye_Sclera"]
    sclera_bsdf = bsdf(sclera)
    image = next(node for node in sclera.node_tree.nodes if node.bl_idname == "ShaderNodeTexImage")
    for link in list(sclera.node_tree.links):
        if link.to_node == sclera_bsdf and link.to_socket.name == "Base Color":
            sclera.node_tree.links.remove(link)
    tone = sclera.node_tree.nodes.new("ShaderNodeHueSaturation")
    tone.name = "Aevrynd Sclera OffWhite R108"
    tone.inputs["Saturation"].default_value = 0.72
    tone.inputs["Value"].default_value = 0.86
    sclera.node_tree.links.new(image.outputs["Color"], tone.inputs["Color"])
    sclera.node_tree.links.new(tone.outputs["Color"], sclera_bsdf.inputs["Base Color"])
    sclera_bsdf.inputs["Roughness"].default_value = 0.44
    sclera_bsdf.inputs["Coat Weight"].default_value = 0.025

    iris = bpy.data.materials["Aevrynd_Eye_Iris"]
    iris_tone = next(node for node in iris.node_tree.nodes if node.bl_idname == "ShaderNodeHueSaturation")
    iris_tone.inputs["Saturation"].default_value = 0.84
    iris_tone.inputs["Value"].default_value = 1.28
    iris_bsdf = bsdf(iris)
    iris_bsdf.inputs["Roughness"].default_value = 0.42
    iris_bsdf.inputs["Specular IOR Level"].default_value = 0.12

    cornea = bpy.data.materials["Aevrynd_Eye_Cornea"]
    cornea_bsdf = bsdf(cornea)
    cornea_bsdf.inputs["Base Color"].default_value = (0.965, 0.985, 1.0, 1.0)
    cornea_bsdf.inputs["Roughness"].default_value = 0.018
    cornea_bsdf.inputs["IOR"].default_value = 1.376
    cornea_bsdf.inputs["Transmission Weight"].default_value = 1.0
    cornea_bsdf.inputs["Alpha"].default_value = 0.16
    cornea_bsdf.inputs["Specular IOR Level"].default_value = 0.50
    cornea.surface_render_method = "DITHERED"

    return {
        "sclera_value": 0.86,
        "iris_value": 1.28,
        "cornea_alpha": 0.16,
        "cornea_ior": 1.376,
    }


def render(camera, name, location, target, lens, size):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    for label, hide_catchlight, hide_tear, tune in VARIANTS:
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
        scene = bpy.context.scene
        scene.frame_set(1)
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        hidden = []
        for obj in bpy.data.objects:
            if is_hair(obj):
                obj.hide_render = True
            if hide_catchlight and "Catchlight" in obj.name:
                obj.hide_render = True
                hidden.append(obj.name)
            if hide_tear and "TearMeniscus" in obj.name:
                obj.hide_render = True
                hidden.append(obj.name)
        material_report = tune_materials() if tune else None
        camera = bpy.data.objects["Aevrynd Review Camera"]
        render(camera, f"{label}-01-eyes-front", (0.0, -0.445, 1.611), (0.0, -0.076, 1.608), 132, (1280, 760))
        render(camera, f"{label}-02-left-eye-three-quarter", (0.225, -0.390, 1.628), (0.018, -0.080, 1.607), 138, (1100, 900))
        render(camera, f"{label}-03-face-front", (0.0, -0.555, 1.605), (0.0, -0.058, 1.604), 116, (1050, 1050))
        report[label] = {"hidden": hidden, "materials": material_report}
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("AEVRYND_V249_R101_EYE_OPTICS_R108=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
