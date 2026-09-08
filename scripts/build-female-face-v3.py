import json
import math
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v2.blend"
OUTPUT = ROOT / "assets-source" / "aevrynd-character" / "aevrynd-female-authoring-v3.blend"
BUILD = ROOT / ".character-build" / "aevrynd-female-authoring-v3.glb"
RENDER_DIR = ROOT.parent / "Temp" / "female-realism" / "face-v3"


def smoothstep(low, high, value):
    if high == low:
        return float(value >= high)
    t = max(0.0, min(1.0, (value - low) / (high - low)))
    return t * t * (3.0 - 2.0 * t)


def bell(center, radius, value):
    return max(0.0, 1.0 - abs(value - center) / radius)


def apply_identity(body):
    inverse = body.matrix_world.inverted()
    changed = 0
    max_delta = 0.0
    for vertex in body.data.vertices:
        source = body.matrix_world @ vertex.co
        target = source.copy()

        # Refine the broad silhouette first: a tapered jaw, supported cheekbones,
        # and a slightly more defined chin while preserving the scan asymmetry.
        jaw = bell(1.505, 0.065, source.z)
        if 1.44 < source.z < 1.57:
            target.x *= 1.0 - 0.045 * jaw
        cheek = bell(1.565, 0.035, source.z) * smoothstep(0.025, 0.065, abs(source.x))
        if abs(source.x) < 0.09:
            target.x += math.copysign(0.0022 * cheek, source.x or 1.0)

        # Primary facial planes. Only the front surface is affected.
        front = smoothstep(-0.09, -0.135, source.y)
        center = 1.0 - smoothstep(0.018, 0.05, abs(source.x))
        nose_bridge = bell(1.595, 0.035, source.z) * center * front
        nose_tip = bell(1.565, 0.022, source.z) * (1.0 - smoothstep(0.0, 0.028, abs(source.x))) * front
        lips = bell(1.525, 0.019, source.z) * (1.0 - smoothstep(0.02, 0.047, abs(source.x))) * front
        chin = bell(1.478, 0.025, source.z) * (1.0 - smoothstep(0.02, 0.052, abs(source.x))) * front
        target.y -= 0.0013 * nose_bridge + 0.0024 * nose_tip + 0.0011 * lips + 0.0012 * chin
        target.z -= 0.0013 * chin

        delta = (target - source).length
        if delta > 1e-7:
            vertex.co = inverse @ target
            changed += 1
            max_delta = max(max_delta, delta)
    body.data.update()
    body["aevrynd_identity_revision"] = 3
    body["aevrynd_identity_changed_vertices"] = changed
    body["aevrynd_identity_max_delta_m"] = max_delta
    return changed, max_delta


def add_skin_detail(body):
    material = body.data.materials[0]
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    shader = nodes.get("Principled BSDF")

    for node in list(nodes):
        if node.name.startswith("Aevrynd Skin"):
            nodes.remove(node)

    micro = nodes.new("ShaderNodeTexNoise")
    micro.name = "Aevrynd Skin Microstructure"
    micro.inputs["Scale"].default_value = 185.0
    micro.inputs["Detail"].default_value = 3.2
    micro.inputs["Roughness"].default_value = 0.72
    bump = nodes.new("ShaderNodeBump")
    bump.name = "Aevrynd Skin Micro Bump"
    bump.inputs["Strength"].default_value = 0.16
    bump.inputs["Distance"].default_value = 0.00022
    links.new(micro.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])

    rough = nodes.new("ShaderNodeTexNoise")
    rough.name = "Aevrynd Skin Roughness Variation"
    rough.inputs["Scale"].default_value = 32.0
    rough.inputs["Detail"].default_value = 2.0
    rough.inputs["Roughness"].default_value = 0.65
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.name = "Aevrynd Skin Roughness Range"
    ramp.color_ramp.elements[0].position = 0.25
    ramp.color_ramp.elements[0].color = (0.38, 0.38, 0.38, 1.0)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (0.58, 0.58, 0.58, 1.0)
    links.new(rough.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Roughness"])
    material["aevrynd_requires_runtime_bake"] = True


def make_hair_material(name, color, roughness):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Roughness"].default_value = roughness
    if shader.inputs.get("Coat Weight"):
        shader.inputs["Coat Weight"].default_value = 0.08
    return material


def evaluated_surface(body):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = body.evaluated_get(depsgraph)
    return BVHTree.FromObject(evaluated, depsgraph), body.matrix_world, body.matrix_world.inverted()


def surface_point(surface, x, z):
    tree, matrix, inverse = surface
    local_origin = inverse @ Vector((x, -0.35, z))
    local_direction = (inverse.to_3x3() @ Vector((0, 1, 0))).normalized()
    location, normal, _, _ = tree.ray_cast(local_origin, local_direction, 0.7)
    if location is None:
        return None
    world_location = matrix @ location
    world_normal = (matrix.inverted().transposed().to_3x3() @ normal).normalized()
    return world_location, world_normal


def tube_mesh(name, strands, material, sides=4):
    vertices = []
    faces = []
    for points, root_radius in strands:
        base = len(vertices)
        for index, point in enumerate(points):
            previous = points[max(0, index - 1)]
            following = points[min(len(points) - 1, index + 1)]
            tangent = (following - previous).normalized()
            reference = Vector((0, 0, 1)) if abs(tangent.z) < 0.85 else Vector((1, 0, 0))
            axis_a = tangent.cross(reference).normalized()
            axis_b = tangent.cross(axis_a).normalized()
            radius = root_radius * (1.0 - index / max(1, len(points) - 1)) + 0.000025
            for side in range(sides):
                angle = side * math.tau / sides
                vertices.append(point + axis_a * math.cos(angle) * radius + axis_b * math.sin(angle) * radius)
        for row in range(len(points) - 1):
            for side in range(sides):
                a = base + row * sides + side
                b = base + row * sides + (side + 1) % sides
                c = base + (row + 1) * sides + (side + 1) % sides
                d = base + (row + 1) * sides + side
                faces.append((a, b, c, d))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def build_brows_and_lashes(body):
    surface = evaluated_surface(body)
    brow_material = make_hair_material("Aevrynd_Brow_Hair", (0.022, 0.009, 0.004, 1), 0.48)
    lash_material = make_hair_material("Aevrynd_Lash_Hair", (0.006, 0.002, 0.001, 1), 0.42)
    created = []
    missed_roots = 0

    for side, eye_x in (("L", 0.034527), ("R", -0.034443)):
        brow_strands = []
        outward_sign = 1.0 if side == "L" else -1.0
        for index in range(184):
            t = index / 183 * 2.0 - 1.0
            flow = t if side == "L" else -t
            row = ((index * 0.61803398875) % 1.0) * 2.0 - 1.0
            taper = max(0.0, 1.0 - abs(flow) ** 1.45)
            x = eye_x + t * 0.0275
            z = 1.6305 + 0.0048 * (1.0 - flow * flow) + row * 0.0028 * taper
            hit = surface_point(surface, x, z)
            if not hit:
                missed_roots += 1
                continue
            root, normal = hit
            root += normal * 0.00012
            progress = (flow + 1.0) * 0.5
            length = 0.0031 + 0.0018 * taper + 0.00025 * math.sin(index * 2.37)
            direction = (
                normal * 0.16
                + Vector((outward_sign * (0.18 + 0.64 * progress), -0.12, 0.92 - 0.62 * progress))
            ).normalized()
            bend = Vector((outward_sign * 0.00035 * progress, -0.0002, -0.00022 * progress))
            brow_strands.append(
                ([root, root + direction * length * 0.52, root + direction * length + bend], 0.000062)
            )
        brow = tube_mesh(f"Brow_{side}", brow_strands, brow_material, 4)
        brow["aevrynd_role"] = "brow"
        created.append(brow)

        for upper in (True, False):
            lash_strands = []
            count = 34 if upper else 18
            for index in range(count):
                t = index / (count - 1) * 2.0 - 1.0
                x = eye_x + t * 0.0132
                arc = math.sqrt(max(0.0, 1.0 - t * t))
                z = 1.6078 + (0.0052 * arc if upper else -0.0040 * arc)
                hit = surface_point(surface, x, z)
                if not hit:
                    missed_roots += 1
                    continue
                root, normal = hit
                root += normal * 0.0001
                outward = Vector((t * 0.16, -1.0, 0.34 if upper else -0.12)).normalized()
                length = (0.0062 if upper else 0.0031) * (0.72 + 0.28 * arc)
                lash_strands.append(
                    ([root, root + outward * length * 0.52 + Vector((0, 0, 0.0004)), root + outward * length], 0.000115)
                )
            label = "UpperLashes" if upper else "LowerLashes"
            lashes = tube_mesh(f"Eye_{side}_{label}", lash_strands, lash_material, 4)
            lashes["aevrynd_role"] = "upper_lashes" if upper else "lower_lashes"
            created.append(lashes)

    for obj in created:
        obj["aevrynd_source"] = "Aevrynd authored on evaluated CC0 skin surface"
        obj["aevrynd_root_method"] = "multires_bvh_raycast"
    return created, missed_roots


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render(camera, name, location, target):
    camera.location = location
    look_at(camera, target)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDER_DIR / f"{name}.png")
    # The transparent cornea is exported and validated separately. Hide it in
    # this Eevee form review so refraction cannot obscure the iris layers.
    for obj in bpy.data.objects:
        if obj.get("aevrynd_role") == "cornea":
            obj.hide_render = True
    bpy.ops.render.render(write_still=True)


def export_runtime(body, authored):
    multires = next(m for m in body.modifiers if m.type == "MULTIRES")
    old = (multires.levels, multires.sculpt_levels, multires.render_levels)
    multires.levels = multires.sculpt_levels = multires.render_levels = 0
    bpy.ops.object.select_all(action="DESELECT")
    objects = [body] + [obj for obj in bpy.data.objects if obj.name.startswith("Eye_") or obj.name.startswith("Brow_")]
    for obj in objects:
        obj.hide_render = False
        obj.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.export_scene.gltf(
        filepath=str(BUILD),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_extras=True,
    )
    multires.levels, multires.sculpt_levels, multires.render_levels = old
    return objects


bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.preferences.filepaths.save_version = 0
RENDER_DIR.mkdir(parents=True, exist_ok=True)
BUILD.parent.mkdir(parents=True, exist_ok=True)
body = bpy.data.objects["AevryndFemaleBodyBase"]
changed_vertices, max_delta = apply_identity(body)
add_skin_detail(body)
authored, missed_roots = build_brows_and_lashes(body)

for obj in bpy.data.objects:
    if obj.name.startswith("Eye_") or obj.name.startswith("Brow_"):
        obj.hide_render = False
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
exported = export_runtime(body, authored)

camera = bpy.data.objects["Aevrynd Review Camera"]
camera.data.lens = 72
render(camera, "female-face-front", (0, -0.78, 1.555), (0, -0.005, 1.535))
render(camera, "female-face-three-quarter", (0.30, -0.68, 1.57), (0, 0, 1.535))

print(
    "AEVRYND_FACE_REPORT="
    + json.dumps(
        {
            "state": "AUTHORING",
            "identity_changed_vertices": changed_vertices,
            "identity_max_delta_m": max_delta,
            "authored_layers": [obj.name for obj in authored],
            "missed_surface_roots": missed_roots,
            "exported_objects": len(exported),
            "runtime_glb": str(BUILD),
        }
    )
)
