import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source" / "aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-sorted-tear-film-r499.blend"
OUT = ASSETS / "runtime-groom-r499"
GLB = OUT / "aevrynd-female-hair-runtime-r499.glb"
MANIFEST = OUT / "manifest.json"
RIG = "AevryndFemaleRig"
LAYERS = (
    "AevryndFemaleRuntimeScalpCap_R467",
    "AevryndFemaleRuntimeHairlineDensity_R467",
    "AevryndFemaleRuntimePartRootDensity_R467",
    "AevryndFemaleRuntimeCards_front_R467",
    "AevryndFemaleRuntimeCards_crown_R467",
    "AevryndFemaleRuntimeCards_rear_R467",
    "AevryndFemaleRuntimeCards_hairline_R467",
)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()
bpy.ops.object.select_all(action="DESELECT")
rig = bpy.data.objects[RIG]
rig.select_set(True)
objects = []
for name in LAYERS:
    obj = bpy.data.objects[name]
    obj.select_set(True)
    objects.append(obj)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.gltf(
    filepath=str(GLB),
    export_format="GLB",
    use_selection=True,
    export_apply=False,
    export_animations=True,
)

manifest = {
    "format": "aevrynd-runtime-card-groom-v1-baseline",
    "source": str(SOURCE),
    "asset": str(GLB),
    "ownership": "Aevrynd-owned geometry and textures",
    "externalRuntimeDependencies": [],
    "layers": [
        {
            "object": obj.name,
            "layer": obj.get("aevrynd_layer"),
            "vertices": len(obj.data.vertices),
            "polygons": len(obj.data.polygons),
            "cards": int(obj.get("aevrynd_card_count", 0)),
        }
        for obj in objects
    ],
    "totals": {
        "vertices": sum(len(obj.data.vertices) for obj in objects),
        "polygons": sum(len(obj.data.polygons) for obj in objects),
        "visibleDynamicCards": sum(int(obj.get("aevrynd_card_count", 0)) for obj in objects),
    },
    "animationCount": len(bpy.data.actions),
    "releaseState": "R499_RUNTIME_PERFORMANCE_BASELINE",
}
manifest["glbBytes"] = GLB.stat().st_size
MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print("AEVRYND_R499_RUNTIME_EXPORT=" + json.dumps(manifest, sort_keys=True))
