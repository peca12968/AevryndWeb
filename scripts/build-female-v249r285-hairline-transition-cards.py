import json
import math
import random
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-safe-tip-transition-r284.blend"
OUTPUT = ROOT / "assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-hairline-transition-cards-r285.blend"
REPORT = ROOT / "assets-source/aevrynd-character/female-v249-mainline-hairline-transition-cards-r285.build-report.json"
RENDER_DIR = ROOT.parent / "Temp/female-realism/v249r285-hairline-transition-cards"
BODY = "AevryndFemaleBody_CC0_R249"
RIG = "AevryndFemaleRig"
HAIRLINE = "AevryndFemaleHairlineTransitionCards_R285"
POINTS = 12


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def smoothstep(value):
    value = clamp(value)
    return value * value * (3.0 - 2.0 * value)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def evaluated_body_tree(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    evaluated = body.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    vertices = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    faces = [tuple(polygon.vertices) for polygon in mesh.polygons]
    evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=False)


def surface_point(tree, x, z):
    hit = tree.ray_cast(Vector((x, -0.30, z)), Vector((0.0, 1.0, 0.0)), 0.50)
    if hit[0] is None or hit[1] is None:
        nearest = tree.find_nearest(Vector((x, -0.10, z)), 0.12)
        if nearest is None or nearest[0] is None or nearest[1] is None:
            raise RuntimeError(f"hairline surface sample failed: x={x}, z={z}")
        return nearest[0], nearest[1].normalized()
    return hit[0], hit[1].normalized()


def build_hairline(body, rig):
    tree = evaluated_body_tree(body)
    rng = random.Random(285032)
    paths, normals, metadata = [], [], []
    for side in (-1.0, 1.0):
        for index in range(16):
            fraction = (index + 0.65) / 16.0
            x0 = side * (0.0075 + fraction * 0.079) + rng.uniform(-0.0015, 0.0015)
            edge_z = 1.686 - 0.046 * (abs(x0) / 0.088) ** 1.55 + rng.uniform(-0.0028, 0.0028)
            span = rng.uniform(0.043, 0.068)
            path, path_normals = [], []
            # Build from dense crown root (UV v=0) toward the feathered forehead tip (v=1).
            for point_index in range(POINTS):
                t = point_index / (POINTS - 1)
                z = edge_z + span * (1.0 - t)
                x = x0 + side * 0.0055 * math.sin(math.pi * (1.0 - t))
                position, normal = surface_point(tree, x, z)
                path.append(position + normal * 0.0014)
                path_normals.append(normal)
            paths.append(path)
            normals.append(path_normals)
            metadata.append({"side": "L" if side < 0 else "R", "edgeX": x0, "edgeZ": edge_z, "lengthM": span})
    vertices, faces = [], []
    for card_index, (path, path_normals) in enumerate(zip(paths, normals)):
        base_width = 0.0030 + 0.0005 * ((card_index * 7) % 5) / 4.0
        for point_index, (point, normal) in enumerate(zip(path, path_normals)):
            before = path[max(0, point_index - 1)]
            after = path[min(POINTS - 1, point_index + 1)]
            tangent = (after - before).normalized()
            side = tangent.cross(normal)
            if side.length < 1e-5:
                side = Vector((1.0, 0.0, 0.0))
            side.normalize()
            t = point_index / (POINTS - 1)
            width = base_width * (1.0 - 0.86 * smoothstep((t - 0.52) / 0.48))
            vertices.extend((point - side * width, point + side * width))
        base = card_index * POINTS * 2
        for point_index in range(POINTS - 1):
            a = base + point_index * 2
            faces.append((a, a + 1, a + 3, a + 2))
    mesh = bpy.data.meshes.new("AevryndFemaleHairlineTransitionTopology_R285")
    inverse = body.matrix_world.inverted()
    mesh.from_pydata([inverse @ point for point in vertices], [], faces)
    mesh.materials.append(bpy.data.materials["Aevrynd_RuntimeHairCards_DenseAlpha_R276"])
    uv = mesh.uv_layers.new(name="AevryndHairlineTransitionUV")
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            local = mesh.loops[loop_index].vertex_index % (POINTS * 2)
            uv.data[loop_index].uv = (float(local % 2), (local // 2) / (POINTS - 1))
    uv.active_render = True
    obj = bpy.data.objects.new(HAIRLINE, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = rig
    obj.parent_type = body.parent_type
    obj.matrix_parent_inverse = body.matrix_parent_inverse.copy()
    obj.matrix_basis = body.matrix_basis.copy()
    group = obj.vertex_groups.new(name="head")
    group.add(list(range(len(vertices))), 1.0, "REPLACE")
    modifier = obj.modifiers.new("Aevrynd Hairline Head Binding", "ARMATURE")
    modifier.object = rig
    obj["aevrynd_layer"] = "hair.hairline_transition.head_bound"
    obj["aevrynd_revision"] = "v249r285"
    obj["aevrynd_surface_clearance_m"] = 0.0014
    return obj, metadata


def clearance_audit(scene, body, layer):
    result = {}
    for frame in (1, 33, 61):
        scene.frame_set(frame)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
        tree = evaluated_body_tree(body)
        evaluated = layer.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        values = []
        for vertex in mesh.vertices:
            world = evaluated.matrix_world @ vertex.co
            hit = tree.find_nearest(world, 0.05)
            if hit is not None and hit[1] is not None:
                values.append((world - hit[0]).dot(hit[1].normalized()))
        evaluated.to_mesh_clear()
        result[str(frame)] = {"samples": len(values), "minimumSignedM": min(values), "maximumSignedM": max(values), "penetratingVertices": sum(value < 0.0 for value in values)}
    return result


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
body = bpy.data.objects[BODY]
hairline, cards = build_hairline(body, bpy.data.objects[RIG])
audit = clearance_audit(scene, body, hairline)
failures = [{"frame": frame, "penetratingVertices": values["penetratingVertices"]} for frame, values in audit.items() if values["penetratingVertices"]]
scene["aevrynd_mainline_revision"] = "v249r285-hairline-transition-cards"
scene["aevrynd_hair_layers"] = "scalp_underlayer|runtime_dynamic_cards|hairline_transition.head_bound|flyaways"
scene["aevrynd_release_state"] = "HAIRLINE_TRANSITION_PENDING_VISUAL_REVIEW" if not failures else "HAIRLINE_TRANSITION_COLLISION_FAIL"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = scene.render.resolution_y = 800
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
    "source": str(SOURCE), "output": str(OUTPUT), "hairlineObject": HAIRLINE,
    "cards": len(cards), "pointsPerCard": POINTS, "vertices": len(hairline.data.vertices), "faces": len(hairline.data.polygons),
    "centralPartHalfWidthM": 0.0075, "surfaceClearanceM": 0.0014, "cardMetadata": cards,
    "clearanceAudit": audit, "failures": failures, "ownedAssetOnly": True,
    "renderDirectory": str(RENDER_DIR), "status": "PASS_PENDING_VISUAL_REVIEW" if not failures else "FAIL",
}
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("AEVRYND_V249R285_HAIRLINE_TRANSITION_CARDS=" + json.dumps(report, sort_keys=True))
if failures:
    raise SystemExit(2)
