import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-canthus-fitted-wedge-r345.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-broad-medial-transition-r417.study.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r417-broad-medial-transition-sweep"
BODY = "AevryndFemaleBody_CC0_R249"
EYES = {"L": (0.034528, 1.607765, 1.0), "R": (-0.034443, 1.607765, -1.0)}
OUTER_HALF = 0.01025
RECESS = 0.0008
VARIANTS = (
    ("a-broad-2p1mm", 1.10),
    ("b-broad-2p7mm", 1.13),
    ("c-broad-3p3mm", 1.16),
)


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def gaussian(value, sigma):
    return math.exp(-0.5 * (value / sigma) ** 2)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def world_bvh(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    tree = BVHTree.FromPolygons(vertices, faces, all_triangles=False)
    evaluated.to_mesh_clear()
    return tree


def make_body(source, name):
    obj = bpy.data.objects.new(name, source.data.copy())
    bpy.context.scene.collection.objects.link(obj)
    obj.matrix_world = source.matrix_world.copy()
    for modifier in source.modifiers:
        copied = obj.modifiers.new(modifier.name, modifier.type)
        for prop in modifier.bl_rna.properties:
            if prop.is_readonly or prop.identifier in {"name", "type", "rna_type"}:
                continue
            try:
                setattr(copied, prop.identifier, getattr(modifier, prop.identifier))
            except (AttributeError, TypeError):
                pass
    return obj


def mapped_x(x, cx, sign, scale):
    outer = cx + sign * OUTER_HALF
    return outer + (x - outer) * scale


def sculpt_medial_aperture(body, scale):
    inverse = body.matrix_world.inverted()
    moved = {"L": 0, "R": 0}
    maximum = 0.0
    for vertex in body.data.vertices:
        world = body.matrix_world @ vertex.co
        if not (-0.158 <= world.y <= -0.106) or not (1.588 <= world.z <= 1.627):
            continue
        side = min(EYES, key=lambda key: abs(world.x - EYES[key][0]))
        cx, cz, sign = EYES[side]
        u = sign * (world.x - cx)
        if not (-0.032 <= u <= 0.018):
            continue
        # Blend across the medial orbital wall and nasal bridge.  The narrow
        # r416 transition ended at the canthus and produced a vertical crease.
        inner_fade = smoothstep((u + 0.032) / 0.024)
        outer_fade = 1.0 - smoothstep((u - 0.011) / 0.007)
        weight = (
            gaussian(world.y + 0.132, 0.017)
            * gaussian(world.z - cz, 0.0105)
            * inner_fade
            * outer_fade
        )
        if weight < 0.002:
            continue
        before = world.copy()
        world.x += (mapped_x(world.x, cx, sign, scale) - world.x) * weight
        vertex.co = inverse @ world
        moved[side] += 1
        maximum = max(maximum, (world - before).length)
    body.data.update()
    return {"movedVertices": moved, "maximumDisplacementM": maximum}


def layer_names():
    return [
        name
        for side in EYES
        for name in (
            f"AevryndEye_{side}_Sclera_R249",
            f"AevryndEye_{side}_Caruncle_R258",
            f"AevryndEye_{side}_UpperLidMargin_R258",
            f"AevryndEye_{side}_LowerLidMargin_R258",
            f"AevryndEye_{side}_TearMeniscus_R258",
            f"AevryndFemaleUpperLashes_{side}_R256",
            f"AevryndFemaleLowerLashes_{side}_R256",
        )
    ]


def snapshot_curve(obj):
    return [point.co.copy() for spline in obj.data.splines for point in spline.points]


def snapshot_mesh(obj):
    return [vertex.co.copy() for vertex in obj.data.vertices]


def restore_and_fit_layers(scale, matrices, geometry):
    report = {}
    for name in layer_names():
        obj = bpy.data.objects[name]
        obj.matrix_world = matrices[name].copy()
        side = "L" if "_L_" in name or name.endswith("_L_R256") else "R"
        cx, _, sign = EYES[side]
        shift = OUTER_HALF * (scale - 1.0)
        if obj.type == "MESH":
            for vertex, original in zip(obj.data.vertices, geometry[name]):
                vertex.co = original.copy()
            obj.data.update()
        else:
            point_index = 0
            for spline in obj.data.splines:
                for point in spline.points:
                    point.co = geometry[name][point_index].copy()
                    point_index += 1

        if "_Sclera_" in name:
            obj.matrix_world.translation.x -= sign * shift
            obj.matrix_world.translation.y += RECESS
            report[name] = {"centerShiftM": shift, "recessM": RECESS}
            continue

        inverse = obj.matrix_world.inverted()
        moved = 0
        maximum = 0.0
        if obj.type == "MESH":
            elements = obj.data.vertices
        else:
            elements = [point for spline in obj.data.splines for point in spline.points]
        for element in elements:
            world = obj.matrix_world @ element.co
            target = world.copy()
            target.x = mapped_x(world.x, cx, sign, scale)
            target.y += RECESS
            element.co = inverse @ target
            moved += 1
            maximum = max(maximum, (target - world).length)
        if obj.type == "MESH":
            obj.data.update()
        report[name] = {"elementsMoved": moved, "maximumDisplacementM": maximum, "recessM": RECESS}
    return report


def setup_neutral_review(scene):
    for obj in list(bpy.data.objects):
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)
    for name, location, energy, size in (
        ("Aevrynd Neutral Key R416", (-0.42, -0.82, 1.82), 39.0, 0.56),
        ("Aevrynd Neutral Fill R416", (0.48, -0.62, 1.70), 24.0, 0.68),
        ("Aevrynd Neutral Top R416", (0.0, -0.08, 2.28), 22.0, 0.52),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.color = (1.0, 1.0, 1.0)
        data.shape = "DISK"
        data.size = size
        obj = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(obj)
        obj.location = location
        look_at(obj, (0.0, -0.025, 1.60))
    world = scene.world or bpy.data.worlds.new("Aevrynd Neutral World R416")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background is None:
        world.node_tree.nodes.clear()
        background = world.node_tree.nodes.new("ShaderNodeBackground")
        output = world.node_tree.nodes.new("ShaderNodeOutputWorld")
        world.node_tree.links.new(background.outputs["Background"], output.inputs["Surface"])
    background.inputs["Color"].default_value = (0.018, 0.018, 0.018, 1.0)
    background.inputs["Strength"].default_value = 0.35


def hide_large_hair():
    hidden = []
    preserve = ("brow", "lash", "lid", "tear", "caruncle", "eye")
    for obj in bpy.data.objects:
        name = obj.name.lower()
        if any(token in name for token in preserve):
            continue
        material_names = ""
        if obj.type in {"MESH", "CURVE", "CURVES"}:
            material_names = " ".join(m.name.lower() for m in getattr(obj.data, "materials", ()) if m)
        if any(token in name + " " + material_names for token in ("hair", "scalp", "groom", "flyaway", "root", "lock", "fiber")):
            obj.hide_render = True
            hidden.append(obj.name)
    return sorted(hidden)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Base Contrast"
scene.view_settings.exposure = 0.0
setup_neutral_review(scene)
hidden_hair = hide_large_hair()
RENDER_DIR.mkdir(parents=True, exist_ok=True)

source_body = bpy.data.objects[BODY]
source_body.hide_render = True
names = layer_names()
matrices = {name: bpy.data.objects[name].matrix_world.copy() for name in names}
geometry = {}
for name in names:
    obj = bpy.data.objects[name]
    if obj.type == "MESH":
        obj.data = obj.data.copy()
        geometry[name] = snapshot_mesh(obj)
    else:
        obj.data = obj.data.copy()
        geometry[name] = snapshot_curve(obj)

camera = bpy.data.objects["Aevrynd R249 Review Camera"]
views = (
    ("face", (0.0, -0.68, 1.605), (0.0, -0.035, 1.606), 92),
    ("eyes", (0.0, -0.46, 1.615), (0.0, -0.035, 1.610), 105),
    ("three-quarter", (0.44, -0.63, 1.62), (0.0, -0.02, 1.595), 88),
)
metrics = {}
previous = None
for label, scale in VARIANTS:
    if previous is not None:
        bpy.data.objects.remove(previous, do_unlink=True)
    body = make_body(source_body, f"AevryndFemaleMedialAperture_{label}")
    edit = sculpt_medial_aperture(body, scale)
    layers = restore_and_fit_layers(scale, matrices, geometry)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    body_tree = world_bvh(body, depsgraph)
    overlaps = {}
    for side in EYES:
        sclera = bpy.data.objects[f"AevryndEye_{side}_Sclera_R249"]
        caruncle = bpy.data.objects[f"AevryndEye_{side}_Caruncle_R258"]
        overlaps[side] = {
            "bodyVsIntegratedEye": len(body_tree.overlap(world_bvh(sclera, depsgraph))),
            "bodyVsCaruncle": len(body_tree.overlap(world_bvh(caruncle, depsgraph))),
        }
    for view_name, location, target, lens in views:
        camera.location = location
        camera.data.lens = lens
        look_at(camera, target)
        scene.render.filepath = str(RENDER_DIR / f"{label}-{view_name}.png")
        bpy.ops.render.render(write_still=True)
    shift = OUTER_HALF * (scale - 1.0)
    metrics[label] = {
        "anchoredOuterScale": scale,
        "eyeCenterMedialShiftM": shift,
        "nominalInnerCanthusExtensionM": 2.0 * shift,
        "eyeLayerRecessM": RECESS,
        "bodyEdit": edit,
        "layerEdit": layers,
        "triangleOverlaps": overlaps,
    }
    previous = body

report = {
    "source": str(SOURCE),
    "renderDirectory": str(RENDER_DIR),
    "method": "Keep the outer canthus fixed, extend the medial aperture toward the nose with a broad orbital-wall/nasal-bridge transition, shift the ocular globe to the new aperture center, and continuously refit every lid, tear, lash and caruncle layer.",
    "neutralReviewRig": "r415 calibrated neutral white three-area-light rig with AgX Base Contrast",
    "hiddenHairObjects": hidden_hair,
    "variants": metrics,
    "status": "VISUAL_AND_COLLISION_REVIEW_PENDING",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_R417_BROAD_MEDIAL_TRANSITION_SWEEP=" + json.dumps(report, sort_keys=True))
