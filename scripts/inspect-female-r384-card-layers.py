import bpy


bpy.ops.wm.open_mainfile(
    filepath=r"D:\Download\Aevrynd\sites-engine-journey\assets-source\aevrynd-character\aevrynd-female-authoring-v249-mainline-runtime-card-bake-r384.blend"
)
for obj in bpy.context.scene.objects:
    text = " ".join((obj.name, str(obj.get("aevrynd_layer", "")))).lower()
    if "hair" not in text and "scalp" not in text:
        continue
    materials = []
    if getattr(obj, "data", None) and hasattr(obj.data, "materials"):
        materials = [material.name for material in obj.data.materials if material]
    print(
        "R384_LAYER",
        obj.name,
        obj.type,
        "visible", not obj.hide_render,
        "layer", obj.get("aevrynd_layer", ""),
        "materials", materials,
    )
    for material in getattr(getattr(obj, "data", None), "materials", []):
        if not material or not material.use_nodes:
            continue
        for node in material.node_tree.nodes:
            if node.bl_idname != "ShaderNodeBsdfPrincipled":
                continue
            print(
                "R384_SHADER",
                material.name,
                "base", tuple(node.inputs["Base Color"].default_value),
                "roughness", node.inputs["Roughness"].default_value,
                "specular", node.inputs["Specular IOR Level"].default_value,
                "alpha", node.inputs["Alpha"].default_value,
            )
