"""Fit owned r584 hair/eyebrow/eyelash layers to the r962 CC0 rig foundation.

This is an isolated visual and collision study.  It never replaces the website
asset and deliberately converts the imported layers to rigid head-bound meshes
before later secondary-motion rigging.
"""

import json
from pathlib import Path

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-knee-crease-volume-r962.blend"
FEATURE_SOURCE = ASSETS / "aevrynd-female-authoring-v249-mainline-balanced-collision-safe-hair-r584.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-hair-feature-fit-r974.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-hair-feature-fit-r974.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r974-cc0-hair-feature-fit"
RIG = "AevryndFemaleRig"
BODY = "AevryndFemaleCC0Baseline_v259"
HAIR = (
    "AevryndFemaleRuntimeHairlineDensity_R467",
    "AevryndFemaleRuntimeScalpCap_R467",
    "AevryndFemaleTangentOuterHairCards_R584",
)
BROWS_LASHES = (
    "Brow_L",
    "Brow_L_Density",
    "Brow_R",
    "Brow_R_Density",
    "Eye_L_LowerLashes",
    "Eye_L_UpperLashes",
    "Eye_R_LowerLashes",
    "Eye_R_UpperLashes",
)

# Hair follows the new cranium bounds; face features follow measured eye centers.
HAIR_SCALE = Vector((1.02, 1.0, 1.0))
HAIR_OFFSET = Vector((0.0, -0.028, -0.047))
SOURCE_EYE_CENTER = Vector((0.0, -0.099762, 1.607765))
TARGET_EYE_CENTER = Vector((0.0, -0.107248, 1.448946))
FEATURE_SCALE = Vector((0.816, 0.907, 0.900))
CLEARANCE_M = 0.00075


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def body_tree(obj):
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


def append_objects(names):
    with bpy.data.libraries.load(str(FEATURE_SOURCE), link=False) as (data_from, data_to):
        missing = [name for name in names if name not in data_from.objects]
        if missing:
            raise RuntimeError(f"Missing feature objects: {missing}")
        data_to.objects = list(names)
    appended = []
    for obj in data_to.objects:
        if obj is None:
            continue
        if obj.name not in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.link(obj)
        appended.append(obj)
    return appended


def transform_world(point, feature):
    if feature:
        delta = point - SOURCE_EYE_CENTER
        return TARGET_EYE_CENTER + Vector((
            delta.x * FEATURE_SCALE.x,
            delta.y * FEATURE_SCALE.y,
            delta.z * FEATURE_SCALE.z,
        ))
    return Vector((point.x * HAIR_SCALE.x, point.y * HAIR_SCALE.y, point.z * HAIR_SCALE.z)) + HAIR_OFFSET


def fit_mesh(obj, target_rig, surface, feature=False):
    if obj.type != "MESH":
        raise RuntimeError(f"Expected mesh feature, got {obj.type}: {obj.name}")
    source_matrix = obj.matrix_world.copy()
    transformed = [transform_world(source_matrix @ vertex.co, feature) for vertex in obj.data.vertices]
    corrected = 0
    maximum_correction = 0.0
    if not feature:
        for index, point in enumerate(transformed):
            hit = surface.find_nearest(point, 0.025)
            if hit is None or hit[1] is None:
                continue
            nearest, normal, _face, _distance = hit
            signed = (point - nearest).dot(normal.normalized())
            if signed >= CLEARANCE_M:
                continue
            delta = normal.normalized() * (CLEARANCE_M - signed)
            transformed[index] = point + delta
            corrected += 1
            maximum_correction = max(maximum_correction, delta.length)
    for modifier in list(obj.modifiers):
        obj.modifiers.remove(modifier)
    obj.parent = None
    obj.matrix_world = Matrix.Identity(4)
    for vertex, point in zip(obj.data.vertices, transformed):
        vertex.co = point
    obj.data.update()
    world = obj.matrix_world.copy()
    obj.parent = target_rig
    # Keep the study in rig-object space.  Bone parenting is intentionally
    # deferred until the static fit passes; assigning the source world-space
    # vertices directly to a bone parent applies the head rest transform twice.
    obj.parent_type = "OBJECT"
    obj.parent_bone = ""
    obj.matrix_parent_inverse = target_rig.matrix_world.inverted()
    obj.matrix_world = world
    obj["aevrynd_layer"] = (
        "face.feature.static_fit" if feature else "hair.static_fit"
    )
    obj["aevrynd_revision"] = "v249r974"
    obj["aevrynd_source"] = FEATURE_SOURCE.name
    obj["aevrynd_runtime_dependency"] = "none"
    return {
        "name": obj.name,
        "vertices": len(obj.data.vertices),
        "polygons": len(obj.data.polygons),
        "clearanceCorrectedVertices": corrected,
        "maximumClearanceCorrectionM": maximum_correction,
    }


def render(scene, camera, name, location, target, lens):
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
rig = bpy.data.objects[RIG]
surface = body_tree(bpy.data.objects[BODY])
objects = append_objects(HAIR + BROWS_LASHES)
records = [fit_mesh(obj, rig, surface, obj.name in BROWS_LASHES) for obj in objects]

scene["aevrynd_mainline_revision"] = "v249r974-cc0-hair-feature-fit"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "STATIC_VISUAL_AND_COLLISION_STUDY_ONLY"
scene["aevrynd_skin_luminance_reference"] = "website-v83=0.545; committed-mainline=0.578"
scene["aevrynd_website_promotion"] = "forbidden pending strict gates and user approval"

scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects.get("Aevrynd R249 Review Camera") or bpy.data.objects.get("Aevrynd Review Camera")
if camera is None:
    camera_data = bpy.data.cameras.new("Aevrynd R974 Review Camera Data")
    camera = bpy.data.objects.new("Aevrynd R974 Review Camera", camera_data)
    scene.collection.objects.link(camera)
scene.camera = camera
for args in (
    ("01-face-front", (0.0, -0.68, 1.49), (0.0, -0.055, 1.48), 88),
    ("02-face-three-quarter", (0.42, -0.58, 1.51), (0.0, -0.045, 1.48), 88),
    ("03-face-profile", (0.68, -0.02, 1.50), (0.0, -0.035, 1.48), 90),
    ("04-hair-back", (0.0, 0.76, 1.50), (0.0, -0.01, 1.48), 86),
    ("05-hair-top", (0.0, -0.18, 2.05), (0.0, -0.02, 1.57), 82),
):
    render(scene, camera, *args)

report = {
    "source": str(SOURCE),
    "featureSource": str(FEATURE_SOURCE),
    "output": str(OUTPUT),
    "hairScale": list(HAIR_SCALE),
    "hairOffsetM": list(HAIR_OFFSET),
    "sourceEyeCenterM": list(SOURCE_EYE_CENTER),
    "targetEyeCenterM": list(TARGET_EYE_CENTER),
    "featureScale": list(FEATURE_SCALE),
    "clearanceM": CLEARANCE_M,
    "objects": records,
    "ownedAssetOnly": True,
    "runtimeDependency": "none",
    "websitePromotionApproved": False,
    "status": "STRICT_VISUAL_AND_COLLISION_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R974_HAIR_FEATURE_FIT=" + json.dumps(report, sort_keys=True))
