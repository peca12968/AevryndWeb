"""Author both 3D front-margin fits against native skin and ocular geometry."""
from pathlib import Path
from runpy import run_path

import bpy
import numpy as np

ROOT=Path(__file__).resolve().parent
topo=run_path(str(ROOT/'topology-r0503.py'))
previous=topo['stage']
r500=topo['ocular']['stage']
author=topo['body_author']
read_json,write_json,digest=(topo[k] for k in ('read_json','write_json','digest'))
mesh_data,tree=(previous['probe'][k] for k in ('mesh_data','tree'))
BASELINE=previous['BASELINE']
DEST=ROOT/'female-next-r0503-conforming-lid-UNACCEPTED.blend'
CONTROL='R503_Front_Lid'
MODES=('control','fair','rest')
KNOTS=(.5,.75,.875,1.)
POSES=((1.,0.),(1.,.75),(1.,.875),(1.,1.),(36.75,1.),(37.,.92),(37.,1.))


def activate(scene,gaze,mode,phase,frame=1.):
    gaze[CONTROL]=MODES.index(mode)
    r500['activate'](scene,gaze,'separated',phase,frame)


def install_driver(key,gaze,mode,index):
    at,lo=KNOTS[index],KNOTS[index-1]
    weight=f'min(1,max(0,(blink-{lo})/{at-lo}))'
    if index+1<len(KNOTS):
        hi=KNOTS[index+1]
        weight+=f'*min(1,max(0,({hi}-blink)/{hi-at}))'
    d=key.driver_add('value').driver
    for label,name in (('mode',CONTROL),('blink',author['BLINK'])):
        var=d.variables.new()
        var.name,var.type=label,'SINGLE_PROP'
        var.targets[0].id=gaze
        var.targets[0].data_path=f'["{name}"]'
    d.expression=f'(mode=={MODES.index(mode)})*{weight}'


def region_laplacian(graph,active,closed,open_):
    index={int(i):j for j,i in enumerate(active)}
    L=np.eye(len(active))
    bend=np.zeros((len(active),3))
    rest=np.zeros_like(bend)
    for row,i in enumerate(active):
        neighbors=np.array(list(graph[int(i)]))
        measure=np.array(list(graph[int(i)].values()))
        weight=1/np.maximum(measure,.00028)
        weight/=weight.sum()
        for other,w in zip(neighbors,weight):
            if other in index:
                L[row,index[other]]-=w
        c=closed[neighbors]-closed[i]
        n=open_[neighbors]-open_[i]
        a,_,b=np.linalg.svd((weight[:,None]*n).T@c)
        if np.linalg.det(a@b)<0:
            a[:,-1]*=-1
        rest[row]=-(weight@n)@(a@b)
        bend[row]=-(weight@c)
    return L,bend,rest


def fit(graph,active,strength,neutral,closed,mode,pins,triangles,donors,new_ids):
    original=active[~np.isin(active,tuple(pins))]
    amount=strength[~np.isin(active,tuple(pins))]
    L,bend,rest=region_laplacian(graph,original,closed,neutral)
    target=-bend if mode=='fair' else .82*rest-bend
    # The same spatial stiffness acts in all three directions. Natural folds
    # from the rest state remain the target in the second comparison.
    regularizer=np.diag(.030+.15*(1.-amount)**2+(.011 if mode=='rest' else 0.))
    result=np.linalg.solve(L.T@L+regularizer,L.T@(target*amount[:,None]))
    limit=.00116 if mode=='fair' else .00130
    result*=np.minimum(1.,limit/np.maximum(np.linalg.norm(result,axis=1),1.e-12))[:,None]
    delta=np.zeros_like(closed)
    delta[original]=result
    support=delta[donors].mean(1)
    # Project each small internal support to its parent tangent blend. The
    # parent perimeter and protected root indices remain explicit constraints.
    near=closed+delta
    normals=np.zeros_like(near)
    tri=triangles[np.isin(triangles,original).any(1)]
    n=np.cross(near[tri[:,1]]-near[tri[:,0]],near[tri[:,2]]-near[tri[:,0]])
    for i in range(3):
        np.add.at(normals,tri[:,i],n)
    dn=normals[donors]
    dn/=np.maximum(1.e-11,np.linalg.norm(dn,axis=2,keepdims=True))
    corners=near[donors]
    mid=corners.mean(1)
    offset=np.mean(np.sum((corners-mid[:,None])*dn,axis=2,keepdims=True)*dn,axis=1)
    offset*=np.minimum(1.,.00014/np.maximum(np.linalg.norm(offset,axis=1),1.e-10))[:,None]
    mask=np.isin(donors,original).any(1) & ~np.isin(donors,tuple(pins)).any(1)
    support+=offset*mask[:,None]*(.70 if mode=='fair' else .90)
    delta[new_ids]=support
    return delta


def contact(sample,affected,layers):
    v,f,p=sample
    rows=np.flatnonzero(affected[f].any(1))
    region=tree(v,f[rows])
    whole=tree(v,f)
    seen={}
    for i,j in region.overlap(whole):
        a=rows[i]
        if p[a]==p[j] or (f[a,:,None]==f[j,None,:]).any():
            continue
        key=('skin',*sorted((int(p[a]),int(p[j]))))
        if key not in seen:
            seen[key]=dict(vertices=np.union1d(f[a],f[j]).tolist(),
                positionMetres=((v[f[a]].mean(0)+v[f[j]].mean(0))/2).tolist())
    for role,(fixture,ids) in layers.items():
        for i,j in region.overlap(fixture):
            a=rows[i]
            key=(role,int(p[a]),int(ids[j]))
            if key not in seen:
                seen[key]=dict(vertices=f[a].tolist(),positionMetres=v[f[a]].mean(0).tolist())
    return seen


def fixtures(layers):
    state={}
    for role,obj in layers.items():
        v,f,p=mesh_data(obj)
        state[role]=tree(v,f),p
    return state


def build_pose_reference(scene,body,gaze,layers,affected):
    samples={}
    for frame,phase in POSES:
        activate(scene,gaze,'control',phase,frame)
        mesh=mesh_data(body)
        surfaces=fixtures(layers)
        samples[frame,phase]=(mesh,surfaces,contact(mesh,affected,surfaces))
    return samples


def check_field(scene,body,gaze,mode,affected,samples):
    issues={}
    pins=set()
    for frame,phase in POSES:
        activate(scene,gaze,mode,phase,frame)
        current=mesh_data(body)
        reference,surfaces,baseline=samples[frame,phase]
        assert np.array_equal(current[0][~affected],reference[0][~affected])
        before=len(baseline)
        after=contact(current,affected,surfaces)
        added=sorted(after.keys()-baseline.keys())
        row=[dict(pair=key,**after[key]) for key in added]
        pins.update(v for witness in row for v in witness['vertices'])
        issues[f'{frame:g}:{phase:g}']=dict(before=before,after=len(after),added=row)
    return issues,pins


def main():
    parent=read_json(BASELINE/'construction-receipt.json')
    source=Path(parent['source']['path'])
    assert digest(source)==parent['source']['sha256'] and not DEST.exists()
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    body,gaze=(bpy.data.objects[parent[k]] for k in ('body','gaze'))
    binding=topo['ocular']['anchors']()
    anchors=np.unique(binding['tri'])
    gaze[CONTROL]=0
    gaze.id_properties_ui(CONTROL).update(min=0,max=2,description='0 exact conforming split, 1 curvature fairing, 2 rest curvature transport')
    activate(scene,gaze,'control',0.)
    old_neutral,old_tri,_=mesh_data(body)
    activate(scene,gaze,'control',1.)
    old_closed,_,_=mesh_data(body)
    graph,active,strength,selected,wall,ring,locked=topo['domain'](body,old_neutral,old_closed,binding['tri'])
    print('R503_DOMAIN',len(active),len(selected),len(ring),sum(i in wall for i in selected),flush=True)
    activate(scene,gaze,'control',0.)
    geometry=topo['rebuild'](body,selected)
    appended=geometry.pop('newVertices')
    donors=geometry.pop('donors')
    geometry.pop('faceParents')
    affected=np.zeros(len(body.data.vertices),dtype=bool)
    affected[active]=True
    affected[appended]=True
    raw=mesh_data(body)[0]
    assert np.array_equal(raw[:len(old_neutral)],old_neutral)
    interpolation=float(np.linalg.norm(raw[appended]-raw[donors].mean(1),axis=1).max())
    assert interpolation<1.2e-5,interpolation
    inverse=np.asarray(body.matrix_world.inverted())[:3,:3]
    basis=author['xyz'](body.data.shape_keys.reference_key.data)
    layer_names=r500['previous']['LAYERS']
    labels=('eye','cornea','meniscus','lash')
    layers={role:bpy.data.objects[name] for role,name in zip(labels,layer_names)}
    samples=build_pose_reference(scene,body,gaze,layers,affected)
    for mode in MODES[1:]:
        for index,phase in enumerate(KNOTS[1:],1):
            key=body.shape_key_add(name=f'R503 {mode} | {phase:g}',from_mix=False)
            install_driver(key,gaze,mode,index)
    records={}
    reports={}
    for mode in MODES[1:]:
        pins=set()
        operations=[]
        for attempt in range(3):
            spec=[]
            for phase in KNOTS[1:]:
                ref=samples[1.,phase][0]
                offset=fit(graph,active,strength,raw,ref[0],mode,pins,old_tri,donors,appended)
                # Blend in progressively as the existing animation enters closure.
                offset*=float({.75:.63,.875:.83,1.:1.}[phase])
                assert np.isfinite(offset).all() and not offset[anchors].any()
                coords=(basis+offset@inverse.T).astype('f4')
                key=body.data.shape_keys.key_blocks[f'R503 {mode} | {phase:g}']
                key.data.foreach_set('co',coords.ravel())
                spec.append(dict(key=key.name,phase=phase,vertices=int(np.count_nonzero(np.any(coords!=basis,axis=1))),
                    maximumMetres=float(np.linalg.norm(offset,axis=1).max()),coordinateHash=r500['array_hash'](coords)))
            body.data.shape_keys.update_tag()
            bpy.context.view_layer.update()
            issues,hit=check_field(scene,body,gaze,mode,affected,samples)
            total=sum(len(row['added']) for row in issues.values())
            operations.append(dict(attempt=attempt+1,pins=sorted(pins),newPairObservations=total,poses=issues))
            print('R503_SCREEN',mode,attempt+1,total,len(pins),flush=True)
            if not hit or attempt==2:
                break
            pins.update(set(active.tolist())&hit)
            for i in hit:
                if i>=len(old_neutral):
                    pins.update(int(j) for j in donors[i-len(old_neutral)])
        records[mode]=spec
        reports[mode]=operations
    activate(scene,gaze,'rest',0.,1.)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True)
    write_json(ROOT/'construction-receipt.json',dict(source=dict(path=str(DEST),bytes=DEST.stat().st_size,sha256=digest(DEST)),
        parent=parent['source'],body=body.name,gaze=gaze.name,blinkProperty=author['BLINK'],layoutProperty=CONTROL,default='rest',
        hair=parent['hair'],cheekCoordinateHash=parent['cheekCoordinateHash'],topology=geometry,faceOwner=topo['OWNER'],
        posteriorReturnFaces=sorted(wall-set(selected)),splitFrontReturnFaces=sorted(wall&set(selected)),
        protectedLashAnchors=len(anchors),rootInterpolateMaxMetres=interpolation,
        movableSourceVertices=active.tolist(),variants=records))
    write_json(ROOT/'screen-receipt.json',dict(sourceSha256=digest(DEST),poses=POSES,variants=reports,
        definition='Native finite triangle overlaps versus the conforming split control. Same polygon identities across fits. Collisions pin only participating source vertices before a refit, maximum three measured attempts.'))


if __name__=='__main__':
    main()

