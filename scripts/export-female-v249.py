from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249.blend"
OUTPUT = ROOT / ".character-build/aevrynd-female-authoring-v249.glb"

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action="DESELECT")
selected = []
for obj in bpy.context.scene.objects:
    if obj.type == "ARMATURE" and obj.name == "AevryndFemaleRig":
        obj.hide_viewport = False
        obj.hide_set(False)
        obj.select_set(True)
        selected.append(obj.name)
    elif obj.type == "MESH" and not obj.hide_render and not obj.get("aevrynd_runtime_exclude"):
        obj.hide_viewport = False
        obj.hide_set(False)
        obj.select_set(True)
        selected.append(obj.name)

bpy.context.view_layer.objects.active = bpy.data.objects["AevryndFemaleRig"]
bpy.ops.export_scene.gltf(
    filepath=str(OUTPUT),
    export_format="GLB",
    use_selection=True,
    export_apply=True,
    export_yup=True,
    export_extras=True,
    export_animations=True,
    export_frame_range=True,
    export_attributes=True,
    export_vertex_color="ACTIVE",
)
print(f"AEVRYND_V249_EXPORT path={OUTPUT} bytes={OUTPUT.stat().st_size} objects={len(selected)} names={selected}")









