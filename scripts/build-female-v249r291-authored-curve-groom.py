import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-matte-root-underlayer-r287.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-authored-curve-groom-r291.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-authored-curve-groom-r291.build-report.json"
AUDIT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-authored-curve-groom-r291.clearance-audit.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r291-authored-curve-groom"
BODY = "AevryndFemaleBody_CC0_R249"
PRIMARY = "AevryndFemalePrimaryClumps_R264"
FILL = "AevryndFemaleSecondaryFill_R264"
FLY = "AevryndFemaleFlyaways_R264"
RUNTIME = "AevryndFemaleRuntimeHairCards_R276"
MATERIAL = "Aevrynd_PrincipledHair_CC0_R264"
POINTS = 24


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def rnd(index, salt=0.0):
    return (math.sin(index * 12.9898 + salt * 78.233) * 43758.5453) % 1.0


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def reshape_curves(obj, layer_scale):
    data = obj.data
    family_attribute = data.attributes.get("aevrynd_guide_family")
    if len(data.points) != len(data.curves) * POINTS:
        raise RuntimeError(f"unexpected point layout for {obj.name}")
    max_shift = 0.0
    for curve_index in range(len(data.curves)):
        family = family_attribute.data[curve_index].value if family_attribute else curve_index
        first = curve_index * POINTS
        root = data.points[first].position.copy()
        radial = Vector((root.x, root.y + 0.010, 0.0))
        if radial.length < 1e-6:
            radial = Vector((1.0, 0.0, 0.0))
        radial.normalize()
        circumferential = Vector((radial.y, -radial.x, 0.0))
        side = -1.0 if root.x < -0.004 else 1.0
        phase = rnd(family, 9.1) * math.tau
        macro_bend = (rnd(family, 9.7) - 0.5) * 0.010 * layer_scale
        volume = (0.0045 + 0.0055 * rnd(family, 10.2)) * layer_scale
        # Left and right intentionally differ, while every child sharing a
        # guide family follows the same large-scale lock direction.
        side_arc = (0.0085 if side < 0.0 else 0.0055) * (0.72 + 0.56 * rnd(family, 10.8)) * layer_scale
        tip_lift = (0.002 + 0.020 * rnd(family, 11.4)) * layer_scale
        for point_index in range(POINTS):
            point = data.points[first + point_index]
            original = point.position.copy()
            t = point_index / (POINTS - 1)
            envelope = math.sin(math.pi * t) ** 1.45
            displacement = radial * (volume * envelope)
            displacement += circumferential * macro_bend * envelope * math.sin(phase + t * math.pi * 1.25)
            if abs(root.x) > 0.025:
                displacement += Vector((side * side_arc * smoothstep((t - 0.18) / 0.70), 0.0, 0.0))
            displacement.z += tip_lift * smoothstep((t - 0.80) / 0.20)
            point.position = original + displacement
            max_shift = max(max_shift, displacement.length)
    data.update_tag()
    obj["aevrynd_revision"] = "v249r291"
    obj["aevrynd_authored_shape"] = "family-coherent asymmetry, volume and uneven tips"
    return {"curves": len(data.curves), "points": len(data.points), "maximumShiftM": max_shift}


def tune_material():
    material = bpy.data.materials[MATERIAL]
    hair = next(node for node in material.node_tree.nodes if node.type == "BSDF_HAIR_PRINCIPLED")
    hair.parametrization = "COLOR"
    hair.inputs["Color"].default_value = (0.0038, 0.00095, 0.00042, 1.0)
    hair.inputs["Roughness"].default_value = 0.34
    hair.inputs["Radial Roughness"].default_value = 0.62
    hair.inputs["Coat"].default_value = 0.055
    hair.inputs["IOR"].default_value = 1.54
    material["aevrynd_revision"] = "v249r291"
    material["aevrynd_role"] = "authored longitudinal fiber preview"
    return material


def body_tree(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def clearance_audit(scene, body, objects):
    results = {}
    failures = []
    for frame in (1, 33, 61):
        scene.frame_set(frame)
        tree = body_tree(body)
        frame_result = {}
        for obj in objects:
            evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
            values = []
            for point in evaluated.data.points:
                world = evaluated.matrix_world @ point.position
                hit = tree.find_nearest(world, 0.20)
                if hit is not None and hit[1] is not None:
                    values.append((world - hit[0]).dot(hit[1].normalized()))
            penetrating = sum(value < -0.00005 for value in values)
            frame_result[obj.name] = {
                "samples": len(values), "minimumSignedM": min(values),
                "penetratingBeyondTolerance": penetrating,
                "toleranceM": -0.00005,
            }
            if penetrating:
                failures.append({"frame": frame, "object": obj.name, "penetratingBeyondTolerance": penetrating})
        results[str(frame)] = frame_result
    return results, failures


def render(camera, frame, name, location):
    scene = bpy.context.scene
    scene.frame_set(frame)
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    camera.location = location
    camera.data.lens = 82
    look_at(camera, (0.0, 0.0, 1.56))
    bpy.ops.render.render(write_still=True)


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene = bpy.context.scene
scene.frame_set(1)
primary = bpy.data.objects[PRIMARY]
fill = bpy.data.objects[FILL]
fly = bpy.data.objects[FLY]
runtime = bpy.data.objects[RUNTIME]
primary.hide_render = primary.hide_viewport = False
fill.hide_render = fill.hide_viewport = False
fly.hide_render = fly.hide_viewport = False
runtime.hide_render = True
runtime.hide_viewport = False
shape_reports = {
    PRIMARY: reshape_curves(primary, 1.0),
    FILL: reshape_curves(fill, 0.88),
    FLY: reshape_curves(fly, 1.25),
}
material = tune_material()
scene["aevrynd_mainline_revision"] = "v249r291-authored-curve-groom"
scene["aevrynd_hair_layers"] = "scalp_underlayer|authored_primary_guides|authored_secondary_fibers|authored_flyaways|runtime_dynamic_card_proxy.hidden|hairline_transition"
scene["aevrynd_release_state"] = "AUTHORED_GROOM_CLEARANCE_AND_VISUAL_REVIEW_PENDING"
audit, failures = clearance_audit(scene, bpy.data.objects[BODY], [primary, fill, fly])
AUDIT.write_text(json.dumps({
    "model": str(OUTPUT), "frames": audit, "failures": failures,
    "status": "FAIL" if failures else "PASS",
    "scope": "visible authored curve groom against evaluated body; runtime dynamic proxy remains r287",
}, indent=2), encoding="utf-8")
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
RENDER_DIR.mkdir(parents=True, exist_ok=True)
camera = bpy.data.objects["Aevrynd R249 Review Camera"]
for frame, name, location in (
    (1, "front-f01", (0.0, -0.90, 1.59)), (33, "front-f33", (0.0, -0.90, 1.59)),
    (1, "left-f01", (-0.72, -0.55, 1.59)), (1, "right-f01", (0.72, -0.55, 1.59)),
    (1, "back-f01", (0.0, 0.90, 1.59)), (33, "back-f33", (0.0, 0.90, 1.59)),
):
    render(camera, frame, name, location)
scene.frame_set(1)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
report = {
    "source": str(SOURCE), "output": str(OUTPUT), "material": material.name,
    "visibleAuthoringLayers": [PRIMARY, FILL, FLY], "runtimeProxy": RUNTIME,
    "runtimeProxyPreserved": True, "runtimeProxyVisibleInViewport": True, "runtimeProxyVisibleInRender": False,
    "shapeReports": shape_reports, "clearanceAudit": str(AUDIT),
    "clearanceStatus": "FAIL" if failures else "PASS", "clearanceFailures": failures,
    "ownedAssetOnly": True, "renderDirectory": str(RENDER_DIR),
    "status": "VISUAL_REVIEW_PENDING" if not failures else "CLEARANCE_FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R291_AUTHORED_CURVE_GROOM=" + json.dumps(report, sort_keys=True))
