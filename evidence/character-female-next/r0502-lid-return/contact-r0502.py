"""Check the rebuilt inner wall and both independent lid motions in Blender."""
from collections import Counter
from pathlib import Path
from runpy import run_path

import bpy
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
model=run_path(str(ROOT/'author-r0502.py'))
probe,stage=(model[k] for k in ('probe','stage'))
read_json,write_json,digest=(model[k] for k in ('read_json','write_json','digest'))
mesh_data,tree=(probe[k] for k in ('mesh_data','tree'))
from time import perf_counter

TESTS=((1.,0.),(1.,.5),(1.,.75),(1.,.875),(1.,1.),(36.75,1.),(37.,.875),(37.,1.))


def open_model(source,proof):
    path=Path(source['path'])
    assert digest(path)==source['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
    skin,gaze=(bpy.data.objects[proof[name]] for name in ('body','gaze'))
    labels=('eye','cornea','meniscus','lashes')
    layers={role:bpy.data.objects[name] for role,name in zip(labels,stage['previous']['LAYERS'])}
    return bpy.context.scene,skin,gaze,layers


def lowest(vertices,indices,bvh):
    observations=[]
    for i in indices:
        p=Vector(vertices[i])
        q,n,_,d=bvh.find_nearest(p)
        if d is not None:
            observations.append((float(d if (p-q).dot(n)>=0 else -d),int(i)))
    if not observations:
        return None
    gap,i=min(observations)
    return dict(signedMetres=gap,vertex=i,positionMetres=vertices[i].tolist(),
        negativeBeyond8Microns=sum(g<-8e-6 for g,_ in observations),sampleCount=len(observations))


def collect(skin,layers,binding,ids,parents,return_triangles):
    vertices,tri,poly=mesh_data(skin)
    subset=np.flatnonzero(np.isin(tri,ids).any(1)|return_triangles[poly])
    own=parents[poly]
    wall=return_triangles[poly]
    patch=tree(vertices,tri[subset])
    whole=tree(vertices,tri)
    contacts={}
    for i,b in patch.overlap(whole):
        a=subset[i]
        if poly[a]==poly[b] or (tri[a,:,None]==tri[b,None,:]).any():
            continue
        first,second=sorted((a,b))
        key=tuple(sorted((int(poly[first]),int(poly[second]))))
        kind='return-return' if wall[a] and wall[b] else 'return-exterior' if wall[a] or wall[b] else 'exterior-exterior'
        old=tuple(sorted((int(own[a]),int(own[b]))))
        if key not in contacts:
            contacts[key]=dict(kind=kind, source=old, actual=key,
                locationMetres=((vertices[tri[a]].mean(0)+vertices[tri[b]].mean(0))/2).tolist())
    layer_results={}
    selected=np.unique(tri[wall])
    roots=probe['probe']['rim_sites'](vertices,binding)
    layer_hash={}
    for role,obj in layers.items():
        v,f,p=mesh_data(obj)
        fixtures=tree(v,f)
        overlaps=patch.overlap(fixtures)
        layer_hash[role]=stage['array_hash'](v.astype('f4'))
        unique={}
        for i,j in overlaps:
            a=subset[i]
            k=int(poly[a]),int(p[j])
            tag='return' if wall[a] else 'exterior'
            if role=='lashes':
                assert np.array_equal(f,binding['faces'])
                tag='root' if binding['segment'][j]==0 else 'shaft'
            if k not in unique:
                unique[k]=dict(kind=tag,actual=k,
                    locationMetres=((vertices[tri[a]].mean(0)+v[f[j]].mean(0))/2).tolist(),
                    sourceFace=int(own[a]))
        layer_results[role]=dict(counts=dict(Counter(row['kind'] for row in unique.values())),
            witnesses=list(unique.values()) if role!='lashes' else [row for row in unique.values() if row['kind']=='shaft'],
            returnSignedSamples=lowest(vertices,selected,fixtures) if role in ('eye','cornea') else None)
        if role=='lashes':
            layer_results[role]['lashRootErrorMetres']=float(np.linalg.norm(v.reshape(-1,68,3)[:,66]-roots,axis=1).max())
    area=np.linalg.norm(np.cross(vertices[tri[wall,1]]-vertices[tri[wall,0]],
                                 vertices[tri[wall,2]]-vertices[tri[wall,0]]),axis=1)*.5
    if not np.isfinite(vertices).all():
        raise AssertionError('Nonfinite skin point')
    return dict(selfCounts=dict(Counter(row['kind'] for row in contacts.values())),
        selfWitnesses=list(contacts.values()),layer=layer_results,layerHashes=layer_hash,
        rootHash=stage['array_hash'](roots.astype('f4')),
        wallTriangleCount=int(wall.sum()),wallTrianglesBelow1e12=int(np.count_nonzero(area<1e-12)),
        minimumWallTriangleAreaM2=float(area.min()),
        skinHash=stage['array_hash'](vertices.astype('f4')))


def main():
    proof=read_json(ROOT/'construction-receipt.json')
    topology=read_json(ROOT/'return-topology.json')
    source_faces=np.array([int(i) for i,mat in topology['faceMaterials'].items() if mat==0])
    binding=probe['probe']['anchors']()
    with np.load(ROOT/'return-topology.npz',allow_pickle=False) as bank:
        ids=bank['ids']
    scene,skin,gaze,layers=open_model(proof['parent'],proof)
    parent_poly=np.arange(len(skin.data.polygons))
    is_return=np.isin(parent_poly,source_faces)
    runs={}
    for frame,amount in TESTS:
        pose=f'{frame:g}:{amount:g}'
        stage['activate'](scene,gaze,'separated',amount,frame)
        row=collect(skin,layers,binding,ids,parent_poly,is_return)
        runs[pose]={'baseline':row}
        print('R502_BASELINE',pose,row['selfCounts'],row['layer']['cornea']['counts'],flush=True)
    scene,skin,gaze,layers=open_model(proof['source'],proof)
    candidate_poly=model['array'](skin.data.attributes[model['FACE_SOURCE']].data,'value',dtype='i4')
    assert (candidate_poly==-1).sum()==sum(row['added'] for row in proof['returnWalls'])
    row_ids=model['array'](skin.data.attributes[model['SITE']].data,'value',dtype='i4')
    assert all(np.count_nonzero(row_ids==i)>0 for i in range(1,5))
    operation={}
    for frame,amount in TESTS:
        pose=f'{frame:g}:{amount:g}'
        reference=runs[pose]['baseline']
        stable={tuple(row['source']) for row in reference['selfWitnesses'] if row['kind']=='exterior-exterior'}
        for mode in model['MODES']:
            t=perf_counter()
            model['activate'](scene,gaze,mode,amount,frame)
            row=collect(skin,layers,binding,ids,candidate_poly,candidate_poly==-1)
            row['seconds']=perf_counter()-t
            row['newExteriorSelf']=[w for w in row['selfWitnesses'] if w['kind']=='exterior-exterior' and w['source'] not in stable]
            assert row['rootHash']==reference['rootHash'] and row['layerHashes']==reference['layerHashes']
            runs[pose][mode]=row
            print('R502_CANDIDATE',pose,mode,row['selfCounts'],row['layer']['cornea']['counts'],flush=True)
        if pose=='1:1':
            for mode in (*model['MODES'],'arc'):
                model['activate'](scene,gaze,mode,amount,frame)
                v,_,_=mesh_data(skin)
                h=stage['array_hash'](v.astype('f4'))
                assert h==runs[pose][mode]['skinHash']
                operation[mode]=h
            assert operation['arc']!=operation['rolled']
    model['activate'](scene,gaze,'arc',0.,1.)
    assert digest(Path(proof['source']['path']))==proof['source']['sha256']
    write_json(ROOT/'contact-receipt.json',dict(source=proof['source'],parent=proof['parent'],poses=runs,
        operation=operation, preservedLayerHashes=True, preservedLashRoots=True,
        scope='Eight native held poses including first failure at frame 1, blink 0.75, and fractional frame 36.75. Skin polygon pairs compare like roles and avoid shared-vertex pairs. Replacement face identities are new. Signed distances are point samples to the oriented mesh, not continuous or volumetric clearance.'))


if __name__=='__main__':
    main()

