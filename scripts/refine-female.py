"""以 Blender 背景模式重建女人偶；保留原始資產與全部臉部塑形。"""
import bpy
import collections
import json
import math
import random
import subprocess
import os
import shutil
import runpy
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(ROOT / 'public/assets/character-third-pants.glb'), merge_vertices=True)
body = bpy.data.objects['Body']
rig = body.modifiers[0].object

def subdivide_with_shapes(obj):
    """以相同拓樸分別求值所有塑形，避免匯出時遺失滑桿與蒙皮。"""
    arm = obj.modifiers.get('Armature')
    if arm: arm.show_viewport = False
    keys = obj.data.shape_keys
    names = [k.name for k in keys.key_blocks] if keys else []
    if keys:
        for k in keys.key_blocks: k.value = 0
    sub = obj.modifiers.new('Surface refinement', 'SUBSURF')
    sub.levels = sub.render_levels = 1
    deps = bpy.context.evaluated_depsgraph_get()
    bpy.context.view_layer.update()
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(deps), preserve_all_data_layers=True, depsgraph=deps)
    coords = []
    for name in names[1:]:
        keys.key_blocks[name].value = 1
        bpy.context.view_layer.update()
        evaluated = obj.evaluated_get(deps).to_mesh()
        data = np.empty(len(evaluated.vertices) * 3, dtype=np.float32)
        evaluated.vertices.foreach_get('co', data)
        coords.append(data)
        obj.evaluated_get(deps).to_mesh_clear()
        keys.key_blocks[name].value = 0
    obj.modifiers.remove(sub)
    obj.data = mesh
    if names:
        obj.shape_key_add(name=names[0], from_mix=False)
        for name, data in zip(names[1:], coords):
            key = obj.shape_key_add(name=name, from_mix=False)
            key.data.foreach_set('co', data)
            key.value = 0
    if arm: arm.show_viewport = True
    for p in mesh.polygons: p.use_smooth = True

subdivide_with_shapes(body)
pants = bpy.data.objects['Pants']
edges = collections.Counter(tuple(sorted(e)) for p in pants.data.polygons for e in p.edge_keys)
boundary = {i for e, count in edges.items() if count == 1 for i in e}
for i in boundary:
    v = pants.data.vertices[i]
    if v.co.z > 1: v.co.z = 1.055
subdivide_with_shapes(pants)
for v in pants.data.vertices:
    x, y, z = v.co
    envelope = math.exp(-((z - .50) / .11) ** 2) + .65 * math.exp(-((z - .18) / .06) ** 2)
    fold = .0018 * envelope * math.sin(z * 175 + x * 20 + y * 13)
    v.co += v.normal * (fold + .0015)

def texture(name, rgb):
    h, w = rgb.shape[:2]
    im = bpy.data.images.new(name, width=w, height=h, alpha=True)
    im.colorspace_settings.name = 'Non-Color'
    rgba = np.ones((h, w, 4), dtype=np.float32)
    rgba[:, :, :3] = rgb
    im.pixels.foreach_set(rgba.ravel())
    im.pack()
    return im

size = 512
y, x = np.mgrid[0:size, 0:size] / size
weave = .45 * np.sin(2 * np.pi * x * 64) + .45 * np.sin(2 * np.pi * y * 64)
leather = np.zeros_like(x)
for f, strength in [(32, .7), (67, .25), (127, .08)]:
    leather += strength * np.sin(2 * np.pi * (x * f + .12 * np.sin(2 * np.pi * y * 8))) * np.cos(2 * np.pi * y * f)

def normal_texture(name, height, strength):
    dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * strength
    dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * strength
    normal = np.stack((-dx, -dy, np.ones_like(dx)), axis=-1)
    normal /= np.linalg.norm(normal, axis=-1, keepdims=True)
    return texture(name, normal * .5 + .5)

cloth_normal = normal_texture('WovenClothNormal', weave, .22)
leather_normal = normal_texture('LeatherGrainNormal', leather, .23)
cloth_rough = texture('WovenClothRoughness', np.repeat((.78 + .035 * weave)[:, :, None], 3, axis=2))

def image_input(mat, socket, im, scale=1):
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    node = nodes.new('ShaderNodeTexImage'); node.image = im
    uv = nodes.new('ShaderNodeTexCoord')
    mapping = nodes.new('ShaderNodeMapping'); mapping.inputs['Scale'].default_value = (scale, scale, 1)
    links.new(uv.outputs['UV'], mapping.inputs['Vector']); links.new(mapping.outputs['Vector'], node.inputs['Vector'])
    if socket == 'Normal':
        normal = nodes.new('ShaderNodeNormalMap'); normal.inputs['Strength'].default_value = .55
        links.new(node.outputs['Color'], normal.inputs['Color']); links.new(normal.outputs['Normal'], bsdf.inputs['Normal'])
    else: links.new(node.outputs['Color'], bsdf.inputs[socket])

for mat in bpy.data.materials:
    if not mat.use_nodes: continue
    bsdf = next((n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not bsdf: continue
    name = mat.name.lower()
    if name.startswith('body_'):
        bsdf.inputs['IOR'].default_value = 1.4
        bsdf.inputs['Subsurface Weight'].default_value = .07
        bsdf.inputs['Subsurface Radius'].default_value = (1, .42, .22)
        bsdf.inputs['Subsurface Scale'].default_value = .0015
        for n in mat.node_tree.nodes:
            if n.type == 'NORMAL_MAP': n.inputs['Strength'].default_value = .12
        if 'lips' in name or 'nails' in name:
            bsdf.inputs['Coat Weight'].default_value = .22 if 'lips' in name else .36
            bsdf.inputs['Coat Roughness'].default_value = .3
    elif 'hair_' in name:
        for link in list(bsdf.inputs['Roughness'].links): mat.node_tree.links.remove(link)
        bsdf.inputs['Roughness'].default_value = .62
        bsdf.inputs['IOR'].default_value = 1.46
    elif 'cloth' in name:
        bsdf.inputs['Base Color'].default_value = (.023, .029, .039, 1)
        bsdf.inputs['Metallic'].default_value = 0
        bsdf.inputs['Sheen Weight'].default_value = .22
        bsdf.inputs['Sheen Tint'].default_value = (.2, .23, .28, 1)
        bsdf.inputs['Sheen Roughness'].default_value = .65
        image_input(mat, 'Normal', cloth_normal, 25)
        image_input(mat, 'Roughness', cloth_rough, 25)
    elif 'leather' in name:
        bsdf.inputs['Base Color'].default_value = (.022, .015, .012, 1)
        for link in list(bsdf.inputs['Roughness'].links): mat.node_tree.links.remove(link)
        bsdf.inputs['Roughness'].default_value = .49
        image_input(mat, 'Normal', leather_normal, 7)
    elif 'sclera' in name or 'iris' in name or 'pupil' in name:
        bsdf.inputs['Coat Weight'].default_value = 1
        bsdf.inputs['Coat Roughness'].default_value = .08
        bsdf.inputs['IOR'].default_value = 1.376

# 虹膜加入放射纖維與外圈，保留原始虹膜及瞳孔幾何。
eyes = bpy.data.objects['Eyes']
colors = eyes.data.color_attributes.new(name='IrisFibers', type='FLOAT_COLOR', domain='CORNER')
for poly in eyes.data.polygons:
    mat = eyes.data.materials[poly.material_index]
    iris = 'Iris' in mat.name
    for li in poly.loop_indices:
        v = eyes.data.vertices[eyes.data.loops[li].vertex_index].co
        if iris:
            cx = -.0343 if v.x < 0 else .0343
            dx, dz = (v.x - cx) / .0065, (v.z - 1.6017) / .0056
            r, a = math.hypot(dx, dz), math.atan2(dz, dx)
            fiber = .75 + .16 * math.sin(a * 83 + r * 9) + .09 * math.sin(a * 139 - r * 14)
            ring = 1 - .70 * max(0, min(1, (r - .78) / .18))
            colors.data[li].color = (.17 * fiber * ring, .074 * fiber * ring, .026 * fiber * ring, 1)
        else: colors.data[li].color = (1, 1, 1, 1)
for mat in eyes.data.materials:
    if 'Iris' not in mat.name: continue
    bsdf = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    node = mat.node_tree.nodes.new('ShaderNodeVertexColor'); node.layer_name = 'IrisFibers'
    mat.node_tree.links.new(node.outputs['Color'], bsdf.inputs['Base Color'])

# 眉毛依身體表面投射，使用真正細絲網格，並繫結頭部骨骼。
tree = BVHTree.FromPolygons([v.co for v in body.data.vertices], [p.vertices[:] for p in body.data.polygons])
hair_mat = bpy.data.materials.new('BrowHair'); hair_mat.use_nodes = True
b = hair_mat.node_tree.nodes.get('Principled BSDF'); b.inputs['Base Color'].default_value = (.033, .017, .009, 1); b.inputs['Roughness'].default_value = .72
verts, faces = [], []
rng = random.Random(915)
for side in (-1, 1):
    for i in range(95):
        t = i / 94
        bx = side * (.015 + .041 * t)
        bz = 1.613 + .0055 * math.sin(t * math.pi) - .004 * t + rng.uniform(-.0013, .0013)
        strand = []
        for step in range(4):
            u = step / 3; px = bx + side * .0021 * u; pz = bz + .0028 * math.sin(u * 1.4)
            hit, normal, _, _ = tree.ray_cast(Vector((px, -.4, pz)), Vector((0, 1, 0)))
            if hit is None: break
            center = hit + normal * .00022
            width = .00013 * (1 - .8 * u)
            strand.append(len(verts)); verts.extend([center + Vector((width, 0, 0)), center - Vector((width, 0, 0))])
        for a, c in zip(strand, strand[1:]): faces.append((a, a + 1, c + 1, c))
mesh = bpy.data.meshes.new('EyebrowStrands'); mesh.from_pydata(verts, [], faces); mesh.materials.append(hair_mat)
brows = bpy.data.objects.new('Brows', mesh); bpy.context.collection.objects.link(brows)
brows.parent = rig
brows.vertex_groups.new(name='head').add(list(range(len(verts))), 1, 'REPLACE')
mod = brows.modifiers.new('Armature', 'ARMATURE'); mod.object = rig

# 沿實際上眼瞼尋找前表面，避免把睫毛放進眼球或貼在眼白上。
verts, faces = [], []
for side in (-1, 1):
    for i in range(34):
        t = i / 33
        px = side * (.022 + .026 * t)
        root = None
        for j in range(55):
            z = 1.602 + .00025 * j
            hit, normal, _, _ = tree.ray_cast(Vector((px, -.4, z)), Vector((0, 1, 0)))
            if hit is not None and hit.y < -.106:
                root = hit + normal * .0002
                break
        if root is None: continue
        base = len(verts)
        length = .0024 + .002 * math.sin(t * math.pi)
        for j in range(4):
            u = j / 3
            center = root + Vector((side * .0008 * u, -length * u, .0015 * u * u))
            width = .00012 * (1 - .9 * u)
            verts.extend([center + Vector((width, 0, 0)), center - Vector((width, 0, 0))])
        for j in range(3):
            a = base + j * 2; faces.append((a, a + 1, a + 3, a + 2))
mesh = bpy.data.meshes.new('LashStrands'); mesh.from_pydata(verts, [], faces); mesh.materials.append(hair_mat.copy()); mesh.materials[0].name = 'LashHair'
lashes = bpy.data.objects.new('Lashes', mesh); bpy.context.collection.objects.link(lashes); lashes.parent = rig
lashes.vertex_groups.new(name='head').add(list(range(len(verts))), 1, 'REPLACE')
mod = lashes.modifiers.new('Armature', 'ARMATURE'); mod.object = rig

# 以既有髮型表面作導引增加細髮，維持原本髮型與輪廓。
guide = bpy.data.objects['Hair']
hair_tree = BVHTree.FromPolygons([v.co for v in guide.data.vertices], [p.vertices[:] for p in guide.data.polygons])
verts, faces = [], []
for i in range(620):
    theta = rng.uniform(.55, math.pi) * (-1 if i % 2 else 1)
    ztop = rng.uniform(1.69, 1.718)
    zend = rng.uniform(1.21, 1.38)
    strand = []
    for j in range(30):
        t = j / 29; z = ztop * (1 - t) + zend * t
        a = theta + .035 * math.sin(t * 7 + i * .3)
        direction = Vector((math.sin(a), -math.cos(a), 0))
        hit, normal, _, _ = hair_tree.ray_cast(direction * .4 + Vector((0, 0, z)), -direction)
        if hit is None:
            if strand: break
            continue
        center = hit + normal * (.00035 + .00018 * math.sin(i))
        width = .00013 * (1 - .82 * t)
        cross = Vector((math.cos(a), math.sin(a), 0)) * width
        strand.append(len(verts)); verts.extend([center + cross, center - cross])
    for a, c in zip(strand, strand[1:]): faces.append((a, a + 1, c + 1, c))
mesh = bpy.data.meshes.new('GroomFibers'); mesh.from_pydata(verts, [], faces)
uv = mesh.uv_layers.new(name='UVMap')
for loop in mesh.loops:
    vertex = mesh.vertices[loop.vertex_index]
    uv.data[loop.index].uv = (loop.vertex_index % 2, (1.72 - vertex.co.z) / .5)
for shade in range(4):
    mat = bpy.data.materials.new('hair_GroomFibers_' + str(shade)); mat.use_nodes = True
    b = mat.node_tree.nodes.get('Principled BSDF'); value = .013 + .006 * shade
    b.inputs['Base Color'].default_value = (value, value * .58, value * .32, 1); b.inputs['Roughness'].default_value = .63
    mesh.materials.append(mat)
for p in mesh.polygons: p.material_index = p.index % 4
fibers = bpy.data.objects.new('HairFibers', mesh); bpy.context.collection.objects.link(fibers); fibers.parent = rig
fibers.vertex_groups.new(name='head').add(list(range(len(verts))), 1, 'REPLACE')
mod = fibers.modifiers.new('Armature', 'ARMATURE'); mod.object = rig

# 依材質拆開服裝與頭髮；原有蒙皮權重仍由各子網格保留。
for name, labels in [('Upper', ['InnerTop', 'Jacket']), ('Hair', ['Scalp', 'HairStrands', 'Flyaways'])]:
    obj = bpy.data.objects[name]
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.separate(type='MATERIAL'); bpy.ops.object.mode_set(mode='OBJECT')
    for piece in list(bpy.context.selected_objects):
        matname = piece.data.materials[0].name
        if name == 'Upper':
            piece.name = 'Jacket' if 'Leather' in matname else 'InnerTop'
            if piece.name == 'Jacket':
                # 原資產背面的內搭與外套相距不足 0.03mm，建立 3mm 的實際分層。
                for v in piece.data.vertices:
                    blend = max(0, min(1, (v.co.y + .025) / .05))
                    v.co.y += .003 * blend * blend * (3 - 2 * blend)
        else: piece.name = 'Flyaways' if 'Flyaway' in matname else 'HairStrands' if 'Layered' in matname else 'Scalp'

for o in bpy.data.objects:
    if o.type == 'MESH' and o.name != 'Icosphere':
        o['characterLayer'] = o.name
        for p in o.data.polygons: p.use_smooth = True

build_dir = ROOT / '.character-build'
build_dir.mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(build_dir / 'pre-contact.blend'))
contact_reports = runpy.run_path(str(ROOT / 'scripts/character-contact.py'))['fit_character']()

build_dir = ROOT / '.character-build'
build_dir.mkdir(exist_ok=True)
out = build_dir / 'authoring.glb'
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.context.scene.objects:
    if o.type in {'MESH', 'ARMATURE'} and o.name != 'Icosphere': o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(out), export_format='GLB', use_selection=True, export_animations=False, export_morph=True, export_skins=True, export_extras=True, export_yup=True)
packer = ROOT.parent / 'ToolCache/meshoptimizer-1.2-build/Release/gltfpack.exe'
if os.environ.get('AEVRYND_CHARACTER_UNPACKED'):
    shutil.copyfile(out, os.environ['AEVRYND_CHARACTER_UNPACKED'])
packed = Path(os.environ.get('AEVRYND_CHARACTER_STAGE', str(ROOT / 'public/assets/character-female-refined.glb')))
subprocess.run([str(packer), '-i', str(out), '-o', str(packed), '-cc', '-kn', '-km', '-ke', '-kv', '-vp', '16', '-vt', '16', '-vn', '12'], check=True)
report = {'source': 'character-third-pants.glb', 'output': out.name, 'layers': [{'name': o.name, 'vertices': len(o.data.vertices), 'faces': len(o.data.polygons)} for o in bpy.context.selected_objects if o.type == 'MESH'], 'morphs': [k.name for k in body.data.shape_keys.key_blocks][1:], 'notes': ['Cloth normals and roughness are procedural, not scanned.', 'Original body albedo preserved.', 'Skin subsurface requires viewer shading; standard glTF does not encode it.']}
report['output'] = packed.name
report['downloadBytes'] = packed.stat().st_size
report['contactChecks'] = contact_reports
report['notes'].append('Counts describe authoring geometry; 16-bit positions/UVs, 12-bit normals; original texture bytes retained.')
packed.with_suffix('.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('REFINEMENT', json.dumps(report))
