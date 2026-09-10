import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r38.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-clean-eyelid-r54.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-clean-eyelid-r54"
OUT.mkdir(parents=True, exist_ok=True)
BODY = "AevryndFemaleBodyBaseV118"
EYES = {"L": (0.034528, -0.10087, 1.607765), "R": (-0.034443, -0.10077, 1.607765)}
SEGMENTS = 48


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def asymmetric_ellipse(point, center, width, upper, lower):
    dx = (point.x - center[0]) / width
    height = upper if point.z >= center[2] else lower
    dz = (point.z - center[2]) / height
    return dx * dx + dz * dz


def surface_y(surface, x, z):
    origin = Vector((x, -0.30, z))
    location, _normal, _index, _distance = surface.ray_cast(origin, Vector((0.0, 1.0, 0.0)))
    if location is None:
        raise RuntimeError(f"No facial surface at x={x:.6f}, z={z:.6f}")
    return location.y


def ring_point(body, side, ring, theta):
    cx, _cy, cz = EYES[side]
    lateral_sign = 1.0 if side == "L" else -1.0
    sine = math.sin(theta)
    cosine = math.cos(theta)
    height = ring["upper"] if sine >= 0.0 else ring["lower"]
    x = cx + ring["width"] * cosine
    z = cz + height * sine + lateral_sign * ring["tilt"] * (x - cx)
    y = surface_y(body, x, z) + ring["surface_offset"]
    return Vector((x, y, z))


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
# Preserve an untouched geometry snapshot for surface projection after the body
# aperture faces have been removed.  It does not enter the scene or the output.
surface_body = BVHTree.FromPolygons(
    [vertex.co.copy() for vertex in body.data.vertices],
    [[vertex_index for vertex_index in polygon.vertices] for polygon in body.data.polygons],
    all_triangles=False,
)
body.data = body.data.copy()

# Remove only the closed facial sheet underneath the replacement patch.  The
# deletion boundary stays hidden below the wider outer ring of the clean patch.
bm = bmesh.new()
bm.from_mesh(body.data)
bm.faces.ensure_lookup_table()
deleted = {}
for side, center in EYES.items():
    faces = [
        face for face in bm.faces
        if face.calc_center_median().y < -0.090
        and asymmetric_ellipse(
            face.calc_center_median(), center, 0.0152, 0.00625, 0.00475
        ) < 1.0
    ]
    deleted[side] = len(faces)
    bmesh.ops.delete(bm, geom=faces, context="FACES")
bm.normal_update()
bm.to_mesh(body.data)
bm.free()
body.data.update()

rings = (
    # Outer skin blend, lid body, visible lid margin, then the inner tarsal wall.
    {"name": "orbital_blend", "width": 0.0182, "upper": 0.0075, "lower": 0.0058,
     "tilt": 0.030, "surface_offset": -0.00010},
    {"name": "lid_plane", "width": 0.0146, "upper": 0.0058, "lower": 0.00435,
     "tilt": 0.026, "surface_offset": -0.00022},
    {"name": "lid_margin", "width": 0.01045, "upper": 0.00415, "lower": 0.00305,
     "tilt": 0.023, "surface_offset": -0.00030},
)

patches = {}
for side in EYES:
    vertices = []
    for ring in rings:
        vertices.extend(ring_point(surface_body, side, ring, 2.0 * math.pi * index / SEGMENTS)
                        for index in range(SEGMENTS))

    # Tarsal thickness follows the clean margin exactly, then moves inward and
    # contracts slightly.  This prevents a black infinitely thin cut edge.
    margin_start = (len(rings) - 1) * SEGMENTS
    for index in range(SEGMENTS):
        point = vertices[margin_start + index].copy()
        cx, _cy, cz = EYES[side]
        point.x = cx + (point.x - cx) * 0.975
        point.z = cz + (point.z - cz) * 0.955
        point.y += 0.00110
        vertices.append(point)

    faces = []
    ring_count = len(rings) + 1
    for ring_index in range(ring_count - 1):
        start = ring_index * SEGMENTS
        next_start = (ring_index + 1) * SEGMENTS
        for index in range(SEGMENTS):
            following = (index + 1) % SEGMENTS
            faces.append((start + index, start + following,
                          next_start + following, next_start + index))

    mesh = bpy.data.meshes.new(f"AevryndFemaleEye{side}CleanLidMesh_r54")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(body.data.materials[0])
    mesh.update()
    patch = bpy.data.objects.new(f"Eye_{side}_CleanEyelid_r54", mesh)
    bpy.context.collection.objects.link(patch)
    patch["aevrynd_layer"] = "face.eyelid.integrated_patch"
    patch["aevrynd_owner"] = "Aevrynd"
    patch["aevrynd_revision"] = "v249-mainline-clean-eyelid-r54"
    patch["aevrynd_topology"] = "48-segment orbital/lid/margin/tarsal quad rings"
    for polygon in mesh.polygons:
        polygon.use_smooth = True

    # Keep the patch in the same deformation system as the body.  All vertices
    # are in the rigid cranium region, so a full head weight is appropriate.
    group = patch.vertex_groups.new(name="head")
    group.add(list(range(len(mesh.vertices))), 1.0, "REPLACE")
    source_modifier = next((modifier for modifier in body.modifiers if modifier.type == "ARMATURE"), None)
    if source_modifier is not None:
        modifier = patch.modifiers.new("Aevrynd Clean Eyelid Deform", "ARMATURE")
        modifier.object = source_modifier.object
        modifier.use_deform_preserve_volume = source_modifier.use_deform_preserve_volume
    patches[side] = {
        "object": patch.name,
        "vertices": len(mesh.vertices),
        "faces": len(mesh.polygons),
    }

body["aevrynd_mainline_baseline"] = "v249"
body["aevrynd_face_revision"] = "v249-mainline-clean-eyelid-r54"
scene = bpy.context.scene
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "clean-eyelid-r54"
scene["aevrynd_release_state"] = "R54_STRICT_VISUAL_REVIEW_REQUIRED"

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
    "deleted_body_faces": deleted,
    "patches": patches,
    "segments_per_ring": SEGMENTS,
    "visible_aperture_width_mm": 20.9,
    "visible_aperture_upper_mm": 4.15,
    "visible_aperture_lower_mm": 3.05,
    "tarsal_depth_mm": 1.10,
    "rigged_to_head": True,
    "status": "STRICT_VISUAL_REVIEW_REQUIRED",
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_CLEAN_EYELID_R54=" + json.dumps(report, sort_keys=True))
