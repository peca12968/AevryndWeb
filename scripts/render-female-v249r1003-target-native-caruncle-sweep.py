"""Create and sweep owned, head-bound medial caruncle layers on r1001."""

import json
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets-source/aevrynd-character"
SOURCE = ASSETS / "aevrynd-female-cc0-mixed-space-eyelid-relief-r1001.blend"
OUTPUT = ASSETS / "aevrynd-female-cc0-target-native-caruncle-r1003-study.blend"
REPORT = ASSETS / "female-v249-mainline-cc0-target-native-caruncle-r1003.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r1003-target-native-caruncle"
BODY = "AevryndFemaleCC0Baseline_v259"
VARIANTS = (
    ("a-none", 0.0, 0.0, 0.0, 0.01725),
    ("b-small", 0.00100, 0.00028, 0.00060, 0.01725),
    ("c-medium", 0.00145, 0.00034, 0.00075, 0.01755),
    ("d-large", 0.00190, 0.00040, 0.00090, 0.01785),
)
VIEWS = (
    ("front", (0.0, -0.48, 1.485), (0.0, -0.060, 1.485)),
    ("three-quarter-left", (0.155, -0.445, 1.485), (0.0, -0.060, 1.480)),
    ("three-quarter-right", (-0.155, -0.445, 1.485), (0.0, -0.060, 1.480)),
)


def world_tree(obj):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    polygons = [tuple(poly.vertices) for poly in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, polygons, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def look_at(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def create_caruncle(side, material, rig):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=1.0)
    obj = bpy.context.object
    obj.name = f"Eye_{side}_Caruncle_R1003"
    obj.data.name = f"Aevrynd_TargetNativeCaruncle_{side}_R1003"
    obj.data.materials.append(material)
    obj.location = (0.01755 if side == "L" else -0.01755, -0.12115, 1.4490)
    obj.scale = (0.00145, 0.00034, 0.00075)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    world = obj.matrix_world.copy()
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "head"
    obj.matrix_world = world
    obj["aevrynd_revision"] = "v249r1003-target-native-caruncle-study"
    obj["aevrynd_layer"] = "caruncle"
    obj["aevrynd_ownership"] = "procedural-in-project"
    return obj


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
bpy.context.view_layer.update()
rig = bpy.data.objects["AevryndFemaleRig"]

material = bpy.data.materials.get("Aevrynd_TargetNativeCaruncle_R1003") or bpy.data.materials.new(
    "Aevrynd_TargetNativeCaruncle_R1003"
)
material.use_nodes = True
shader = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
shader.inputs["Base Color"].default_value = (0.22, 0.055, 0.045, 1.0)
shader.inputs["Roughness"].default_value = 0.52
shader.inputs["Specular IOR Level"].default_value = 0.18
shader.inputs["Subsurface Weight"].default_value = 0.035
material["aevrynd_ownership"] = "procedural-in-project"

objects = {side: create_caruncle(side, material, rig) for side in ("L", "R")}
RENDER_DIR.mkdir(parents=True, exist_ok=True)
scene.render.resolution_x = scene.render.resolution_y = 800
camera = scene.camera
camera.data.lens = 105

hidden = []
for obj in scene.objects:
    if obj.name.startswith(("Groom_", "AevryndFemaleTargetScalp")) or obj.type in {"CURVES", "CURVE"}:
        if not obj.hide_render:
            obj.hide_render = True
            hidden.append(obj.name)

results = []
for label, rx, ry, rz, center_abs_x in VARIANTS:
    for side, obj in objects.items():
        obj.hide_render = rx == 0.0
        obj.location.x = center_abs_x if side == "L" else -center_abs_x
        if rx:
            # Geometry was applied at the medium bound; scale relative to it.
            obj.scale = (rx / 0.00145, ry / 0.00034, rz / 0.00075)
        else:
            obj.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()
    collisions = {}
    if rx:
        body_tree = world_tree(bpy.data.objects[BODY])
        for side, obj in objects.items():
            caruncle_tree = world_tree(obj)
            collisions[side] = {
                "body": len(body_tree.overlap(caruncle_tree)),
                "sclera": len(world_tree(bpy.data.objects[f"Eye_{side}_Sclera"]).overlap(caruncle_tree)),
                "cornea": len(world_tree(bpy.data.objects[f"Eye_{side}_Cornea"]).overlap(caruncle_tree)),
                "upperLashes": len(world_tree(bpy.data.objects[f"Eye_{side}_UpperLashes"]).overlap(caruncle_tree)),
                "lowerLashes": len(world_tree(bpy.data.objects[f"Eye_{side}_LowerLashes"]).overlap(caruncle_tree)),
            }
    rendered = []
    for view_name, location, target in VIEWS:
        camera.location = location
        look_at(camera, target)
        path = RENDER_DIR / f"{label}-{view_name}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        rendered.append(str(path))
    total = sum(value for side in collisions.values() for value in side.values())
    results.append(
        {
            "label": label,
            "radiiM": [rx, ry, rz],
            "centerAbsXM": center_abs_x,
            "triangleOverlaps": collisions,
            "totalTriangleOverlaps": total,
            "rendered": rendered,
            "status": "PASS" if total == 0 else "FAIL",
        }
    )

for name in hidden:
    bpy.data.objects[name].hide_render = False
for obj in objects.values():
    obj.hide_render = False
scene["aevrynd_mainline_revision"] = "v249r1003-target-native-caruncle-study"
scene["aevrynd_mainline_parent"] = SOURCE.name
scene["aevrynd_release_state"] = "STUDY_ONLY_VISUAL_REVIEW_REQUIRED"
scene["aevrynd_website_promotion"] = "forbidden"
report = {
    "source": str(SOURCE),
    "output": str(OUTPUT),
    "objects": [obj.name for obj in objects.values()],
    "material": material.name,
    "variants": results,
    "selected": None,
    "status": "VISUAL_REVIEW_REQUIRED",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
print("AEVRYND_R1003_TARGET_NATIVE_CARUNCLE=" + json.dumps(report, sort_keys=True))
