"""Reopen r503, verify the protected geometry, and test finite contact identities."""
from collections import Counter
from pathlib import Path
from runpy import run_path

import bpy
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
model=run_path(str(ROOT/'author-r0503.py'))
r500=model['r500']
author=model['author']
read_json,write_json,digest=(model[k] for k in ('read_json','write_json','digest'))
mesh_data,tree=(model[k] for k in ('mesh_data','tree'))
TESTS=((1.,0.),(1.,.5),(1.,.75),(1.,.82),(1.,.875),(1.,1.),(36.5,.94),(36.75,1.),
       (37.,.875),(37.,.92),(37.,.985),(37.,1.))


def open_scene(source,proof):
    p=Path(source['path'])
    assert digest(p)==source['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(p),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    skin,gaze=(bpy.data.objects[proof[name]] for name in ('body','gaze'))
    layers={role:bpy.data.objects[name] for role,name in zip(('eye','cornea','meniscus','lash'),r500['previous']['LAYERS'])}
    return scene,skin,gaze,layers


def pose_key(frame,phase):
    return f'{frame:g}:{phase:g}'


def sample_signed(coords,mask,fixture):
    measured=[]
    for i in np.flatnonzero(mask):
        p=Vector(coords[i])
        q,n,_,d=fixture.find_nearest(p)
        if d is not None:
            measured.append((float(d if (p-q).dot(n)>=0 else -d),int(i)))
    v,i=min(measured)
    return dict(metres=v,vertex=i,world=coords[i].tolist(),
        belowMinus8Micrometres=sum(a<-8e-6 for a,_ in measured),samples=len(measured))


def snapshot(skin,layers,affected,parents,source_ring):
    mesh=mesh_data(skin)
    fixtures=model['fixtures'](layers)
    raw=model['contact'](mesh,affected,fixtures)
    scoped={}
    for key,item in raw.items():
        role,a,b=key
        src_a=int(parents[a])
        if role=='skin':
            src_b=int(parents[b])
            if src_a==src_b or not source_ring[src_a].isdisjoint(source_ring[src_b]):
                continue
            address=(role,*sorted((src_a,src_b)))
        else:
            address=(role,src_a,b)
        scoped.setdefault(address,item|dict(actualFaces=[a,b]))
    ocular_hash={role:r500['array_hash'](mesh_data(layer)[0].astype('f4')) for role,layer in layers.items()}
    distances={role:sample_signed(mesh[0],affected,fixtures[role][0]) for role in ('eye','cornea')}
    return mesh,scoped,ocular_hash,distances,raw


def main():
    proof=read_json(ROOT/'construction-receipt.json')
    top=proof['topology']
    num=top['baseVertices']
    scene,skin,gaze,layers=open_scene(proof['parent'],proof)
    rings=[set(poly.vertices) for poly in skin.data.polygons]
    anchors=np.unique(model['topo']['ocular']['anchors']()['tri'])
    bank=read_json(model['topo']['PREVIOUS']/'return-topology.json')
    parents=np.arange(len(rings))
    donors=np.array([list(skin.data.polygons[i].vertices) for i in top['splitParents']])
    active=np.zeros(num,dtype=bool)
    active[proof['movableSourceVertices']]=True
    original_region=active.copy()
    original_region[donors]=True
    preserved_faces=[fid for fid in proof['posteriorReturnFaces'] if not any(active[v] for v in bank['rings'][str(fid)])]
    preserved_vertices=np.unique([v for fid in preserved_faces for v in bank['rings'][str(fid)]])
    assert len(preserved_faces)>300
    old_keys={key.name:r500['array_hash'](author['xyz'](key.data)) for key in skin.data.shape_keys.key_blocks}
    baseline={}
    for frame,phase in TESTS:
        r500['activate'](scene,gaze,'separated',phase,frame)
        baseline[pose_key(frame,phase)]=snapshot(skin,layers,original_region,parents,rings)
    scene,skin,gaze,layers=open_scene(proof['source'],proof)
    assert int(gaze[proof['layoutProperty']])==2 and float(gaze[proof['blinkProperty']])==0.
    keys=skin.data.shape_keys.key_blocks
    for name,hash_ in old_keys.items():
        assert r500['array_hash'](author['xyz'](keys[name].data)[:num])==hash_,name
    for label,values in proof['variants'].items():
        for spec in values:
            assert r500['array_hash'](author['xyz'](keys[spec['key']].data))==spec['coordinateHash']
    assert tuple(u.name for u in skin.data.uv_layers)==tuple(top['uvLayers'])
    hair=bpy.data.objects[proof['hair']['object']]
    assert r500['array_hash'](author['prior']['positions'](hair))==proof['hair']['positionHash']
    parents=model['topo']['mesh_array'](skin.data.attributes[proof['faceOwner']].data,'value',dtype='i4')
    affected=np.r_[original_region,np.ones(top['addedVertices'],dtype=bool)]
    outcome={}
    deviations={}
    for frame,phase in TESTS:
        pose=pose_key(frame,phase)
        ref,base_contacts,base_layers,_,_=baseline[pose]
        outcome[pose]={}
        control=None
        for mode in model['MODES']:
            model['activate'](scene,gaze,mode,phase,frame)
            mesh,pairs,ocular_hash,signed,raw=snapshot(skin,layers,affected,parents,rings)
            v,f,p=mesh
            assert ocular_hash==base_layers
            assert np.array_equal(v[anchors],ref[0][anchors])
            assert np.array_equal(v[preserved_vertices],ref[0][preserved_vertices])
            assert np.array_equal(v[:num][~active],ref[0][~active])
            if mode=='control':
                assert np.array_equal(v[:num],ref[0])
                control=raw
                gap=np.linalg.norm(v[num:]-v[donors].mean(1),axis=1)
                i=int(gap.argmax())
                deviations[pose]=dict(metres=float(gap[i]),vertex=num+i,sourceFace=top['splitParents'][i])
                assert np.isfinite(gap).all()
            base={kind:count for kind,count in Counter(key[0] for key in base_contacts).items()}
            current={kind:count for kind,count in Counter(key[0] for key in pairs).items()}
            outcome[pose][mode]=dict(baseline=base,current=current,
                newAgainstR500=[dict(pair=k,**pairs[k]) for k in sorted(pairs.keys()-base_contacts.keys())],
                newRawAgainstSplitControl=[dict(pair=k,**raw[k]) for k in sorted(raw.keys()-control.keys())],
                signedSamples=signed,skinHash=r500['array_hash'](v.astype('f4')),
                externalChangeMaxMetres=float(np.linalg.norm(v[:num]-ref[0],axis=1).max()))
        print('R503_REOPEN',pose,{m:(len(row['newAgainstR500']),len(row['newRawAgainstSplitControl']))
              for m,row in outcome[pose].items()},flush=True)
    operation={}
    for mode in ('control','fair','rest','control','rest'):
        model['activate'](scene,gaze,mode,1.,37.)
        h=r500['array_hash'](mesh_data(skin)[0].astype('f4'))
        assert outcome['37:1'][mode]['skinHash']==h
        operation[mode]=h
    assert len(set(operation.values()))==3
    assert all(d.is_valid for d in skin.data.shape_keys.animation_data.drivers if 'R503' in d.data_path)
    model['activate'](scene,gaze,'rest',0.,1.)
    assert digest(Path(proof['source']['path']))==proof['source']['sha256']
    meshes=[obj for obj in scene.objects if obj.type=='MESH']
    for obj in meshes:
        obj.data.calc_loop_triangles()
    stats=dict(vertices=sum(len(obj.data.vertices) for obj in meshes),
        triangles=sum(len(obj.data.loop_triangles) for obj in meshes),
        bones=sum(len(obj.data.bones) for obj in scene.objects if obj.type=='ARMATURE'),
        morphs=sum(len(obj.data.shape_keys.key_blocks)-1 for obj in meshes if obj.data.shape_keys),
        materials=len(bpy.data.materials),images=len(bpy.data.images),
        strands=len(hair.data.curves),hairPoints=len(hair.data.points))
    write_json(ROOT/'reopen-contact.json',dict(source=proof['source'],parent=proof['parent'],poses=outcome,
        splitControlInterpolationMetres=deviations,protectedReturnFaces=len(preserved_faces),
        protectedReturnVertices=len(preserved_vertices),preservedLashAnchors=len(anchors),
        originalKeyHashesVerified=len(old_keys),operation=operation,stats=stats,
        scope=('Held evaluated native frames. Triangle overlap comparison at original polygon ownership for r500, and '
               'actual new polygon identities versus the split control. Adjacent pairs sharing a source vertex are excluded '
               'from original-identity comparison. Signed values are sampled points only. No swept certification.')))


if __name__=='__main__':
    main()

