import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-eyelid-r78.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-topology-r79"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-topology-r79.json"
BODY = "AevryndFemaleBodyBaseV118"


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def band(body, center, half_height=0.004):
    points = [
        vertex.co for vertex in body.data.vertices
        if abs(vertex.co.z - center) <= half_height and vertex.co.y < -0.050
    ]
    if not points:
        return None
    front = min(point.y for point in points)
    near_front = [point for point in points if point.y <= front + 0.030]
    return {
        "z_m": center,
        "samples": len(points),
        "front_y_m": front,
        "front_width_m": 2.0 * max(abs(point.x) for point in near_front),
    }


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
OUT.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects[BODY]
mesh = body.data
face_polygons = [
    polygon for polygon in mesh.polygons
    if 1.440 < polygon.center.z < 1.690 and polygon.center.y < -0.060
]
report = {
    "source": str(SOURCE),
    "body_vertices": len(mesh.vertices),
    "body_edges": len(mesh.edges),
    "body_polygons": len(mesh.polygons),
    "face_region_polygons": len(face_polygons),
    "face_region_triangles": sum(len(p.vertices) == 3 for p in face_polygons),
    "face_region_quads": sum(len(p.vertices) == 4 for p in face_polygons),
    "cross_sections": [
        band(body, z) for z in (1.665, 1.640, 1.615, 1.590, 1.565, 1.540, 1.515, 1.490, 1.465)
    ],
}
payload = json.dumps(report, indent=2)
(OUT / "topology-report.json").write_text(payload, encoding="utf-8")
REPORT.write_text(payload, encoding="utf-8")

for obj in bpy.data.objects:
    obj.hide_render = obj != body and obj.name != "Aevrynd Review Camera"
wire_material = bpy.data.materials.new("Aevrynd Topology Diagnostic Wire")
wire_material.diffuse_color = (0.015, 0.018, 0.022, 1.0)
wire_overlay = body.copy()
wire_overlay.data = body.data.copy()
wire_overlay.name = "AevryndFaceTopologyWireDiagnostic"
body.users_collection[0].objects.link(wire_overlay)
wire_overlay.data.materials.clear()
wire_overlay.data.materials.append(wire_material)
wire = wire_overlay.modifiers.new("Aevrynd Face Wire", "WIREFRAME")
wire.thickness = 0.00010
wire.use_even_offset = True
wire.use_replace = True
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "WORLD"
scene.display.shading.show_specular_highlight = False
scene.render.resolution_x = scene.render.resolution_y = 1400
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("01-front-wire", (0.0, -0.56, 1.585), (0.0, -0.060, 1.585), 108),
    ("02-three-quarter-wire", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
    ("03-profile-wire", (0.70, -0.03, 1.61), (0.0, -0.005, 1.595), 88),
)
for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)
print("AEVRYND_V249_TOPOLOGY_R79=" + json.dumps(report, sort_keys=True))
