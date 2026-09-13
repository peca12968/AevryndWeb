import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-layered-optical-stack-r420.blend"
AUDIT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-layered-optical-stack-r420.face-layer-audit.json"
KINDS = ("ScleraOpen", "LimbalAnnulus", "IrisConcave", "PupilRecessed", "CorneaConvex")


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
expected = [f"AevryndEye_{side}_{kind}_R420" for side in ("L", "R") for kind in KINDS]
violations = []
layers = {}
positions = {}

for frame in (1, 20):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    positions[str(frame)] = {}
    for name in expected:
        obj = bpy.data.objects.get(name)
        if obj is None:
            if frame == 1:
                violations.append({"object": name, "issue": "missing"})
            continue
        positions[str(frame)][name] = list(obj.matrix_world.translation)

for name in expected:
    obj = bpy.data.objects.get(name)
    if obj is None:
        continue
    info = {
        "type": obj.type,
        "vertices": len(obj.data.vertices) if obj.type == "MESH" else None,
        "polygons": len(obj.data.polygons) if obj.type == "MESH" else None,
        "parent": obj.parent.name if obj.parent else None,
        "parentType": obj.parent_type,
        "parentBone": obj.parent_bone,
        "binding": obj.get("aevrynd_binding"),
        "layer": obj.get("aevrynd_layer"),
        "revision": obj.get("aevrynd_revision"),
        "hideRender": obj.hide_render,
        "materials": [material.name for material in obj.data.materials if material],
    }
    p1 = positions["1"].get(name)
    p20 = positions["20"].get(name)
    motion = sum((p20[i] - p1[i]) ** 2 for i in range(3)) ** 0.5 if p1 and p20 else 0.0
    info["frame1To20OriginMotionM"] = motion
    layers[name] = info
    if obj.type != "MESH":
        violations.append({"object": name, "issue": "not_mesh"})
    if not obj.parent or obj.parent.name != "AevryndFemaleRig" or obj.parent_type != "BONE" or obj.parent_bone != "head":
        violations.append({"object": name, "issue": "invalid_head_binding"})
    if obj.get("aevrynd_binding") != "rig.head":
        violations.append({"object": name, "issue": "missing_binding_contract"})
    if not obj.data.materials:
        violations.append({"object": name, "issue": "missing_material"})
    if obj.hide_render:
        violations.append({"object": name, "issue": "unexpected_hidden_render"})
    if motion <= 1e-6:
        violations.append({"object": name, "issue": "does_not_follow_head_frame20"})

for side in ("L", "R"):
    if bpy.data.objects.get(f"AevryndEye_{side}_Sclera_R249"):
        violations.append({"object": f"AevryndEye_{side}_Sclera_R249", "issue": "retired_integrated_eye_still_present"})

audit = {
    "model": str(SOURCE), "expectedLayerCount": len(expected), "layers": layers,
    "violations": violations, "status": "PASS" if not violations else "FAIL",
}
AUDIT.write_text(json.dumps(audit, indent=2), encoding="utf-8")
print("AEVRYND_R420_FACE_LAYER_AUDIT=" + json.dumps(audit, sort_keys=True))
if violations:
    raise SystemExit(2)
