"""Subdivide native front-margin faces without spanning the source eye wall."""
from collections import defaultdict
from heapq import heapify, heappop, heappush
from pathlib import Path
from runpy import run_path

import bmesh
import numpy as np

ROOT=Path(__file__).resolve().parent
PREVIOUS=ROOT.parent/'r0502-lid-return'
stage=run_path(str(PREVIOUS/'author-r0502.py'))
read_json,write_json,digest,mesh_array=(stage[k] for k in ('read_json','write_json','digest','array'))
ocular=stage['probe']['probe']
body_author=stage['author']
OWNER='R503 parent eyelid polygon'
SUPPORT='R503 conforming support'


def distances(graph,seeds,limit):
    distance=dict.fromkeys(seeds,0.)
    frontier=[(0.,int(v)) for v in seeds]
    heapify(frontier)
    while frontier:
        cost,i=heappop(frontier)
        if cost!=distance[i]:
            continue
        for j,w in graph.get(i,{}).items():
            value=cost+w
            if value<min(limit,distance.get(j,np.inf)):
                distance[j]=value
                heappush(frontier,(value,j))
    return distance


def domain(body,neutral,closed,bindings):
    topo=read_json(PREVIOUS/'return-topology.json')
    walls,edge_faces=stage['chart']['chart_faces'](topo['rings'],topo['faceMaterials'])
    ring=set()
    wall=set().union(*walls)
    for eye in walls:
        kinds,_=stage['chart']['boundary'](eye,edge_faces)
        ring.update(i for e,k in kinds.items() if k=='skin' for i in e)
    vertices=topo['rings']
    wall_ids={i for fid in wall for i in vertices[str(fid)]}
    graph=defaultdict(dict)
    for row in vertices.values():
        for a,b in stage['chart']['edges'](row):
            length=max(.00009,float(np.linalg.norm(neutral[a]-neutral[b])))
            graph[a][b]=graph[b][a]=length
    front=distances(graph,ring,.0035)
    locked=(wall_ids-set(front))|set(bindings.ravel().tolist())
    # Keep the proven cheek, scalp, optical sheets and unaffected source shape.
    r499=read_json(ROOT.parent/'r0499-lid-fold/fold-probe.json')
    seeds={i for row in r499['rays']['1.0'] if row['pixel'][0] in (196,204,212,428,436,444)
           and row['pixel'][1] in (337,342,347,352) for i in row['vertices'] if i in graph}
    span=distances(graph,seeds,.0083)
    upper_band={i for i in span if .032<abs(closed[i,0])<.055 and
                -.126<closed[i,1]<-.097 and 1.456<closed[i,2]<1.478}
    active=np.array(sorted(upper_band-locked),dtype='i4')
    # Split source triangles around the front join and in the visible band.
    # No replacement face spans a vertex outside its parent triangle.
    split={}
    movable=set(active.tolist())
    for fid,row in vertices.items():
        j=int(fid)
        if len(row)!=3 or not (set(row)&upper_band):
            continue
        if j in wall and (not all(i in front for i in row) or not any(i in ring for i in row)):
            continue
        if j not in wall and not (set(row)&movable):
            continue
        if np.linalg.norm(neutral[row]-neutral[np.roll(row,1)],axis=1).max()>.0048:
            continue
        assert list(body.data.polygons[j].vertices)==row
        split[j]=row
    assert 150<len(active)<900 and len(split)>40
    strength=np.array([float(1.-span[i]/.0083) for i in active])
    strength=strength*strength*(3.-2.*strength)
    return graph,active,strength,split,wall,ring,locked


def rebuild(body,selected):
    mesh=body.data
    n=len(mesh.vertices)
    faces=[tuple(p.vertices) for p in mesh.polygons]
    starts=mesh_array(mesh.polygons,'loop_start',dtype='i4')
    saved={key.name:body_author['xyz'](key.data) for key in mesh.shape_keys.key_blocks}
    before_uv={u.name:mesh_array(u.uv,'vector',2) for u in mesh.uv_layers}
    before_norm=mesh_array(mesh.corner_normals,'vector',3) if mesh.has_custom_normals else None
    sources=np.array(list(selected.values()),dtype='i4')
    old_positions=body_author['xyz'](mesh.vertices)
    points={}
    bm=bmesh.new()
    try:
        bm.from_mesh(mesh,use_shape_key=False)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        bm.faces.index_update()
        bm.verts.index_update()
        shape_layers={k:bm.verts.layers.shape[k] for k in bm.verts.layers.shape.keys()}
        owner=bm.faces.layers.int.new(OWNER)
        support=bm.verts.layers.int.new(SUPPORT)
        original={i:bm.verts[i] for i in set(sources.ravel().tolist())}
        originals={fid:bm.faces[fid] for fid in selected}
        deform=bm.verts.layers.deform.active
        for face in bm.faces:
            face[owner]=face.index
        before_nonmanifold=sum(not e.is_manifold for e in bm.edges)
        for offset,(fid,tri) in enumerate(selected.items()):
            parent=originals[fid]
            sources0=[original[v] for v in tri]
            centre=bm.verts.new(sum((v.co for v in sources0),sources0[0].co*0)/3.)
            centre[support]=offset+1
            for layer in shape_layers.values():
                centre[layer]=sum((v[layer] for v in sources0),centre.co*0)/3.
            if deform is not None:
                weights=defaultdict(float)
                for v in sources0:
                    for index,weight in v[deform].items():
                        weights[index]+=weight/3.
                for index,weight in weights.items():
                    centre[deform][index]=weight
            for a,b in zip(sources0,sources0[1:]+sources0[:1]):
                child=bm.faces.new((a,b,centre))
                child[owner]=fid
                child.smooth=parent.smooth
                child.material_index=parent.material_index
            bm.faces.remove(parent)
            points[fid]=n+offset
        after_nonmanifold=sum(not e.is_manifold for e in bm.edges)
        assert before_nonmanifold==after_nonmanifold,(before_nonmanifold,after_nonmanifold)
        bm.to_mesh(mesh)
    finally:
        bm.free()
    mesh.update()
    assert len(mesh.vertices)==n+len(selected) and len(mesh.polygons)==len(faces)+len(selected)*2
    support_values=mesh_array(mesh.attributes[SUPPORT].data,'value',dtype='i4')
    assert np.array_equal(support_values[n:],np.arange(1,len(selected)+1))
    assert np.array_equal(body_author['xyz'](mesh.vertices)[:n],old_positions)
    for key in mesh.shape_keys.key_blocks:
        original=saved[key.name]
        extended=np.vstack([original,original[sources].mean(1)])
        assert len(key.data)==len(extended)
        key.data.foreach_set('co',extended.ravel())
        assert np.array_equal(body_author['xyz'](key.data),extended)
    parents=mesh_array(mesh.attributes[OWNER].data,'value',dtype='i4')
    ordinary=np.empty(len(mesh.loops),dtype='i4')
    triples={}
    for face,i in zip(mesh.polygons,parents):
        if int(i) not in selected:
            assert tuple(face.vertices)==faces[i]
        lookup={v:starts[i]+j for j,v in enumerate(faces[i])}
        for loop,vertex in zip(face.loop_indices,face.vertices):
            ordinary[loop]=lookup.get(vertex,-1)
            if vertex>=n:
                triples[loop]=np.array(list(lookup.values()),dtype='i4')
    keep=ordinary>=0
    for uv in mesh.uv_layers:
        before=before_uv[uv.name]
        out=np.empty((len(mesh.loops),2),dtype='f4')
        out[keep]=before[ordinary[keep]]
        for j,loops in triples.items():
            out[j]=before[loops].mean(0)
        uv.uv.foreach_set('vector',out.ravel())
        assert np.array_equal(mesh_array(uv.uv,'vector',2),out)
    if before_norm is not None:
        normals=np.zeros((len(mesh.loops),3),dtype='f4')
        normals[keep]=before_norm[ordinary[keep]]
        for j,loops in triples.items():
            avg=before_norm[loops].mean(0)
            normals[j]=avg/max(1.e-8,np.linalg.norm(avg))
        mesh.normals_split_custom_set(normals.tolist())
    mesh.update()
    return dict(baseVertices=n,addedVertices=len(selected),baseFaces=len(faces),createdFaces=len(selected)*3,
                splitParents=list(selected),verticesByFace=points,nonmanifoldEdges=after_nonmanifold,
                uvLayers=list(before_uv),newVertices=np.arange(n,len(mesh.vertices)),donors=sources,faceParents=parents)

