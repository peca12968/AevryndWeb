"""女人偶目前姿勢的接觸修整與表面取樣驗證。"""
import bpy
import bmesh
from collections import Counter
from mathutils import Vector
from mathutils.bvhtree import BVHTree

class ContactSurface:
    def __init__(self, vertices, polygons, open_surface=False):
        self.vertices = vertices
        self.polygons = [(face[0], face[i], face[i + 1]) for face in polygons for i in range(1, len(face) - 1)]
        self.tree = BVHTree.FromPolygons(vertices, self.polygons, all_triangles=True)
        self.boundary = set()
        self.reference = None
        if open_surface:
            edges = Counter(tuple(sorted((face[i], face[(i + 1) % 3]))) for face in self.polygons for i in range(3))
            self.boundary = {edge for edge, count in edges.items() if count == 1}
    def find_nearest(self, point): return self.tree.find_nearest(point)
    def is_boundary_contact(self, point, face_index):
        if not self.boundary: return False
        ids = self.polygons[face_index]
        a, b, c = (self.vertices[i] for i in ids)
        u, v, p = b - a, c - a, point - a
        uu, uv, vv = u.dot(u), u.dot(v), v.dot(v)
        denominator = uu * vv - uv * uv
        if abs(denominator) < 1e-20: return True
        wb = (vv * p.dot(u) - uv * p.dot(v)) / denominator
        wc = (uu * p.dot(v) - uv * p.dot(u)) / denominator
        bary = (1 - wb - wc, wb, wc)
        return any(bary[i] < 1e-5 and tuple(sorted((ids[(i + 1) % 3], ids[(i + 2) % 3]))) in self.boundary for i in range(3))

def surface(obj, outward_against=None):
    vertices = [obj.matrix_world @ v.co for v in obj.data.vertices]
    polygons = []
    for face in obj.data.polygons:
        if outward_against is not None:
            center = sum((vertices[i] for i in face.vertices), Vector()) / len(face.vertices)
            hit, normal, _, _ = outward_against.find_nearest(center)
            if normal.dot(obj.matrix_world.to_3x3() @ face.normal) < 0:
                polygons.append(tuple(reversed(face.vertices[:])))
                continue
        polygons.append(face.vertices[:])
    result = ContactSurface(vertices, polygons, outward_against is not None)
    result.reference = outward_against
    return result

def correction(point, colliders, margin):
    worst = 0
    push = Vector()
    for tree, reach in colliders:
        hit, normal, face_index, distance = tree.find_nearest(point)
        if hit is None or distance > reach: continue
        if tree.is_boundary_contact(hit, face_index): continue
        if tree.reference is not None:
            _, normal, _, _ = tree.reference.find_nearest(point)
        signed = (point - hit).dot(normal)
        depth = margin - signed
        if depth > worst:
            worst = depth
            push = normal * depth
    return push, worst

def fit(obj, colliders, margin, iterations=60):
    positions = [obj.matrix_world @ v.co for v in obj.data.vertices]
    original = [p.copy() for p in positions]
    corrected = set()
    for iteration in range(iterations):
        maximum = 0
        for i, point in enumerate(positions):
            push, depth = correction(point, colliders, margin + .0003)
            if depth > .000015:
                point += push
                corrected.add(i)
                maximum = max(maximum, depth)
        # 邊中點及三角形內部也取樣，避免只有頂點通過但三角面切進身體。
        accumulated = [Vector() for _ in positions]
        weights = [0] * len(positions)
        for face in obj.data.polygons:
            ids = face.vertices[:]
            samples = [(sum((positions[i] for i in ids), Vector()) / len(ids), ids)]
            for a, b in zip(ids, ids[1:] + ids[:1]): samples.append(((positions[a] + positions[b]) * .5, (a, b)))
            for point, affected in samples:
                push, depth = correction(point, colliders, margin)
                if depth > .000015:
                    maximum = max(maximum, depth)
                    for i in affected:
                        accumulated[i] += push
                        weights[i] += 1
                        corrected.add(i)
        for i, weight in enumerate(weights):
            if weight: positions[i] += accumulated[i] / weight * 1.1
        # BVH 實際交線檢查補足離散取樣：細髮片可能跨過整個耳廓。
        current = ContactSurface(positions, [p.vertices[:] for p in obj.data.polygons])
        intersection_pushes = {}
        for collider, _ in colliders:
            for own_face, other_face in current.tree.overlap(collider.tree):
                ids = current.polygons[own_face]
                a, b, c = (collider.vertices[i] for i in collider.polygons[other_face])
                normal = (b - a).cross(c - a).normalized()
                center = sum((positions[i] for i in ids), Vector()) / 3
                if collider.reference is not None:
                    _, normal, _, _ = collider.reference.find_nearest(center)
                if obj.name in ['Scalp', 'HairStrands', 'Flyaways', 'HairFibers'] and abs(center.x) > .072 and 1.55 < center.z < 1.65:
                    normal = Vector((1 if center.x > 0 else -1, 0, 0))
                for i in ids:
                    intersection_pushes.setdefault(i, []).append(normal * .0006)
        for i, pushes in intersection_pushes.items():
            positions[i] += sum(pushes, Vector()) / len(pushes)
            corrected.add(i)
        if intersection_pushes: maximum = max(maximum, .0006)
        if maximum < .00003: break
        if iteration % 10 == 0: print('CONTACT_PROGRESS', obj.name, iteration + 1, 'crossing vertices', len(intersection_pushes), flush=True)
    inverse = obj.matrix_world.inverted()
    for vertex, position in zip(obj.data.vertices, positions): vertex.co = inverse @ position
    obj.data.update()
    max_movement = max((a - b).length for a, b in zip(positions, original))
    minimum = float('inf')
    penetrations = 0
    samples = len(positions)
    for point in positions:
        _, depth = correction(point, colliders, 0)
        if depth > .00004: penetrations += 1
        minimum = min(minimum, -depth)
    for face in obj.data.polygons:
        point = sum((positions[i] for i in face.vertices), Vector()) / len(face.vertices)
        _, depth = correction(point, colliders, 0)
        samples += 1
        if depth > .00004: penetrations += 1
    return {'object': obj.name, 'correctedVertices': len(corrected), 'maxMovementMeters': max_movement, 'sampleCount': samples, 'penetratingSamples': penetrations, 'iterations': iteration + 1}

def fit_character():
    body = surface(bpy.data.objects['Body'])
    reports = []
    # 移除原衣物深入身體的封口與內部面；不以隱藏身體來掩飾接觸。
    for name in ['InnerTop', 'Jacket', 'HairStrands', 'Flyaways', 'HairFibers']:
        obj = bpy.data.objects[name]
        bm = bmesh.new(); bm.from_mesh(obj.data)
        remove = []
        for face in bm.faces:
            samples = [obj.matrix_world @ face.calc_center_median()]
            samples.extend(obj.matrix_world @ v.co for v in face.verts)
            depths = []
            for point in samples:
                hit, normal, _, _ = body.find_nearest(point)
                depths.append(-(point - hit).dot(normal))
            is_hair = name in ['HairStrands', 'Flyaways', 'HairFibers']
            if depths[0] > (.003 if is_hair else .012) or min(depths[1:]) > (.002 if is_hair else .008):
                remove.append(face)
        bmesh.ops.delete(bm, geom=remove, context='FACES')
        loose = [v for v in bm.verts if not v.link_faces]
        if loose: bmesh.ops.delete(bm, geom=loose, context='VERTS')
        bm.to_mesh(obj.data); bm.free(); obj.data.update()
        print('CONTACT_TOPOLOGY', name, 'interior faces removed', len(remove), flush=True)
    def fit_cloth(name, colliders, margin):
        obj = bpy.data.objects[name]
        before = [v.co.copy() for v in obj.data.vertices]
        report = fit(obj, colliders, margin)
        bm = bmesh.new(); bm.from_mesh(obj.data)
        bm.verts.ensure_lookup_table()
        affected = {v for v in bm.verts if (v.co - before[v.index]).length > .002}
        for _ in range(2): affected |= {edge.other_vert(v) for v in list(affected) for edge in v.link_edges}
        movable = [v for v in affected if not v.is_boundary]
        for _ in range(12): bmesh.ops.smooth_vert(bm, verts=movable, factor=.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
        bm.to_mesh(obj.data); bm.free(); obj.data.update()
        final = fit(obj, colliders, margin)
        report['relaxedVertices'] = len(movable)
        report['finalContact'] = final
        return report
    reports.append(fit_cloth('InnerTop', [(body, 1)], .0018))
    reports.append(fit(bpy.data.objects['Pants'], [(body, 1)], .0025))
    inner = surface(bpy.data.objects['InnerTop'], body)
    reports.append(fit_cloth('Jacket', [(body, 1), (inner, .025)], .003))
    jacket = surface(bpy.data.objects['Jacket'], body)
    clothes = [(body, 1), (inner, .035), (jacket, .035)]
    for name in ['Scalp', 'HairStrands', 'Flyaways', 'HairFibers']:
        obj = bpy.data.objects[name]
        before = [v.co.copy() for v in obj.data.vertices]
        report = fit(obj, clothes, .001, iterations=40)
        # 少數原髮片橫跨耳廓／領口，投影無法保持合理形狀，修剪交界片段。
        bm = bmesh.new(); bm.from_mesh(obj.data)
        bmesh.ops.triangulate(bm, faces=list(bm.faces))
        bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
        vertices = [obj.matrix_world @ vertex.co for vertex in bm.verts]
        tree = BVHTree.FromPolygons(vertices, [[v.index for v in face.verts] for face in bm.faces], all_triangles=True)
        remove = set()
        for collider, _ in clothes:
            remove.update(own for own, other in tree.overlap(collider.tree))
        if name == 'HairFibers':
            # 細髮若被接觸投影拉成寬片，修短該段，維持真正的細絲輪廓。
            for face_index, face in enumerate(bm.faces):
                if max((v.co - before[v.index]).length for v in face.verts) > .004 and face.calc_center_median().z > 1.5:
                    remove.add(face_index)
        bmesh.ops.delete(bm, geom=[bm.faces[index] for index in remove], context='FACES')
        loose = [vertex for vertex in bm.verts if not vertex.link_faces]
        if loose: bmesh.ops.delete(bm, geom=loose, context='VERTS')
        bm.to_mesh(obj.data); bm.free(); obj.data.update()
        report['trimmedHairTriangles'] = len(remove)
        reports.append(report)
    for report in reports: print('CONTACT_FIT', report, flush=True)
    return reports
