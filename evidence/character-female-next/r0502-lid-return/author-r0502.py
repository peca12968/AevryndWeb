"""Build connected inner eyelid strips with explicit rows and retain live outer skin."""
from collections import defaultdict
from pathlib import Path
from runpy import run_path

import bmesh
import bpy
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
probe=run_path(str(ROOT/'probe-r0502.py'))
chart=run_path(str(ROOT/'map-return-r0502.py'))
read_json,write_json,digest=(probe[k] for k in ('read_json','write_json','digest'))
stage=probe['stage']
author=stage['author']
BASELINE=probe['probe']['PARENT']
DEST=ROOT/'female-next-r0502-lid-return-UNACCEPTED.blend'
CONTROL='R502_Inner_Return'
MODES=('arc','rolled')
PHASES=(0.,.5,.75,.875,1.)
FACE_SOURCE='R502 Source face'
SITE='R502 Eyelid return row'
TAU=np.pi*2


def array(rows, prop, n=1, dtype='f4'):
    out=np.empty((len(rows),n),dtype)
    rows.foreach_get(prop,out.ravel())
    return out if n>1 else out[:,0]


def activate(scene,gaze,mode,phase,frame=1.):
    gaze[CONTROL]=MODES.index(mode)+1
    stage['activate'](scene,gaze,'separated',phase,frame)


def smooth(value):
    x=np.clip(value,0.,1.)
    return x*x*(3.-2.*x)


def unit(v):
    return v/np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1.e-10)


def order_loop(vertices, links, used, rings):
    start=min(vertices)
    stop=next(b for a,b in (edge for i in used for edge in zip(rings[str(i)],rings[str(i)][1:]+rings[str(i)][:1]))
              if a==start and b in links[start])
    out=[start,stop]
    while True:
        v=next(i for i in links[out[-1]] if i!=out[-2])
        if v==start:
            break
        out.append(v)
    assert set(out)==vertices
    return np.asarray(out,dtype='i4')


def match_deep(front,deep,xyz,center):
    def phase(ids):
        v=xyz[ids]-center
        return np.unwrap(np.arctan2(v[:,2],v[:,0]))
    ap,dp=phase(front),phase(deep)
    if (ap[-1]-ap[0])*(dp[-1]-dp[0])<0:
        deep=deep[::-1].copy()
        dp=phase(deep)
    sign=np.sign(ap[-1]-ap[0])
    outer=sign*(ap-ap[0])
    a=(sign*(dp-ap[0]))%TAU
    # Preserve deep-ring connectivity. One small local reversal is spread across
    # the adjoining segment so the zipper keeps that actual boundary edge.
    start=np.argmin(a)
    deep=np.roll(deep,-start)
    a=np.roll(a,-start)
    a=np.maximum.accumulate(a+np.arange(len(a))*1.e-6)
    a=np.minimum(a,TAU-(len(a)-np.arange(len(a)))*1.e-6)
    assert np.all(np.diff(outer)>0) and a[0]<.4, (outer,a)
    return deep,outer,a


def interpolate_deep(values, a, u):
    ap=np.r_[a[-1]-TAU,a,a[0]+TAU]
    order=np.r_[len(a)-1,np.arange(len(a)),0]
    left=np.clip(np.searchsorted(ap,u,side='right')-1,0,len(ap)-2)
    t=(u-ap[left])/np.maximum(ap[left+1]-ap[left],1.e-10)
    return values[order[left]]*(1-t[:,None])+values[order[left+1]]*t[:,None]


def spherical(outer,inner,center,t,rolled):
    a,b=outer-center,inner-center
    ra,rb=np.linalg.norm(a,axis=1),np.linalg.norm(b,axis=1)
    au,bu=unit(a),unit(b)
    angle=np.arccos(np.clip((au*bu).sum(1),-.99999,.99999))
    tau=t if not rolled else t + .115*np.sin(np.pi*t)
    direction=(np.sin((1-tau)*angle)[:,None]*au+np.sin(tau*angle)[:,None]*bu)
    shoulder=(.00014 if rolled else .00007)*np.sin(np.pi*t)
    radius=(1-t)*ra+t*rb+shoulder
    return center+unit(direction)*radius[:,None]


def find_unique(target, xyz, available):
    cost=np.linalg.norm(target[:,None,:]-xyz[available][None,:,:],axis=2)
    result=np.full(len(target),-1,dtype='i4')
    ordered=np.argsort(np.min(cost,axis=1))
    for i in ordered:
        j=np.argmin(cost[i])
        assert np.isfinite(cost[i,j])
        result[i]=available[j]
        cost[:,j]=np.inf
    return result


def triangles_between(a,b):
    assert len(a)==len(b)
    out=[]
    for j in range(len(a)):
        n=(j+1)%len(a)
        out.extend(((a[j],a[n],b[j]),(a[n],b[n],b[j])))
    return out


def zipper(row,deep,ap,dp):
    out=[]
    j=k=0
    # At index zero, outer starts on the same meridian as deep to within its
    # first actual boundary interval; no interior order is sorted or deleted.
    while j<len(row) or k<len(deep):
        a=row[j%len(row)]
        b=deep[k%len(deep)]
        aj=ap[j+1] if j+1<len(row) else TAU if j<len(row) else np.inf
        bk=dp[k+1] if k+1<len(deep) else TAU+dp[0] if k<len(deep) else np.inf
        if aj<=bk:
            out.append((a,row[(j+1)%len(row)],b))
            j+=1
        else:
            out.append((a,deep[(k+1)%len(deep)],b))
            k+=1
    return out


def barycentric(point, triangle):
    a,b,c=triangle
    z=np.linalg.lstsq(np.column_stack((b-a,c-a)),point-a,rcond=None)[0]
    w=np.maximum(0.,np.r_[1.-z.sum(),z])
    return w/w.sum()


def build_maps(data,bank,world):
    components,edge_faces=chart['chart_faces'](data['rings'],data['faceMaterials'])
    assert len(components)==2
    points=bank['0/cornea']
    ids=bank['ids']
    original=world.copy()
    new_faces=[]
    replaced=set()
    models=[]
    for comp in components:
        edge_kind,links=chart['boundary'](comp,edge_faces)
        loops=chart['partition'](links)
        assert len(loops)==2 and all(len(v)==2 for v in links.values())
        outside=next(loop for loop in loops if all(edge_kind[e]=='skin' for e in edge_kind if e[0] in loop))
        inside=next(loop for loop in loops if loop!=outside)
        outer=order_loop(outside,links,comp,data['rings'])
        deep=order_loop(inside,links,comp,data['rings'])
        side=int(np.sign(world[outer].mean(0)[0]))
        source=points[np.sign(points[:,0])==side]
        eye_mm=source*1000.
        mat=np.c_[2*eye_mm,np.ones(len(source))]
        center=np.linalg.lstsq(mat,(eye_mm*eye_mm).sum(1),rcond=None)[0][:3]*.001
        deep,ap,dp=match_deep(outer,deep,world,center)
        v_deep=interpolate_deep(world[deep],dp,ap)
        values=(.29,.62)
        targets=np.concatenate([spherical(world[outer],v_deep,center,t,False) for t in values])
        inner_verts=sorted({v for i in comp for v in data['rings'][str(i)]}-outside-inside)
        assert len(inner_verts)>=len(targets)
        used=find_unique(targets,world,np.asarray(inner_verts))
        faces=bank['0/face']
        polygon=bank['0/polygon']
        selection=np.isin(polygon,tuple(comp))
        faces,polygon=faces[selection],polygon[selection]
        compact=np.searchsorted(ids,faces)
        bvh=probe['tree'](bank['0/skin'],compact)
        donor=[]
        bary=[]
        donor_poly=[]
        near=[]
        for target in targets:
            location,_,idx,dist=bvh.find_nearest(Vector(target))
            face=faces[idx]
            donor.append(face)
            bary.append(barycentric(np.asarray(location),world[face]))
            donor_poly.append(polygon[idx])
            near.append(np.asarray(location))
        donor=np.array(donor,dtype='i4')
        bary=np.array(bary)
        near=np.array(near)
        # Neutral layout remains close to the source wall while putting the
        # new circumferential supports on the explicit eye-centred trajectory.
        rows=np.split(used,len(values))
        neutral=.67*targets+.33*near
        world[used]=neutral
        children=triangles_between(outer,rows[0])+triangles_between(rows[0],rows[1])+zipper(rows[1],deep,ap,dp)
        new_faces.extend(children)
        replaced.update(comp)
        models.append(dict(side=side,outer=outer,deep=deep,ap=ap,dp=dp,center=center,used=used,
            donor=donor,bary=bary,donor_poly=donor_poly,values=values,neutral=neutral,
            removed=len(comp),added=len(children),unused=sorted(set(inner_verts)-set(used))))
    return models,replaced,new_faces,original


def remesh(obj,models,replaced,children,original_world,world):
    mesh=obj.data
    before_counts=(len(mesh.vertices),len(mesh.edges),len(mesh.polygons))
    original_keys={key.name:author['xyz'](key.data) for key in mesh.shape_keys.key_blocks}
    old_base=original_keys[mesh.shape_keys.reference_key.name].copy()
    old_faces=[tuple(face.vertices) for face in mesh.polygons]
    old_starts=array(mesh.polygons,'loop_start',dtype='i4')
    uv={layer.name:array(layer.uv,'vector',2) for layer in mesh.uv_layers}
    normals=array(mesh.corner_normals,'vector',3) if mesh.has_custom_normals else None
    weight_donors={}
    uv_donors={}
    for m in models:
        for j,i in enumerate(m['used']):
            i=int(i)
            tri=m['donor'][j]
            q=m['bary'][j]
            tally=defaultdict(float)
            for a,w in zip(tri,q):
                for group in mesh.vertices[int(a)].groups:
                    tally[group.group]+=group.weight*w
            weight_donors[i]=dict(tally)
            parent=int(m['donor_poly'][j])
            lookup={v:int(old_starts[parent])+k for k,v in enumerate(old_faces[parent])}
            uv_donors[i]=(np.array([lookup[v] for v in tri]),q)
    # Boundary UVs are sampled only from the original return, on the same side
    # of the texture seam as the replacement faces.
    for i in sorted(replaced):
        for k,v in enumerate(old_faces[i]):
            uv_donors.setdefault(v,(np.array([int(old_starts[i])+k]),np.array([1.])))
    bm=bmesh.new()
    try:
        bm.from_mesh(mesh,use_shape_key=False)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        bm.faces.index_update()
        owner=bm.faces.layers.int.new(FACE_SOURCE)
        for face in bm.faces:
            face[owner]=face.index
        old_nonmanifold=sum(not e.is_manifold for e in bm.edges if len(e.link_faces)>0)
        remove=[bm.faces[i] for i in sorted(replaced)]
        old_edges={e for face in remove for e in face.edges}
        for face in remove:
            bm.faces.remove(face)
        for tri in children:
            face=bm.faces.new(tuple(bm.verts[int(j)] for j in tri))
            face[owner]=-1
            face.smooth=True
            face.material_index=0
        for e in old_edges:
            if e.is_valid and not e.link_faces:
                bm.edges.remove(e)
        new_nonmanifold=sum(not e.is_manifold for e in bm.edges if len(e.link_faces)>0)
        assert old_nonmanifold==new_nonmanifold,(old_nonmanifold,new_nonmanifold)
        bm.to_mesh(mesh)
    finally:
        bm.free()
    mesh.update()
    assert len(mesh.vertices)==before_counts[0]
    source=array(mesh.attributes[FACE_SOURCE].data,'value',dtype='i4')
    assert np.count_nonzero(source==-1)==len(children) and len(source)==before_counts[2]-len(replaced)+len(children)
    group_set=tuple(obj.vertex_groups)
    for i,weights in weight_donors.items():
        for index in [row.group for row in mesh.vertices[i].groups]:
            group_set[index].remove([i])
        for group,weight in weights.items():
            if weight>0:
                group_set[group].add([i],weight,'REPLACE')
    inverse=np.asarray(obj.matrix_world.inverted())[:3,:3]
    for key in mesh.shape_keys.key_blocks:
        coords=original_keys[key.name].copy()
        for m in models:
            ids,donor,bary=m['used'],m['donor'],m['bary']
            donor_base=np.sum(old_base[donor]*bary[:,:,None],axis=1)
            donor_morph=np.sum(coords[donor]*bary[:,:,None],axis=1)
            # World-space displacement from the source's evaluated neutral point
            # retains the donor's rig-relative rest space and all original keys.
            orig=np.sum(original_world[donor]*bary[:,:,None],axis=1)
            delta=(world[ids]-orig)@inverse.T
            coords[ids]=donor_base+delta+(donor_morph-donor_base)
        key.data.foreach_set('co',coords.ravel())
    new_base=author['xyz'](mesh.shape_keys.reference_key.data)
    changed=np.sort(np.concatenate([m['used'] for m in models]))
    keep=np.ones(len(old_base),dtype=bool)
    keep[changed]=False
    assert np.array_equal(new_base[keep],old_base[keep])
    unchanged_loops=np.full(len(mesh.loops),-1,dtype='i4')
    created={}
    for face,i in zip(mesh.polygons,source):
        if i>=0:
            ids=old_faces[i]
            assert tuple(face.vertices)==ids
            unchanged_loops[face.loop_start:face.loop_start+face.loop_total]=old_starts[i]+np.arange(face.loop_total)
        else:
            created.update((loop,uv_donors[vert]) for loop,vert in zip(face.loop_indices,face.vertices))
    preserve=unchanged_loops>=0
    for layer in mesh.uv_layers:
        original=uv[layer.name]
        values=np.empty((len(mesh.loops),2),'f4')
        values[preserve]=original[unchanged_loops[preserve]]
        for loop,(donors,w) in created.items():
            values[loop]=w@original[donors]
        layer.uv.foreach_set('vector',values.ravel())
        assert np.array_equal(array(layer.uv,'vector',2)[preserve],values[preserve])
    if normals is not None:
        value=np.zeros((len(mesh.loops),3),'f4')
        value[preserve]=normals[unchanged_loops[preserve]]
        mesh.normals_split_custom_set(value.tolist())
    tag=mesh.attributes.new(SITE,'INT','POINT')
    rows=np.zeros(len(mesh.vertices),'i4')
    for m in models:
        rows[m['outer']]=1
        rows[m['deep']]=4
        for j,idx in enumerate(np.split(m['used'],2)):
            rows[idx]=j+2
    tag.data.foreach_set('value',rows)
    mesh.update()
    return dict(before=before_counts,after=[len(mesh.vertices),len(mesh.edges),len(mesh.polygons)],
        beforeNonmanifold=old_nonmanifold,afterNonmanifold=new_nonmanifold,rewiredVertices=len(changed),
        sourceUnusedIds=sum(len(m['unused']) for m in models),preservedUvLayers=list(uv))


def rim_motion(pos,m,near_ids,anchor_ids,amount,rolled):
    outer=m['outer']
    boundary=pos[outer]
    # Fair the upper/lower margin in its ordered 3D curve. The two halves have
    # their own support; the corners taper to their original join.
    a=m['ap']
    # Use stable material-side assignment (neutral topology), not current z.
    upper=m['upper']
    wrap=np.abs(a[:,None]-a)
    wrap=np.minimum(wrap,TAU-wrap)
    weights=np.exp(-.5*(wrap/(.16 if rolled else .105))**2)
    weights*=upper[:,None]==upper
    rounded=(weights@boundary)/weights.sum(1)[:,None]
    difference=rounded-boundary
    shoulder=smooth(np.abs(m['neutralSin'])/.30)
    difference*=shoulder[:,None]*(.72 if rolled else .48)*smooth((amount-.50)/.43)
    length=np.linalg.norm(difference,axis=1)
    max_depth=.00054 if rolled else .00035
    difference*=np.minimum(1.,max_depth/np.maximum(length,1.e-10))[:,None]
    difference[np.isin(outer,anchor_ids)]=0.
    base=pos[near_ids]
    delta=base[:,None,:]-boundary[None,:,:]
    distance=np.linalg.norm(delta,axis=2)
    nearby=np.argmin(distance,axis=1)
    proximity=distance[np.arange(len(base)),nearby]
    motion=difference[nearby]*smooth(1.-proximity/.0033)[:,None]
    motion[np.isin(near_ids,anchor_ids)]=0.
    # The source return and socket are handled by the separate interior rows.
    return motion,difference


def driver(key,gaze,mode,i):
    at=PHASES[i]
    if i==0:
        weight=f'min(1,max(0,({PHASES[1]}-blink)/{PHASES[1]}))'
    else:
        weight=f'min(1,max(0,(blink-{PHASES[i-1]})/{at-PHASES[i-1]}))'
        if i+1<len(PHASES):
            weight+=f'*min(1,max(0,({PHASES[i+1]}-blink)/{PHASES[i+1]-at}))'
    d=key.driver_add('value').driver
    for n,prop in (('mode',CONTROL),('blink',author['BLINK'])):
        v=d.variables.new()
        v.name,v.type=n,'SINGLE_PROP'
        v.targets[0].id=gaze
        v.targets[0].data_path=f'["{prop}"]'
    d.expression=f'(mode=={MODES.index(mode)+1})*{weight}'


def main():
    data=read_json(ROOT/'return-topology.json')
    parent=read_json(BASELINE/'construction-receipt.json')
    assert data['parent']==parent['source']
    source=Path(parent['source']['path'])
    assert digest(source)==parent['source']['sha256'] and not DEST.exists()
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    skin,gaze=(bpy.data.objects[parent[name]] for name in ('body','gaze'))
    gaze[CONTROL]=0
    gaze.id_properties_ui(CONTROL).update(min=0,max=2,soft_min=1,soft_max=2,
        description='1 concentric arc return, 2 rolled return. 0 shows the inherited donor motion on the new topology.')
    stage['activate'](scene,gaze,'separated',0.,1.)
    pos,_,_=probe['mesh_data'](skin)
    with np.load(ROOT/'return-topology.npz',allow_pickle=False) as bank:
        models,replaced,children,original=build_maps(data,bank,pos.copy())
        for m in models:
            theta=original[m['outer']]-m['center']
            m['neutralSin']=theta[:,2]/np.maximum(np.linalg.norm(theta[:,[0,2]],axis=1),1.e-10)
            m['upper']=m['neutralSin']>=0.
        topology=remesh(skin,models,replaced,children,original,pos)
        basis=author['xyz'](skin.data.shape_keys.reference_key.data)
        anchors=np.unique(bank['tri'])
        inner_ids=np.concatenate([np.r_[m['used'],m['deep'],m['unused']] for m in models]).astype('i4')
        outer_faces=[ring for id,ring in data['rings'].items() if data['faceMaterials'][id]==8]
        outer_skin=np.unique([i for ring in outer_faces for i in ring])
        eligible=np.setdiff1d(outer_skin,inner_ids)
        inverse=np.asarray(skin.matrix_world.inverted())[:3,:3]
        records={mode:[] for mode in MODES}
        for i,amount in enumerate(PHASES):
            gaze[CONTROL]=0
            stage['activate'](scene,gaze,'separated',amount,1.)
            raw,_,_=probe['mesh_data'](skin)
            ref=raw.copy()
            ref[bank['ids']]=bank[f'{i}/skin']
            for mode in MODES:
                rolled=mode=='rolled'
                field=np.zeros_like(raw)
                for m in models:
                    outer=m['outer']
                    side=m['side']
                    near=eligible[(np.sign(original[eligible,0])==side)]
                    outer_delta,attached=rim_motion(ref,m,near,anchors,amount,rolled)
                    field[near]=outer_delta
                    field[outer]=attached
                    current=ref[outer]+attached
                    back=interpolate_deep(ref[m['deep']],m['dp'],m['ap'])
                    targets=np.concatenate([spherical(current,back,m['center'],t,rolled) for t in m['values']])
                    donor=np.sum(ref[m['donor']]*m['bary'][:,:,None],axis=1)
                    # The arc follows the actual blink at both joins. The rolled
                    # variant carries more of the spherical arc around the globe.
                    weight=.78 if rolled else .62
                    targets=weight*targets+(1.-weight)*donor
                    field[m['used']]=targets-raw[m['used']]
                assert not np.any(field[anchors])
                assert np.isfinite(field).all()
                coords=(basis+field@inverse.T).astype('f4')
                changed=np.flatnonzero(np.any(coords!=basis,axis=1))
                key=skin.shape_key_add(name=f'R502 {mode} | {amount:g} blink',from_mix=False)
                key.data.foreach_set('co',coords.ravel())
                driver(key,gaze,mode,i)
                records[mode].append(dict(key=key.name,phase=amount,vertices=len(changed),
                    coordinateHash=stage['array_hash'](coords),maximumMetres=float(np.linalg.norm(field,axis=1).max())))
        details=[]
        for m in models:
            details.append(dict(side=m['side'],outer=m['outer'].tolist(),deep=m['deep'].tolist(),
                rows=[row.tolist() for row in np.split(m['used'],2)],removed=m['removed'],added=m['added'],
                donor=m['donor'].tolist(),bary=m['bary'].tolist(),unused=m['unused']))
    activate(scene,gaze,'arc',0.,1.)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True)
    write_json(ROOT/'construction-receipt.json',dict(source=dict(path=str(DEST),sha256=digest(DEST),bytes=DEST.stat().st_size),
        parent=parent['source'],body=skin.name,gaze=gaze.name,blinkProperty=author['BLINK'],layoutProperty=CONTROL,default='arc',
        topology=topology,returnWalls=details,faceOwner=FACE_SOURCE,rowAttribute=SITE,variants=records,
        lashAnchors=len(anchors),hair=parent['hair'],bankSha256=digest(ROOT/'return-topology.npz')))
    print('R502_RETURN',topology,[(row['side'],row['removed'],row['added']) for row in details],flush=True)


if __name__=='__main__':
    main()

