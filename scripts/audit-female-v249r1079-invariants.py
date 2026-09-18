"""Verify r1079 only moves the intended aperture and wall vertices."""
import hashlib
import json
import struct
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-eyelid-inner-wall-r1078-study.blend"
CANDIDATE = ASSETS / "aevrynd-female-cc0-canthus-contour-r1079-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1079-canthus-contour.invariant-audit.json"
SOURCE_BODY = "AevryndFemaleCC0EyelidInnerWall_R1078"
CANDIDATE_BODY = "AevryndFemaleCC0CanthusContour_R1079"


def digest_topology(mesh):
    value = hashlib.sha256()
    for polygon in mesh.polygons:
        value.update(struct.pack("<I", len(polygon.vertices)))
        for index in polygon.vertices: value.update(struct.pack("<I", index))
    return value.hexdigest()


def digest_weights(body):
    value = hashlib.sha256()
    for vertex in body.data.vertices:
        for item in sorted(vertex.groups, key=lambda member: member.group): value.update(struct.pack("<If", item.group, item.weight))
    return value.hexdigest()


def snapshot(path, name):
    bpy.ops.wm.open_mainfile(filepath=str(path)); body = bpy.data.objects[name]; blocks = body.data.shape_keys.key_blocks
    return {
        "vertices": len(body.data.vertices), "edges": len(body.data.edges), "faces": len(body.data.polygons),
        "shapeKeyNames": [block.name for block in blocks], "coords": [[item.co.copy() for item in block.data] for block in blocks],
        "relativeIndices": [blocks[:].index(block.relative_key) for block in blocks],
        "topologyDigest": digest_topology(body.data), "weightDigest": digest_weights(body),
        "materials": [item.name if item else None for item in body.data.materials], "modifiers": [(item.name,item.type) for item in body.modifiers],
        "objectCount": len(bpy.data.objects),
    }


source = snapshot(SOURCE, SOURCE_BODY); candidate = snapshot(CANDIDATE, CANDIDATE_BODY)
changed = []
for index, (a,b) in enumerate(zip(source["coords"][0], candidate["coords"][0])):
    if (b-a).length > 1e-10: changed.append(index)
maximum_delta_error = 0.0; maximum_displacement = 0.0
for key_index in range(len(source["shapeKeyNames"])):
    relative = source["relativeIndices"][key_index]
    for index in changed:
        a = source["coords"][key_index][index] - source["coords"][relative][index]
        b = candidate["coords"][key_index][index] - candidate["coords"][relative][index]
        maximum_delta_error = max(maximum_delta_error, (b-a).length)
        maximum_displacement = max(maximum_displacement, (candidate["coords"][key_index][index]-source["coords"][key_index][index]).length)
unaffected_identical = all(source["coords"][key][index] == candidate["coords"][key][index] for key in range(len(source["shapeKeyNames"])) for index in range(source["vertices"]) if index not in set(changed))
checks = {
    "topologyIdentical": source["topologyDigest"] == candidate["topologyDigest"], "weightsIdentical": source["weightDigest"] == candidate["weightDigest"],
    "shapeKeysIdentical": source["shapeKeyNames"] == candidate["shapeKeyNames"], "relativeShapeKeyDeltasPreserved": maximum_delta_error <= 2e-7,
    "unaffectedCoordinatesBitIdentical": unaffected_identical, "expectedEditedVertexCount": len(changed) == 174,
    "materialsIdentical": source["materials"] == candidate["materials"], "modifiersIdentical": source["modifiers"] == candidate["modifiers"], "objectCountIdentical": source["objectCount"] == candidate["objectCount"],
}
report = {"revision": "v249r1079-canthus-contour-invariants", "source": str(SOURCE), "candidate": str(CANDIDATE), "editedVertexIndices": changed, "editedVertexCount": len(changed), "maximumRelativeShapeKeyDeltaErrorM": maximum_delta_error, "maximumDisplacementM": maximum_displacement, "checks": checks, "status": "PASS" if all(checks.values()) else "FAIL"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1079_INVARIANTS=" + json.dumps({"status": report["status"], "edited": len(changed), "maxDeltaError": maximum_delta_error, "maxDisplacementM": maximum_displacement, "checks": checks}, sort_keys=True))
