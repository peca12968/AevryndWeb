import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-recessed-natural-eyes-r301.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-recessed-natural-eyes-r301.eye-topology.json"
BODY_CANDIDATES = ("AevryndFemaleBodyBaseV118", "AevryndFemaleBody_CC0_R249", "AevryndFemaleBody")
EYES = {"L": (0.034528, 1.607765), "R": (-0.034443, 1.607765)}


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = next((bpy.data.objects.get(name) for name in BODY_CANDIDATES if bpy.data.objects.get(name)), None)
if body is None:
    possible = [obj for obj in bpy.data.objects if obj.type == "MESH" and ("body" in obj.name.lower() or "skin" in obj.name.lower())]
    if not possible:
        raise RuntimeError("No body mesh found; mesh objects=" + ", ".join(obj.name for obj in bpy.data.objects if obj.type == "MESH"))
    body = max(possible, key=lambda obj: len(obj.data.vertices))
mesh = body.data
edge_face_counts = {}
for polygon in mesh.polygons:
    for key in polygon.edge_keys:
        normalized = tuple(sorted(key))
        edge_face_counts[normalized] = edge_face_counts.get(normalized, 0) + 1
edge_rows = {}
surface_rows = {}
for side, (cx, cz) in EYES.items():
    candidates = []
    for edge in mesh.edges:
        if edge_face_counts.get(tuple(sorted(edge.vertices)), 0) != 1:
            continue
        a = mesh.vertices[edge.vertices[0]].co
        b = mesh.vertices[edge.vertices[1]].co
        mx = (a.x + b.x) * 0.5
        my = (a.y + b.y) * 0.5
        mz = (a.z + b.z) * 0.5
        if abs(mx - cx) < 0.025 and abs(mz - cz) < 0.018 and my < -0.085:
            candidates.append({"edge": list(edge.vertices), "mid": [mx, my, mz]})
    vertex_ids = sorted({index for row in candidates for index in row["edge"]})
    vertices = [
        {"index": index, "co": list(mesh.vertices[index].co)}
        for index in vertex_ids
    ]
    edge_rows[side] = {"edges": candidates, "vertices": vertices}
    local = []
    for vertex in mesh.vertices:
        point = vertex.co
        if abs(point.x - cx) < 0.024 and abs(point.z - cz) < 0.016 and point.y < -0.075:
            local.append({"index": vertex.index, "co": list(point.co if hasattr(point, "co") else point)})
    surface_rows[side] = sorted(local, key=lambda row: row["co"][1])

eye_objects = []
for obj in bpy.data.objects:
    lowered = obj.name.lower()
    if any(token in lowered for token in ("eye", "lid", "lash", "brow", "tear", "caruncle")):
        if obj.type == "MESH":
            world = [obj.matrix_world @ vertex.co for vertex in obj.data.vertices]
            point_count = len(obj.data.vertices)
        elif obj.type == "CURVE":
            world = [obj.matrix_world @ point.co.xyz for spline in obj.data.splines for point in spline.points]
            point_count = len(world)
        else:
            continue
        if not world:
            continue
        eye_objects.append({
            "name": obj.name,
            "type": obj.type,
            "vertices": point_count,
            "parent": obj.parent.name if obj.parent else None,
            "bounds": {
                axis: [min(point[index] for point in world), max(point[index] for point in world)]
                for index, axis in enumerate(("x", "y", "z"))
            },
            "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
        })

report = {
    "source": str(SOURCE),
    "body": body.name,
    "bodyVertices": len(mesh.vertices),
    "bodyEdges": len(mesh.edges),
    "bodyPolygons": len(mesh.polygons),
    "boundary": edge_rows,
    "surfaceVertices": surface_rows,
    "eyeObjects": eye_objects,
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R301_EYE_TOPOLOGY=" + json.dumps({
    "report": str(REPORT),
    "counts": {side: {"edges": len(data["edges"]), "vertices": len(data["vertices"])} for side, data in edge_rows.items()},
}, sort_keys=True))
