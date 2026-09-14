import json
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
OUT = ASSETS / "runtime-character-r526"
MODELS = (
    ("baseline-r522", ASSETS / "aevrynd-female-authoring-v249-mainline-natural-commissures-r522.blend"),
    ("candidate-r526", ASSETS / "aevrynd-female-authoring-v249-mainline-orbital-brow-refit-r526.blend"),
)

OUT.mkdir(parents=True, exist_ok=True)
exports = {}
for label, source in MODELS:
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    scene.frame_set(1)
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    selected = []
    for obj in bpy.data.objects:
        if obj.hide_render or obj.type not in {"MESH", "CURVE", "ARMATURE"}:
            continue
        obj.select_set(True)
        selected.append(obj)
    rig = bpy.data.objects.get("AevryndFemaleRig")
    if rig:
        bpy.context.view_layer.objects.active = rig
    target = OUT / f"{label}.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(target),
        export_format="GLB",
        use_selection=True,
        export_apply=False,
        export_animations=True,
    )
    exports[label] = {
        "source": str(source),
        "asset": str(target),
        "bytes": target.stat().st_size,
        "selectedObjects": len(selected),
        "selectedMeshes": sum(obj.type == "MESH" for obj in selected),
        "selectedCurves": sum(obj.type == "CURVE" for obj in selected),
        "selectedArmatures": sum(obj.type == "ARMATURE" for obj in selected),
    }

manifest = {
    "format": "aevrynd-full-character-runtime-comparison-v1",
    "ownership": "Aevrynd-owned/CC0-traceable authoring geometry; no MetaHuman or Unreal runtime dependency",
    "externalRuntimeDependencies": [],
    "exports": exports,
    "releaseState": "OFFLINE_BENCHMARK_ASSETS_WEBSITE_REPLACEMENT_NOT_APPROVED",
}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print("AEVRYND_R526_FULL_EXPORT=" + json.dumps(manifest, sort_keys=True))
