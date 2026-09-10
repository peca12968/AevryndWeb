import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r38.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-boolean-eyelid-r66.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-boolean-eyelid-r66"
OUT.mkdir(parents=True, exist_ok=True)
BODY = "AevryndFemaleBodyBaseV118"
EYES = {"L": (0.034528, -0.10087, 1.607765), "R": (-0.034443, -0.10077, 1.607765)}
SEGMENTS = 64


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def cutter_point(side, center, ring, index):
    theta = 2.0 * math.pi * index / SEGMENTS
    sine = math.sin(theta)
    cosine = math.cos(theta)
    height = ring["upper"] if sine >= 0.0 else ring["lower"]
    lateral_sign = 1.0 if side == "L" else -1.0
    x = center[0] + ring["width"] * cosine
    z = center[2] + height * sine + lateral_sign * ring["tilt"] * (x - center[0])
    return (x, ring["y"], z)


def make_cutter(side, center):
    # The first ring begins outside the face; the rear ring extends beyond the
    # legacy eye cap.  Gentle inward taper creates a physical lid wall.
    rings = (
        {"y": -0.135, "width": 0.01045, "upper": 0.00382, "lower": 0.00282, "tilt": 0.023},
        {"y": -0.108, "width": 0.01025, "upper": 0.00368, "lower": 0.00272, "tilt": 0.023},
        {"y": -0.074, "width": 0.00970, "upper": 0.00342, "lower": 0.00252, "tilt": 0.021},
    )
    vertices = [
        cutter_point(side, center, ring, index)
        for ring in rings
        for index in range(SEGMENTS)
    ]
    faces = []
    for ring_index in range(len(rings) - 1):
        first = ring_index * SEGMENTS
        second = (ring_index + 1) * SEGMENTS
        for index in range(SEGMENTS):
            following = (index + 1) % SEGMENTS
            faces.append((first + index, first + following, second + following, second + index))
    faces.append(tuple(reversed(range(SEGMENTS))))
    rear = (len(rings) - 1) * SEGMENTS
    faces.append(tuple(rear + index for index in range(SEGMENTS)))
    mesh = bpy.data.meshes.new(f"AevryndEyeCutter{side}Mesh_r64")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    cutter = bpy.data.objects.new(f"AevryndEyeCutter_{side}_r64", mesh)
    bpy.context.collection.objects.link(cutter)
    bevel = cutter.modifiers.new("Aevrynd Lid Edge Radius", "BEVEL")
    bevel.width = 0.00022
    bevel.segments = 3
    bevel.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = cutter
    cutter.select_set(True)
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    cutter.select_set(False)
    return cutter


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
body.data = body.data.copy()
boolean_stats = {}
for side, center in EYES.items():
    cutter = make_cutter(side, center)
    before = {"vertices": len(body.data.vertices), "faces": len(body.data.polygons)}
    modifier = body.modifiers.new(f"Aevrynd Boolean Eye Aperture {side}", "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = cutter
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    # The aperture must be authored in the undeformed base mesh.  Applying a
    # boolean after the armature bakes pose-space geometry and breaks frame 20.
    while body.modifiers.find(modifier.name) > 0:
        bpy.ops.object.modifier_move_up(modifier=modifier.name)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    body.select_set(False)
    after = {"vertices": len(body.data.vertices), "faces": len(body.data.polygons)}
    boolean_stats[side] = {"before": before, "after": after}
    bpy.data.objects.remove(cutter, do_unlink=True)

# Remove exact-boolean duplicate and degenerate elements before deformation.
bm = bmesh.new()
bm.from_mesh(body.data)
merge_result = bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.0000001)
bmesh.ops.dissolve_degenerate(bm, edges=list(bm.edges), dist=0.00000001)
bm.normal_update()
bm.to_mesh(body.data)
bm.free()
body.data.update()

# Boolean-created cut vertices do not inherit reliable deformation weights.
# The complete orbital region is rigid cranium, so bind it explicitly to head.
head_group = body.vertex_groups.get("head")
if head_group is None:
    raise RuntimeError("Body has no head deformation group")
orbital_vertices = [
    vertex.index for vertex in body.data.vertices
    if -0.137 < vertex.co.y < -0.072
    and any(
        abs(vertex.co.x - center[0]) < 0.013
        and abs(vertex.co.z - center[2]) < 0.006
        for center in EYES.values()
    )
]
head_group.add(orbital_vertices, 1.0, "REPLACE")

for side in EYES:
    for part in ("Sclera", "Cornea", "Iris", "LimbalRing", "Pupil", "Catchlight"):
        optical = bpy.data.objects.get(f"Eye_{side}_{part}")
        if optical is not None and optical.type == "MESH":
            optical.data = optical.data.copy()
            for vertex in optical.data.vertices:
                vertex.co.y += 0.00020
            optical.data.update()
    for part in ("UpperLashes", "LowerLashes", "TearMeniscus"):
        accessory = bpy.data.objects.get(f"Eye_{side}_{part}")
        if accessory is not None:
            accessory.hide_render = False
            accessory["aevrynd_revision"] = "temporarily-retained-for-v249-mainline-boolean-eyelid-r66"

body["aevrynd_mainline_baseline"] = "v249"
body["aevrynd_face_revision"] = "v249-mainline-boolean-eyelid-r66"
body["aevrynd_eye_topology"] = "exact tapered almond aperture boolean with rounded cutter"
scene = bpy.context.scene
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "boolean-eyelid-r66"
scene["aevrynd_release_state"] = "R66_STRICT_VISUAL_AND_COLLISION_REVIEW_REQUIRED"

scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
camera = bpy.data.objects["Aevrynd Review Camera"]
views = (
    ("01-eye-close", (0.0, -0.47, 1.610), (0.0, -0.065, 1.608), 112),
    ("02-face-front", (0.0, -0.72, 1.60), (0.0, -0.025, 1.595), 88),
    ("03-face-three-quarter", (0.45, -0.62, 1.62), (0.0, -0.015, 1.595), 88),
)
for name, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)

report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "boolean_stats": boolean_stats,
    "segments": SEGMENTS,
    "visible_aperture_width_mm": 20.9,
    "visible_aperture_upper_mm": 3.82,
    "visible_aperture_lower_mm": 2.82,
    "cutter_edge_radius_mm": 0.22,
    "modifier_order": "boolean-before-armature",
    "explicit_head_weight_vertices": len(orbital_vertices),
    "boolean_merge_distance_mm": 0.0001,
    "optical_recess_mm": 0.20,
    "status": "STRICT_VISUAL_REVIEW_REQUIRED",
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_BOOLEAN_EYELID_R66=" + json.dumps(report, sort_keys=True))
