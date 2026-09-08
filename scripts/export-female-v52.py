from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v52.blend"
FULL = ROOT / ".character-build" / "aevrynd-female-authoring-v52.glb"
LOD1 = ROOT / ".character-build" / "aevrynd-female-authoring-v52-lod1.glb"
LOD_EXCLUDED = {
    "HairMain", "HairFlyaways", "HairGuides", "HairClumpsMediumCards", "HairlineBaby",
    "HairTempleClumps", "HairNapeClumps", "HairBoundaryClumps", "HairUndercutScalp",
    "Brow_L_Density", "Brow_R_Density",
    "Eye_L_Catchlight", "Eye_R_Catchlight", "Eye_L_IrisFibers", "Eye_R_IrisFibers",
    "Eye_L_LimbalRing", "Eye_R_LimbalRing", "Eye_L_TearMeniscus", "Eye_R_TearMeniscus",
    "Eye_L_Caruncle", "Eye_R_Caruncle", "Eye_L_UpperFold", "Eye_R_UpperFold",
    "Eye_L_UpperLashes", "Eye_R_UpperLashes", "Eye_L_LowerLashes", "Eye_R_LowerLashes",
}


def export(path, rig, excluded=()):
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
FULL.parent.mkdir(parents=True, exist_ok=True)
rig = bpy.data.objects["AevryndFemaleRig"]
export(FULL, rig)
export(LOD1, rig, LOD_EXCLUDED)
print(f"AEVRYND_V52_EXPORT full={FULL.stat().st_size} lod1={LOD1.stat().st_size}")
