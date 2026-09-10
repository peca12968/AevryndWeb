import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.interpolate import poly_3d_calc


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-face-r38.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-clean-eyelid-r58.blend"
OUT = ROOT.parent / "Temp/female-realism/v249-mainline-clean-eyelid-r58"
OUT.mkdir(parents=True, exist_ok=True)
BODY = "AevryndFemaleBodyBaseV118"
EYES = {"L": (0.034528, -0.10087, 1.607765), "R": (-0.034443, -0.10077, 1.607765)}
GLOBES = {
    "L": {"center": (0.0345275, -0.1003675, 1.6077619), "radii": (0.0109505, 0.0121000, 0.0116765)},
    "R": {"center": (-0.0344431, -0.1001710, 1.6077617), "radii": (0.0108295, 0.0121000, 0.0116765)},
}
SEGMENTS = 48


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def asymmetric_ellipse(point, center, width, upper, lower):
    dx = (point.x - center[0]) / width
    height = upper if point.z >= center[2] else lower
    dz = (point.z - center[2]) / height
    return dx * dx + dz * dz


def surface_sample(surface, source_mesh, x, z):
    origin = Vector((x, -0.30, z))
    location, _normal, index, _distance = surface.ray_cast(origin, Vector((0.0, 1.0, 0.0)))
    if location is None:
        raise RuntimeError(f"No facial surface at x={x:.6f}, z={z:.6f}")
    polygon = source_mesh.polygons[index]
    coordinates = [source_mesh.vertices[vertex_index].co for vertex_index in polygon.vertices]
    weights = poly_3d_calc(coordinates, location)
    uv_data = source_mesh.uv_layers["UVMap"].data
    uv = Vector((0.0, 0.0))
    for weight, loop_index in zip(weights, polygon.loop_indices):
        uv += uv_data[loop_index].uv * weight
    return location.y, uv


def ring_point(surface, source_mesh, side, ring, theta):
    cx, _cy, cz = EYES[side]
    lateral_sign = 1.0 if side == "L" else -1.0
    sine = math.sin(theta)
    cosine = math.cos(theta)
    height = ring["upper"] if sine >= 0.0 else ring["lower"]
    x = cx + ring["width"] * cosine
    z = cz + height * sine + lateral_sign * ring["tilt"] * (x - cx)
    y, uv = surface_sample(surface, source_mesh, x, z)
    return Vector((x, y + ring["surface_offset"], z)), uv


def globe_front_y(side, x, z):
    (cx, cy, cz) = GLOBES[side]["center"]
    (rx, ry, rz) = GLOBES[side]["radii"]
    radius_term = max(0.015, 1.0 - ((x - cx) / rx) ** 2 - ((z - cz) / rz) ** 2)
    return cy - ry * math.sqrt(radius_term)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
body = bpy.data.objects[BODY]
# Preserve an untouched geometry snapshot for surface projection after the body
# aperture faces have been removed.  It does not enter the scene or the output.
source_mesh = body.data
surface_body = BVHTree.FromPolygons(
    [vertex.co.copy() for vertex in source_mesh.vertices],
    [[vertex_index for vertex_index in polygon.vertices] for polygon in source_mesh.polygons],
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
            face.calc_center_median(), center, 0.0170, 0.00700, 0.00540
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
     "tilt": 0.030, "surface_offset": -0.00024},
    {"name": "lid_plane", "width": 0.0137, "upper": 0.00555, "lower": 0.00410,
     "tilt": 0.026, "surface_offset": -0.00022},
    {"name": "lid_margin", "width": 0.01000, "upper": 0.00370, "lower": 0.00280,
     "tilt": 0.023, "surface_offset": -0.00030},
)

patches = {}
for side in EYES:
    vertices = []
    vertex_uvs = []
    for index in range(SEGMENTS):
        theta = 2.0 * math.pi * index / SEGMENTS
        outer, outer_uv = ring_point(surface_body, source_mesh, side, rings[0], theta)
        lid, lid_uv = ring_point(surface_body, source_mesh, side, rings[1], theta)
        margin, margin_uv = ring_point(surface_body, source_mesh, side, rings[2], theta)
        margin.y = globe_front_y(side, margin.x, margin.z) - 0.00022
        # The lid body bridges from the unchanged orbital surface to the globe-
        # fitted margin.  This removes the 29mm upper/lower depth discontinuity.
        lid.y = 0.43 * outer.y + 0.57 * margin.y - 0.00018
        # The closed eye cap occupies a deliberately black region of the old UV
        # atlas.  Carry the valid surrounding skin sample radially inward.
        for point, uv in ((outer, outer_uv), (lid, outer_uv), (margin, outer_uv)):
            vertices.append(point)
            vertex_uvs.append(uv)

    # Convert the per-angle interleaving above back to contiguous rings.
    order = [ring * SEGMENTS + index for ring in range(3) for index in range(SEGMENTS)]
    interleaved_vertices = vertices
    interleaved_uvs = vertex_uvs
    vertices = [interleaved_vertices[index * 3 + ring] for ring in range(3) for index in range(SEGMENTS)]
    vertex_uvs = [interleaved_uvs[index * 3 + ring] for ring in range(3) for index in range(SEGMENTS)]

    # Tarsal thickness follows the clean margin exactly, then moves inward and
    # contracts slightly.  This prevents a black infinitely thin cut edge.
    margin_start = (len(rings) - 1) * SEGMENTS
    for index in range(SEGMENTS):
        point = vertices[margin_start + index].copy()
        cx, _cy, cz = EYES[side]
        point.x = cx + (point.x - cx) * 0.975
        point.z = cz + (point.z - cz) * 0.955
        point.y += 0.00085
        vertices.append(point)
        vertex_uvs.append(vertex_uvs[margin_start + index].copy())

    faces = []
    ring_count = len(rings) + 1
    for ring_index in range(ring_count - 1):
        start = ring_index * SEGMENTS
        next_start = (ring_index + 1) * SEGMENTS
        for index in range(SEGMENTS):
            following = (index + 1) % SEGMENTS
            faces.append((start + index, start + following,
                          next_start + following, next_start + index))

    mesh = bpy.data.meshes.new(f"AevryndFemaleEye{side}CleanLidMesh_r58")
    mesh.from_pydata(vertices, [], faces)
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        uv_layer.data[loop.index].uv = vertex_uvs[loop.vertex_index]
    lid_material = body.data.materials[0].copy()
    lid_material.name = f"Aevrynd_EyelidSkin_{side}_r58"
    principled = next(node for node in lid_material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    base_color = principled.inputs["Base Color"]
    for link in tuple(base_color.links):
        lid_material.node_tree.links.remove(link)
    measured_skin = {
        "L": (0.68134, 0.48552, 0.41999, 1.0),
        "R": (0.66958, 0.47755, 0.41316, 1.0),
    }
    base_color.default_value = measured_skin[side]
    roughness = principled.inputs["Roughness"]
    for link in tuple(roughness.links):
        lid_material.node_tree.links.remove(link)
    roughness.default_value = 0.47
    mesh.materials.append(lid_material)
    mesh.update()
    patch = bpy.data.objects.new(f"Eye_{side}_CleanEyelid_r58", mesh)
    bpy.context.collection.objects.link(patch)
    patch["aevrynd_layer"] = "face.eyelid.integrated_patch"
    patch["aevrynd_owner"] = "Aevrynd"
    patch["aevrynd_revision"] = "v249-mainline-clean-eyelid-r58"
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
body["aevrynd_face_revision"] = "v249-mainline-clean-eyelid-r58"
scene = bpy.context.scene
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_mainline_revision"] = "clean-eyelid-r58"
scene["aevrynd_release_state"] = "R58_STRICT_VISUAL_REVIEW_REQUIRED"

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
    "visible_aperture_width_mm": 20.0,
    "visible_aperture_upper_mm": 3.70,
    "visible_aperture_lower_mm": 2.80,
    "tarsal_depth_mm": 0.85,
    "rigged_to_head": True,
    "status": "STRICT_VISUAL_REVIEW_REQUIRED",
}
(OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_V249_CLEAN_EYELID_R58=" + json.dumps(report, sort_keys=True))
