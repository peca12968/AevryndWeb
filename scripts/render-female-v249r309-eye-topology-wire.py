import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-recessed-natural-eyes-r301.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r309-eye-topology-wire"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-eye-topology-wire-r309.study.json"
BODY = "AevryndFemaleBody_CC0_R249"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
body = bpy.data.objects[BODY]
wire = body.copy()
wire.data = body.data.copy()
wire.name = "AevryndEyeTopologyWire_R309"
scene.collection.objects.link(wire)
wire.display_type = "WIRE"
wire.data.materials.clear()
material = bpy.data.materials.new("AevryndEyeTopologyWire_R309")
material.use_nodes = True
shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
shader.inputs["Base Color"].default_value = (0.005, 0.30, 0.75, 1.0)
shader.inputs["Emission Color"].default_value = (0.005, 0.20, 0.80, 1.0)
shader.inputs["Emission Strength"].default_value = 2.0
shader.inputs["Roughness"].default_value = 0.25
wire.data.materials.append(material)
for polygon in wire.data.polygons:
    polygon.material_index = 0
modifier = wire.modifiers.new("Eye topology wire", "WIREFRAME")
modifier.thickness = 0.000085
modifier.use_even_offset = True
modifier.use_replace = True

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
OUT.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    ("front", (0.0, -0.57, 1.608), (0.0, -0.025, 1.608), 105),
    ("three-quarter", (0.35, -0.47, 1.62), (0.0, -0.02, 1.608), 105),
    ("left-eye", (0.17, -0.41, 1.611), (0.0345, -0.105, 1.608), 120),
)
for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x = scene.render.resolution_y = 1200
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)

nearby = {}
for side, cx in (("L", 0.034528), ("R", -0.034443)):
    vertices = [
        vertex.index for vertex in body.data.vertices
        if abs(vertex.co.x - cx) < 0.024 and abs(vertex.co.z - 1.607765) < 0.017 and vertex.co.y < -0.125
    ]
    faces = [
        polygon.index for polygon in body.data.polygons
        if any(index in vertices for index in polygon.vertices)
    ]
    nearby[side] = {"vertices": len(vertices), "faces": len(faces), "vertexIndices": vertices, "faceIndices": faces}
report = {"source": str(SOURCE), "body": BODY, "renderDirectory": str(OUT), "eyeRegions": nearby, "status": "TOPOLOGY_REVIEW_READY"}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R309_EYE_TOPOLOGY_WIRE=" + json.dumps({"renderDirectory": str(OUT), "counts": {side: {key: value for key, value in rows.items() if key in ('vertices','faces')} for side, rows in nearby.items()}}, sort_keys=True))
