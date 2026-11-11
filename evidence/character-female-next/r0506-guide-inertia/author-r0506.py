"""Bake distributed guide motion for the displayed r505 hairstyle in Blender."""
from pathlib import Path
from runpy import run_path
from time import perf_counter

import bpy
import numpy as np
from mathutils import Matrix,Vector

ROOT=Path(__file__).resolve().parent
PARENT=ROOT.parent/'r0505-ear-nape-bridge'
previous=run_path(str(PARENT/'author-r0505.py'))
contact=run_path(str(PARENT/'contact-r0505.py'))
r500=previous['r500']
read_json,write_json,digest,positions,attribute,array_hash=(
    previous[k] for k in ('read_json','write_json','digest','positions','attribute','array_hash'))
mesh_data,tree,xform=(contact[k] for k in ('mesh_data','tree','xform'))
DEST=ROOT/'female-next-r0506-guide-inertia-UNACCEPTED.blend'
STATIONS=np.array([0,8,16,24,32,40,48,56,64,72,79],dtype='i4')
PINNED=2
SUBSTEPS=8
MODIFIER='R506 baked guide dynamics'
PFX='AEVRYND_R506_'
MODES=('spring','rod')


def get_pose(scene,gaze,hair):
    matrices=[]
    for frame in range(1,38):
        r500['activate'](scene,gaze,'separated',0.,float(frame))
        matrices.append(hair.matrix_world.copy())
    r500['activate'](scene,gaze,'separated',0.,1.)
    return matrices


def make_groups(bank):
    samples=bank[:,[0,19,39,59,79]].astype('f8')
    features=(samples*np.array([.62,.87,1.0,1.04,.90])[None,:,None]).reshape(len(bank),-1)
    root=bank[:,0]
    behind=bank[:,51,1]>.036
    side=bank[:,34,0]>=0
    pool=side.astype('i4')+2*behind.astype('i4')
    nearest=np.empty((len(bank),3),'i4')
    weights=np.empty((len(bank),3),'f4')
    guides=[]
    for k,guide_count in enumerate((34,34,30,30)):
        ids=np.flatnonzero(pool==k)
        x=features[ids]
        distance=np.full(len(x),np.inf)
        centre=x.mean(0)
        choice=int(np.linalg.norm(x-centre,axis=1).argmin())
        picked=[]
        for _ in range(guide_count):
            picked.append(choice)
            distance=np.minimum(distance,np.sum((x-x[choice])**2,axis=1))
            choice=int(distance.argmax())
        refs=x[picked]
        offset=len(guides)
        guides.extend(ids[picked].tolist())
        for first in range(0,len(ids),850):
            end=min(first+850,len(ids))
            ds=np.sum((x[first:end,None]-refs[None])**2,axis=2)
            order=np.argsort(ds,axis=1)[:,:3]
            d=np.take_along_axis(ds,order,axis=1)
            # Blend compatible whole paths rather than introducing a lock edge.
            w=(d+.0000028)**-1.6
            w/=w.sum(1)[:,None]
            nearest[ids[first:end]]=order+offset
            weights[ids[first:end]]=w
    return np.array(guides,'i4'),nearest,weights,pool


def signed(p,bvh):
    point=Vector(p)
    hit,n,_,d=bvh.find_nearest(point)
    return (d if (point-hit).dot(n)>=0 else -d),np.asarray(n)


def force_step(p,v,target,prev,omega,damping,gravity,dt):
    desired_velocity=(target-prev)/dt
    v+=(omega**2*(target-p)+2*damping*omega*(desired_velocity-v)+gravity)*dt
    p+=v*dt


def project_lengths(p,lengths,free):
    for parity in (0,1):
        idx=np.arange(parity,p.shape[1]-1,2)
        delta=p[:,idx+1]-p[:,idx]
        norm=np.maximum(np.linalg.norm(delta,axis=2),1e-10)
        left=free[idx]
        right=free[idx+1]
        denom=np.maximum(left+right,1e-10)
        change=(delta*(.91*(norm-lengths[:,idx])/norm)[:,:,None])/denom[None,:,None]
        p[:,idx]+=change*left[None,:,None]
        p[:,idx+1]-=change*right[None,:,None]


def collision(p,inverse,matrix,bvh,clearance):
    local=xform(p,inverse)
    hits=0
    max_move=0.
    for i,j in np.argwhere(clearance>0.):
        gap,n=signed(local[i,j],bvh)
        if gap<clearance[i,j]:
            correction=clearance[i,j]-gap
            p[i,j]+=n@matrix[:3,:3].T*correction
            hits+=1
            max_move=max(max_move,float(correction))
    return hits,max_move


def solve(rest,mats,bvh,fps,mode,project_collision=collision):
    start=perf_counter()
    nr,nj,_=rest.shape
    coord=np.linspace(0.,1.,nj)
    real_length=np.linalg.norm(np.diff(rest,axis=1),axis=2).sum(1)
    speed=(real_length/np.median(real_length))**-.32
    region=np.where(rest[:,5,1]>.034,1.07,.94)
    root_stiff=24.+37.*(1-coord)**1.9
    if mode=='rod':
        root_stiff=16.5+37.*(1-coord)**1.75
    omega=(speed*region)[:,None,None]*root_stiff[None,:,None]
    damping=.66 if mode=='spring' else .58
    dt=1./(fps*SUBSTEPS)
    free=np.clip((coord-.08)*3.,0.,1.)
    free[:PINNED]=0.
    lengths=np.linalg.norm(np.diff(rest,axis=1),axis=2)
    limit=np.zeros(rest.shape[:2],'f8')
    if mode=='rod':
        for i in range(nr):
            for j in range(PINNED,nj):
                gap,_=signed(rest[i,j],bvh)
                limit[i,j]=min(.00065,max(.000035,gap*.62))
    current=xform(rest,np.asarray(mats[0]))
    velocity=np.zeros_like(current)
    prior=current.copy()
    basis_g=np.array([0.,0.,-9.81])
    output=np.zeros((len(mats),nr,nj,3),'f4')
    impacts=0
    max_step=0.
    peak_length=0.
    frame_peaks=[]
    for frame in range(1,len(mats)):
        q0,q1=mats[frame-1].to_quaternion(),mats[frame].to_quaternion()
        a0,a1=mats[frame-1].translation,mats[frame].translation
        for step in range(1,SUBSTEPS+1):
            t=step/SUBSTEPS
            R=q0.slerp(q1,t).to_matrix().to_4x4()
            R.translation=a0.lerp(a1,t)
            matrix=np.asarray(R)
            inv=np.asarray(R.inverted())
            target=xform(rest,matrix)
            # The authored rest guide represents its loaded gravity shape.
            # Only the changing gravity direction enters as an extra force.
            gravity=basis_g-(matrix[:3,:3]@basis_g)
            prev=current.copy()
            force_step(current,velocity,target,prior,omega,damping,gravity,dt)
            current[:,:PINNED]=target[:,:PINNED]
            if mode=='rod':
                for _ in range(5):
                    project_lengths(current,lengths,free)
                    current[:,:PINNED]=target[:,:PINNED]
                hits,delta=project_collision(current,inv,matrix,bvh,limit)
                impacts+=hits
                max_step=max(max_step,delta)
                velocity=(current-prev)/dt
            prior=target
        local=xform(current,np.asarray(mats[frame].inverted()))
        motion=local-rest
        motion[:,:PINNED]=0.
        output[frame]=motion.astype('f4')
        stretch=np.linalg.norm(np.diff(local,axis=1),axis=2)/np.maximum(lengths,1e-9)-1
        peak_length=max(peak_length,float(np.max(abs(stretch))))
        frame_peaks.append(float(np.linalg.norm(motion,axis=2).max()))
    return output,dict(guides=nr,stations=nj,pinnedStations=PINNED,substepsPerFrame=SUBSTEPS,
        mode=mode,dampingRatio=damping,tipOmegaRange=[float(omega[:,-1].min()),float(omega[:,-1].max())],
        guideCollisionProjections=impacts,largestLocalProjectionMetres=max_step,
        peakGuideSegmentStrain=peak_length,guidePeakByFrameMetres=[0.,*frame_peaks],
        peakTipMetres=float(np.linalg.norm(output[:,:,-1],axis=2).max()),
        settledTipMetres=float(np.linalg.norm(output[-1,:,-1],axis=1).max()),
        elapsedSeconds=perf_counter()-start)


def baked_mesh(scene,label,offset):
    meshes=bpy.data.meshes
    data=meshes.new(f'R506 {label} guide offsets')
    data.from_pydata(np.zeros((offset.shape[1]*offset.shape[2],3)).tolist(),[],[])
    obj=bpy.data.objects.new(data.name,data)
    scene.collection.objects.link(obj)
    obj.hide_render=True
    obj.hide_set(True)
    obj.shape_key_add(name='Rest offset',from_mix=False)
    for j,values in enumerate(offset[1:],2):
        key=obj.shape_key_add(name=f'Frame {j:02}',from_mix=False)
        key.data.foreach_set('co',values.ravel())
        key.driver_add('value').driver.expression=f'max(0,1-abs(frame-{j}))'
    return obj


def make_fields(obj,indices,weight):
    n,k=positions(obj).shape[:2]
    p=np.arange(k)
    lo=np.clip(np.searchsorted(STATIONS,p,side='right')-1,0,len(STATIONS)-2)
    amount=((p-STATIONS[lo])/(STATIONS[lo+1]-STATIONS[lo])).astype('f4')
    amount[:STATIONS[PINNED-1]+1]=0
    fields={}
    for j in range(3):
        names=(f'{PFX}Guide {j+1}',f'{PFX}Weight {j+1}')
        idx=(indices[:,j,None]*len(STATIONS)+lo).astype('i4')
        wt=np.broadcast_to(weight[:,j,None],(n,k)).astype('f4').copy()
        wt[:,:STATIONS[PINNED-1]+1]=0.
        for name,dtype,values in zip(names,('INT','FLOAT'),(idx,wt)):
            a=obj.data.attributes.new(name,dtype,'POINT')
            a.data.foreach_set('value',values.ravel())
            fields[name]=array_hash(values)
    name=f'{PFX}Span fraction'
    values=np.broadcast_to(amount,(n,k)).copy()
    obj.data.attributes.new(name,'FLOAT','POINT').data.foreach_set('value',values.ravel())
    fields[name]=array_hash(values)
    return fields


def add_modifier(obj,proxies):
    graph=bpy.data.node_groups.new('R506 | Baked guide displacement','GeometryNodeTree')
    graph.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    selector=graph.interface.new_socket(name='Motion model',in_out='INPUT',socket_type='NodeSocketInt')
    selector.default_value=2
    selector.min_value=0
    selector.max_value=2
    graph.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    nodes,links=graph.nodes,graph.links
    def put(node,socket,value):
        if isinstance(value,bpy.types.NodeSocket):
            links.new(value,node.inputs[socket])
        else:
            node.inputs[socket].default_value=value
    def read(name,typ):
        node=nodes.new('GeometryNodeInputNamedAttribute')
        node.data_type=typ
        put(node,'Name',name)
        return node.outputs['Attribute']
    def compare(inp,value):
        node=nodes.new('FunctionNodeCompare')
        node.data_type='INT'
        node.operation='EQUAL'
        links.new(inp,node.inputs['A'])
        node.inputs['B'].default_value=value
        return node.outputs[0]
    def geom(obj_):
        node=nodes.new('GeometryNodeObjectInfo')
        node.transform_space='ORIGINAL'
        put(node,'Object',obj_)
        return node.outputs['Geometry']
    def switch(kind,select,a,b):
        node=nodes.new('GeometryNodeSwitch')
        node.input_type=kind
        put(node,'Switch',select)
        put(node,'False',a)
        put(node,'True',b)
        return node.outputs[0]
    def vec(op,a,b):
        node=nodes.new('ShaderNodeVectorMath')
        node.operation=op
        put(node,0,a)
        put(node,'Scale' if op=='SCALE' else 1,b)
        return node.outputs[0]
    def sample(proxy,idx):
        node=nodes.new('GeometryNodeSampleIndex')
        node.data_type='FLOAT_VECTOR'
        node.domain='POINT'
        put(node,'Geometry',proxy)
        put(node,'Index',idx)
        put(node,'Value',nodes.new('GeometryNodeInputPosition').outputs[0])
        return node.outputs[0]
    entry=nodes.new('NodeGroupInput')
    mode=entry.outputs['Motion model']
    proxy=switch('GEOMETRY',compare(mode,1),geom(proxies['rod']),geom(proxies['spring']))
    frac=read(f'{PFX}Span fraction','FLOAT')
    total=None
    for i in range(1,4):
        idx=read(f'{PFX}Guide {i}','INT')
        add=nodes.new('ShaderNodeMath')
        add.operation='ADD'
        put(add,0,idx)
        put(add,1,1.)
        a=sample(proxy,idx)
        b=sample(proxy,add.outputs[0])
        value=vec('ADD',a,vec('SCALE',vec('SUBTRACT',b,a),frac))
        value=vec('SCALE',value,read(f'{PFX}Weight {i}','FLOAT'))
        total=value if total is None else vec('ADD',total,value)
    total=switch('VECTOR',compare(mode,0),total,(0.,0.,0.))
    node=nodes.new('GeometryNodeSetPosition')
    put(node,'Geometry',entry.outputs['Geometry'])
    put(node,'Offset',total)
    out=nodes.new('NodeGroupOutput')
    put(out,'Geometry',node.outputs[0])
    for i,node_ in enumerate(nodes):
        node_.location=((i//8)*240,-(i%8)*145)
    modifier=obj.modifiers.new(MODIFIER,'NODES')
    modifier.node_group=graph
    getattr(modifier.properties.inputs,selector.identifier).value=2
    obj.update_tag()
    return selector.identifier


def main():
    old=read_json(PARENT/'construction-receipt.json')
    source=Path(old['source']['path'])
    assert digest(source)==old['source']['sha256'] and not DEST.exists()
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    rig,body,gaze=(bpy.data.objects[old[key]] for key in ('rig','body','gaze'))
    hair=bpy.data.objects[old['variants']['layered']['object']]
    rest=positions(hair)
    assert array_hash(rest)==old['variants']['layered']['positionHash']
    assert not hair.modifiers and hair.parent==rig and hair.parent_bone=='Head'
    ids=attribute(hair.data,'AFN409_CURVE_ID')
    assert array_hash(ids)==old['idsHash']
    matrices=get_pose(scene,gaze,hair)
    v,f,_=mesh_data(body)
    v=xform(v,np.asarray(hair.matrix_world.inverted()))
    # The entire measured head/neck surface is retained around the groom.
    near=v[f,2].max(1)>1.265
    bvh=tree(v,f[near])
    g,nearest,weights,pool=make_groups(rest)
    guide=rest[g][:,STATIONS].astype('f8')
    fps=scene.render.fps/scene.render.fps_base
    offsets={}
    receipts={}
    proxies={}
    for mode in MODES:
        offsets[mode],receipts[mode]=solve(guide,matrices,bvh,fps,mode)
        proxies[mode]=baked_mesh(scene,mode,offsets[mode])
        print('R506_SOLVE',mode,receipts[mode]['peakTipMetres'],receipts[mode]['settledTipMetres'],
              receipts[mode]['guideCollisionProjections'],flush=True)
    hair.name='R506 native guide-motion hair'
    fields=make_fields(hair,nearest,weights)
    socket=add_modifier(hair,proxies)
    r500['activate'](scene,gaze,'separated',0.,1.)
    bpy.context.view_layer.update()
    actual=positions(hair.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    assert np.array_equal(actual,rest)
    scene.frame_start,scene.frame_end=1,37
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True)
    np.savez_compressed(ROOT/'guide-bake.npz',guideRows=g,curveIDs=ids[g],stations=STATIONS,
        nearestGuideRows=nearest,weights=weights,pool=pool,matrices=np.array([np.asarray(m) for m in matrices]),
        spring=offsets['spring'],rod=offsets['rod'])
    write_json(ROOT/'construction-receipt.json',dict(source=dict(path=str(DEST),sha256=digest(DEST),bytes=DEST.stat().st_size),
        parent=old['source'],workingRollback=old['fullWorkingRollback'],body=body.name,gaze=gaze.name,rig=rig.name,scalp=old['scalp'],
        hair=hair.name,modifier=MODIFIER,modeSocket=socket,default=2,motionFps=fps,
        controlPositionHash=array_hash(rest),rootHash=array_hash(rest[:,0]),radiusHash=old['radiusHash'],idsHash=old['idsHash'],
        follicleCount=len(rest),pointCount=int(rest.shape[0]*rest.shape[1]),fields=fields,
        proxies={key:obj.name for key,obj in proxies.items()},guideCounts=np.bincount(pool[g]).tolist(),
        motions=receipts,bank=dict(path=str(ROOT/'guide-bake.npz'),sha256=digest(ROOT/'guide-bake.npz')),
        originalBodyBasisHash=old['sourceBasisHash'],originalCheekHash=old['sourceCheekHash'],
        scope='Offline deterministic guide bake from the measured head animation. Rod collision projects guide knots against the measured neutral head/neck in the head frame. Full-strand and actual posed-mesh checks are separate.'))
    print('R506_SAVED',str(DEST),flush=True)


if __name__=='__main__':
    main()

