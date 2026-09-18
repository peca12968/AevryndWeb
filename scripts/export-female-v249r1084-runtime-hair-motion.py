"""Export r1083 into an Aevrynd-owned deterministic runtime hair-motion format."""
import hashlib
import json
import struct
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-layered-hair-motion-r1083-study.blend"
OUT = ASSETS / "runtime-hair-motion-r1084"
PUBLIC_OUT = ROOT / "public/assets/character-r1084-motion"
REPORT = ASSETS / "female-v249-mainline-r1084-runtime-hair-motion.export.json"
HAIR = "AevryndFemaleGradedHairlineGroom_R1081"


def write_values(path, code, values):
    payload = struct.pack(f"<{len(values)}{code}", *values)
    path.write_bytes(payload)
    return {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
hair = bpy.data.objects[HAIR]
motion = hair.data.attributes["aevrynd_motion_vector_r1083"]
phase = hair.data.attributes["aevrynd_motion_phase_r1083"]
radius = hair.data.attributes.get("radius")
offsets = [curve.first_point_index for curve in hair.data.curves] + [len(hair.data.points)]
base_positions = [axis for point in hair.data.points for axis in point.position]
motion_vectors = [axis for item in motion.data for axis in item.vector]
curve_phases = [phase.data[curve.first_point_index].value for curve in hair.data.curves]
radii = [item.value for item in radius.data] if radius else [0.00004] * len(hair.data.points)
OUT.mkdir(parents=True, exist_ok=True)
PUBLIC_OUT.mkdir(parents=True, exist_ok=True)
files = {
    "curveOffsets": ("curve-offsets.u32", "I", offsets),
    "basePositions": ("base-positions.f32", "f", base_positions),
    "motionVectors": ("motion-vectors.f32", "f", motion_vectors),
    "curvePhases": ("curve-phases.f32", "f", curve_phases),
    "radii": ("radii.f32", "f", radii),
}
digests = {}
for key, (name, code, values) in files.items():
    digests[key] = write_values(OUT / name, code, values)
    (PUBLIC_OUT / name).write_bytes((OUT / name).read_bytes())
manifest = {
    "format": "aevrynd-runtime-hair-motion-v1",
    "source": str(SOURCE),
    "license": "Aevrynd project-authored geometry and motion; no runtime platform dependency",
    "coordinateSystem": "hair-object local metres, Blender Z up",
    "geometry": {
        "curveCount": len(hair.data.curves),
        "pointCount": len(hair.data.points),
        "longCurveCount": sum(curve.points_length == 20 for curve in hair.data.curves),
        "shortCurveCount": sum(curve.points_length < 20 for curve in hair.data.curves),
    },
    "motion": {
        "framesPerSecond": 30,
        "cycleFrames": 60,
        "restFrames": [1, 61],
        "envelope": "sin(pi*u)^2",
        "sway": "envelope*(0.55+0.45*sin((frame-1)*2pi/48+curvePhase))",
        "rootFalloff": "authored into per-point motion vectors with t^2.15",
        "maximumAuthoredVectorM": max((item.vector.length for item in motion.data), default=0.0),
    },
    "files": {key: name for key, (name, _code, _values) in files.items()},
    "digests": digests,
    "sourceAudit": "female-v249-mainline-r1083-layered-hair-motion.audit.json",
    "releaseState": "ISOLATED_RUNTIME_CANDIDATE_NOT_WEBSITE_ASSET",
}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
(PUBLIC_OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
total = sum(item["bytes"] for item in digests.values())
report = {"revision": "v249r1084-runtime-hair-motion-export", "source": str(SOURCE), "output": str(OUT), "publicBenchmarkCopy": str(PUBLIC_OUT), "manifest": manifest, "totalBinaryBytes": total, "status": "EXPORTED_AUDIT_PENDING"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1084_RUNTIME_HAIR_EXPORT=" + json.dumps({"curveCount": manifest["geometry"]["curveCount"], "pointCount": manifest["geometry"]["pointCount"], "totalBinaryBytes": total, "digests": digests}, sort_keys=True))
