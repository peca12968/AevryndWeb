"""Verify r1078 only appends weighted eyelid-wall topology to the r1076 body."""
import hashlib
import json
import struct
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-commissure-curvature-r1076-study.blend"
CANDIDATE = ASSETS / "aevrynd-female-cc0-eyelid-inner-wall-r1078-study.blend"
REPORT = ASSETS / "female-v249-mainline-r1078-eyelid-inner-wall.invariant-audit.json"
SOURCE_BODY = "AevryndFemaleCC0CommissureCurvature_R1076"
CANDIDATE_BODY = "AevryndFemaleCC0EyelidInnerWall_R1078"


def digest_prefix(body, vertex_count, face_count):
    geometry = hashlib.sha256()
    weights = hashlib.sha256()
    keys = body.data.shape_keys.key_blocks
    for block in keys:
        geometry.update(block.name.encode("utf-8"))
        for item in list(block.data)[:vertex_count]:
            geometry.update(struct.pack("<3f", item.co.x, item.co.y, item.co.z))
    for vertex in list(body.data.vertices)[:vertex_count]:
        for group in sorted(vertex.groups, key=lambda item: item.group):
            weights.update(struct.pack("<If", group.group, group.weight))
    faces = hashlib.sha256()
    for polygon in list(body.data.polygons)[:face_count]:
        faces.update(struct.pack("<I", len(polygon.vertices)))
        for index in polygon.vertices:
            faces.update(struct.pack("<I", index))
    return geometry.hexdigest(), weights.hexdigest(), faces.hexdigest()


def snapshot(path, name, prefix_vertices=None, prefix_faces=None):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    body = bpy.data.objects[name]
    vcount = len(body.data.vertices) if prefix_vertices is None else prefix_vertices
    fcount = len(body.data.polygons) if prefix_faces is None else prefix_faces
    geometry, weights, faces = digest_prefix(body, vcount, fcount)
    return {
        "vertices": len(body.data.vertices), "edges": len(body.data.edges), "faces": len(body.data.polygons),
        "shapeKeyNames": [block.name for block in body.data.shape_keys.key_blocks],
        "materials": [item.name if item else None for item in body.data.materials],
        "modifiers": [(item.name, item.type) for item in body.modifiers],
        "objects": len(bpy.data.objects), "geometryPrefixDigest": geometry,
        "weightPrefixDigest": weights, "facePrefixDigest": faces,
        "newWeightCounts": [len(vertex.groups) for vertex in list(body.data.vertices)[vcount:]],
    }


source = snapshot(SOURCE, SOURCE_BODY)
candidate = snapshot(CANDIDATE, CANDIDATE_BODY, source["vertices"], source["faces"])
added_vertices = candidate["vertices"] - source["vertices"]
added_faces = candidate["faces"] - source["faces"]
checks = {
    "originalShapeKeyCoordinatesBitIdentical": source["geometryPrefixDigest"] == candidate["geometryPrefixDigest"],
    "originalWeightsBitIdentical": source["weightPrefixDigest"] == candidate["weightPrefixDigest"],
    "originalFacePrefixBitIdentical": source["facePrefixDigest"] == candidate["facePrefixDigest"],
    "shapeKeyNamesIdentical": source["shapeKeyNames"] == candidate["shapeKeyNames"],
    "materialSlotsIdentical": source["materials"] == candidate["materials"],
    "modifiersIdentical": source["modifiers"] == candidate["modifiers"],
    "objectCountIdentical": source["objects"] == candidate["objects"],
    "expectedTopologyDelta": added_vertices == 180 and added_faces == 180,
    "allNewVerticesWeighted": len(candidate["newWeightCounts"]) == 180 and min(candidate["newWeightCounts"]) >= 3,
}
report = {
    "revision": "v249r1078-eyelid-inner-wall-invariants", "source": str(SOURCE), "candidate": str(CANDIDATE),
    "sourceSummary": source, "candidateSummary": candidate,
    "topologyDelta": {"vertices": added_vertices, "faces": added_faces},
    "checks": checks, "status": "PASS" if all(checks.values()) else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R1078_INVARIANTS=" + json.dumps({"status": report["status"], "delta": report["topologyDelta"], "checks": checks}, sort_keys=True))
