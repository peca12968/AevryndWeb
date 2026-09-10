import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-cc0-scalp-foundation-r101.blend"
OUT = ROOT.parent / "Temp/female-realism/v249r101-tear-meniscus-r109-sweep"
BODY = "AevryndFemaleBodyBaseV118"
EYES = {"L": (0.034528, -0.10087, 1.607765), "R": (-0.034443, -0.10077, 1.607765)}
VARIANTS = (("a-control", None), ("b-fine-060um", 0.000060), ("c-balanced-095um", 0.000095), ("d-strong-135um", 0.000135))


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def is_hair(obj):
    layer = str(obj.get("aevrynd_layer", ""))
    lower = obj.name.lower()
    return layer.startswith("hair.") or any(token in lower for token in ("hair", "groom", "scalp"))


def body_tree(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [vertex.co.copy() for vertex in mesh.vertices]
    faces = [tuple(poly.vertices) for poly in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(points, faces, all_triangles=False)


def lower_lid_edge(tree, x, aperture_z):
    # Walk down from the analytical aperture until the first real skin surface
    # is found. This follows the evaluated lower-lid boundary and never bridges
    # the open eye socket with a guessed straight segment.
    for step in range(1, 19):
        sample_z = aperture_z - step * 0.00035
        hit, _normal, _face, _distance = tree.ray_cast(
            Vector((x, -0.20, sample_z)), Vector((0.0, 1.0, 0.0)), 0.20
        )
        if hit is not None:
            return Vector((x, hit.y - 0.00010, sample_z + 0.00005))
    return None


def tear_material():
    material = bpy.data.materials.new("Aevrynd_TearMeniscus_Clear_R109")
    material.use_nodes = True
    material.surface_render_method = "DITHERED"
    node = next(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeBsdfPrincipled")
    node.inputs["Base Color"].default_value = (0.82, 0.91, 0.95, 1.0)
    node.inputs["Roughness"].default_value = 0.055
    node.inputs["IOR"].default_value = 1.336
    node.inputs["Transmission Weight"].default_value = 0.28
    node.inputs["Alpha"].default_value = 0.24
    node.inputs["Specular IOR Level"].default_value = 0.42
    node.inputs["Coat Weight"].default_value = 0.55
    node.inputs["Coat Roughness"].default_value = 0.035
    return material


def build_meniscus(side, center, tree, material, radius):
    cx, _cy, cz = center
    lateral = 1.0 if side == "L" else -1.0
    points = []
    for index in range(37):
        u = -0.88 + 1.76 * index / 36.0
        arc = math.sqrt(max(0.0, 1.0 - u * u))
        x = cx + 0.01045 * u
        tilt = lateral * 0.023 * (x - cx)
        edge_z = cz - 0.00282 * arc + tilt
        point = lower_lid_edge(tree, x, edge_z)
        if point is not None:
            points.append(point)
    curve = bpy.data.curves.new(f"Eye_{side}_TearMeniscus_R109", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 1
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    curve.resolution_u = 2
    spline = curve.splines.new("NURBS")
    spline.points.add(len(points) - 1)
    for target, point in zip(spline.points, points):
        target.co = (*point, 1.0)
    spline.order_u = min(3, len(points))
    spline.use_endpoint_u = True
    obj = bpy.data.objects.new(f"Eye_{side}_TearMeniscus_R109", curve)
    bpy.context.collection.objects.link(obj)
    curve.materials.append(material)
    obj["aevrynd_layer"] = "face.eye.tear-meniscus"
    obj["aevrynd_revision"] = "v249r101-tear-meniscus-r109"
    return {"points": len(points), "radius_um": radius * 1_000_000.0}


def render(camera, name, location, target, lens, size):
    scene = bpy.context.scene
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = str(OUT / f"{name}.png")
    bpy.ops.render.render(write_still=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}
    for label, radius in VARIANTS:
        bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
        scene = bpy.context.scene
        scene.frame_set(1)
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        for obj in bpy.data.objects:
            if is_hair(obj):
                obj.hide_render = True
        geometry = None
        if radius is not None:
            for side in ("L", "R"):
                bpy.data.objects[f"Eye_{side}_TearMeniscus"].hide_render = True
            tree = body_tree(bpy.data.objects[BODY])
            material = tear_material()
            geometry = {side: build_meniscus(side, EYES[side], tree, material, radius) for side in ("L", "R")}
        camera = bpy.data.objects["Aevrynd Review Camera"]
        render(camera, f"{label}-01-eyes-front", (0.0, -0.445, 1.611), (0.0, -0.076, 1.608), 132, (1280, 760))
        render(camera, f"{label}-02-left-eye-three-quarter", (0.225, -0.390, 1.628), (0.018, -0.080, 1.607), 138, (1100, 900))
        render(camera, f"{label}-03-face-front", (0.0, -0.555, 1.605), (0.0, -0.058, 1.604), 116, (1050, 1050))
        report[label] = geometry
    (OUT / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("AEVRYND_V249_R101_TEAR_MENISCUS_R109=" + json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
