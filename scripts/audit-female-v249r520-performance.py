import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
BASELINE = ASSETS / "aevrynd-female-authoring-v249-mainline-layered-front-locks-r517.blend"
CANDIDATE = ASSETS / "aevrynd-female-authoring-v249-mainline-natural-eye-ratio-r520.blend"
REPORT = ASSETS / "female-v249-mainline-natural-eye-ratio-r520.performance-audit.json"


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    visible = [obj for obj in bpy.data.objects if obj.type == "MESH" and not obj.hide_render]
    return {
        "fileBytes": path.stat().st_size,
        "visibleMeshObjects": len(visible),
        "vertices": sum(len(obj.data.vertices) for obj in visible),
        "polygons": sum(len(obj.data.polygons) for obj in visible),
        "triangles": sum(max(0, len(poly.vertices) - 2) for obj in visible for poly in obj.data.polygons),
        "drawCallsUpperBound": sum(max(1, len(obj.material_slots)) for obj in visible),
        "materials": len({slot.material.name for obj in visible for slot in obj.material_slots if slot.material}),
    }


baseline = snapshot(BASELINE)
candidate = snapshot(CANDIDATE)
deltas = {name: candidate[name] - baseline[name] for name in baseline}
gate = {
    "verticesNoIncrease": deltas["vertices"] <= 0,
    "trianglesNoIncrease": deltas["triangles"] <= 0,
    "drawCallsNoIncrease": deltas["drawCallsUpperBound"] <= 0,
    "materialsNoIncrease": deltas["materials"] <= 0,
}
report = {
    "baseline": str(BASELINE),
    "candidate": str(CANDIDATE),
    "measurement": "visible authoring mesh structural upper bound; website v83 remains unchanged",
    "baselineStats": baseline,
    "candidateStats": candidate,
    "delta": deltas,
    "gate": gate,
    "status": "PASS" if all(gate.values()) else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R520_PERFORMANCE=" + json.dumps({"status": report["status"], "delta": deltas}, sort_keys=True))
if report["status"] != "PASS":
    raise SystemExit(2)
