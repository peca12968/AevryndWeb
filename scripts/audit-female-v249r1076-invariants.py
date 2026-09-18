"""Verify r1076 edits only eight paired vertices and preserves all relative key deltas."""
import hashlib
import json
import struct
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-commissure-falloff-r1074-study.blend"
CANDIDATE = ASSETS / "aevrynd-female-cc0-commissure-curvature-r1076-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1076-commissure-curvature.invariant-audit.json"
SOURCE_BODY = "AevryndFemaleCC0CommissureFalloff_R1074"
CANDIDATE_BODY = "AevryndFemaleCC0CommissureCurvature_R1076"
EDITED = (13523, 13686, 13524, 13688, 13558, 13722, 13559, 13723)


def topology_digest(mesh):
    digest = hashlib.sha256()
    for polygon in mesh.polygons:
        digest.update(struct.pack("<I", len(polygon.vertices)))
        for vertex in polygon.vertices:
            digest.update(struct.pack("<I", vertex))
    return digest.hexdigest()


def weight_digest(body):
    digest = hashlib.sha256()
    for vertex in body.data.vertices:
        for group in sorted(vertex.groups, key=lambda item: item.group):
            digest.update(struct.pack("<If", group.group, group.weight))
    return digest.hexdigest()


def unaffected_digest(body):
    edited = set(EDITED)
    digest = hashlib.sha256()
    for block in body.data.shape_keys.key_blocks:
        digest.update(block.name.encode("utf-8"))
        for index, item in enumerate(block.data):
            if index not in edited:
                digest.update(struct.pack("<3f", item.co.x, item.co.y, item.co.z))
    return digest.hexdigest()


def snapshot(path, body_name):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = bpy.data.objects[body_name]
    blocks = body.data.shape_keys.key_blocks
    deltas = {}
    coordinates = {}
    for block in blocks:
        relative = block.relative_key
        deltas[block.name] = {
            index: tuple(block.data[index].co - relative.data[index].co) for index in EDITED
        }
        coordinates[block.name] = {index: tuple(block.data[index].co) for index in EDITED}
    return {
        "vertices": len(body.data.vertices), "edges": len(body.data.edges), "faces": len(body.data.polygons),
        "shapeKeyNames": [block.name for block in blocks],
        "topologyDigest": topology_digest(body.data), "weightDigest": weight_digest(body),
        "unaffectedGeometryDigest": unaffected_digest(body),
        "materialNames": [material.name if material else None for material in body.data.materials],
        "deltas": deltas, "coordinates": coordinates,
    }


source = snapshot(SOURCE, SOURCE_BODY)
candidate = snapshot(CANDIDATE, CANDIDATE_BODY)
maximum_delta_error = 0.0
maximum_displacement = 0.0
displacements = {}
for key_name in source["shapeKeyNames"]:
    displacements[key_name] = {}
    for index in EDITED:
        source_delta = source["deltas"][key_name][index]
        candidate_delta = candidate["deltas"][key_name][index]
        error = sum((candidate_delta[axis] - source_delta[axis]) ** 2 for axis in range(3)) ** 0.5
        maximum_delta_error = max(maximum_delta_error, error)
        source_co = source["coordinates"][key_name][index]
        candidate_co = candidate["coordinates"][key_name][index]
        displacement = tuple(candidate_co[axis] - source_co[axis] for axis in range(3))
        maximum_displacement = max(maximum_displacement, sum(value * value for value in displacement) ** 0.5)
        displacements[key_name][str(index)] = [float(value) for value in displacement]

checks = {
    "topologyIdentical": source["topologyDigest"] == candidate["topologyDigest"],
    "weightsIdentical": source["weightDigest"] == candidate["weightDigest"],
    "shapeKeyNamesIdentical": source["shapeKeyNames"] == candidate["shapeKeyNames"],
    "unaffectedGeometryBitIdentical": source["unaffectedGeometryDigest"] == candidate["unaffectedGeometryDigest"],
    "relativeShapeKeyDeltaPreserved": maximum_delta_error <= 2e-7,
    "materialSlotCountIdentical": len(source["materialNames"]) == len(candidate["materialNames"]),
}
report = {
    "revision": "v249r1076-commissure-curvature-invariants",
    "source": str(SOURCE), "candidate": str(CANDIDATE), "editedVertices": list(EDITED),
    "sourceSummary": {key: value for key, value in source.items() if key not in ("deltas", "coordinates")},
    "candidateSummary": {key: value for key, value in candidate.items() if key not in ("deltas", "coordinates")},
    "maximumRelativeShapeKeyDeltaErrorM": maximum_delta_error,
    "maximumEditedVertexDisplacementM": maximum_displacement,
    "editedDisplacementsByShapeKey": displacements,
    "checks": checks, "status": "PASS" if all(checks.values()) else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1076_INVARIANTS=" + json.dumps({"status": report["status"], "checks": checks, "maximumRelativeShapeKeyDeltaErrorM": maximum_delta_error, "maximumEditedVertexDisplacementM": maximum_displacement}, sort_keys=True))
