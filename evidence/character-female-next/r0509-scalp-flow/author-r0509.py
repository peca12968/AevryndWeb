"""Construct frontal curves from actual scalp tangents and independent release routes."""
from pathlib import Path
from runpy import run_path
from time import perf_counter
import bpy
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
R508=ROOT.parent/'r0508-frontal-sweep'
probe=run_path(str(R508/'probe-r0508.py'))
past=run_path(str(R508/'author-r0508.py'))
read_json,write_json,digest,positions,attribute,array_hash,r500,set_positions,old=(
    probe[k] for k in ('read_json','write_json','digest','positions','attribute','array_hash','r500','set_positions','old'))
contact=probe['r505']
previous=probe['prior']['author']
smooth=previous['smooth']
DEST=ROOT/'female-next-r0509-scalp-flow-UNACCEPTED.blend'
MODES=('open_sweep','layered_tuck')
PREFIX='AEVRYND_R509_'
LANES=np.array([-.095,-.075,-.054,-.034,-.011])
PIN=4
SCALP_STEPS=22
HEAD_CENTRE=np.array([0.,-.027,1.495])

# Original XYZ rails in head-local millimetres. Left and right have different
# part flows, ear exits, and hem contours. X is given as positive magnitude.
RAILS={
    -1:np.array([
        [[90,-77,1492],[94,-60,1452],[80,-56,1394]],
        [[91,-63,1492],[97,-47,1455],[83,-36,1376]],
        [[91,-46,1491],[93,-31,1450],[81,-22,1392]],
        [[91,-29,1493],[92,-13,1452],[83,-3,1404]],
        [[87,-5,1489],[89,13,1447],[77,24,1390]],
    ],dtype='f8'),
    1:np.array([
        [[86,-68,1493],[91,-51,1455],[80,-42,1400]],
        [[89,-55,1492],[93,-31,1453],[80,-23,1392]],
        [[91,-40,1493],[94,-18,1451],[81,-9,1405]],
        [[91,-24,1494],[92,3,1451],[81,11,1397]],
        [[87,-3,1489],[88,22,1448],[77,31,1388]],
    ],dtype='f8'),
}


def unit(x):
    return x/np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1.e-12)


def blend_rows(values,lower,fraction):
    weight=fraction.reshape((-1,)+(1,)*(values.ndim-1))
    return values[lower]+weight*(values[lower+1]-values[lower])


def scalp_tree(body,carrier):
    vertices,faces,_=contact['mesh_data'](body)
    vertices=contact['xform'](vertices,np.asarray(carrier.matrix_world.inverted()))
    coordinates=vertices[faces]
    high=coordinates[:,:,2].min(axis=1)>1.481
    return contact['tree'](vertices,faces[high]),int(high.sum())


def nearest(tree,coords):
    points=np.empty_like(coords)
    normal=np.empty_like(coords)
    max_gap=0.
    for i,p in enumerate(coords):
        q,n,_,d=tree.find_nearest(Vector(p),.036)
        if q is None:
            raise ValueError(f'Scalp departure point misses supporting skin: {p}')
        points[i]=q
        normal[i]=n
        max_gap=max(max_gap,d)
    outward=np.einsum('ij,ij->i',points-HEAD_CENTRE,normal)>0.
    normal[~outward]*=-1.
    return points,unit(normal),max_gap


def walk(tree,bank,sign,lo,fraction,layer,mode):
    roots=bank[:,0].astype('f8')
    start=bank[:,PIN-1].astype('f8')
    scalp,normal,gap=nearest(tree,start)
    root_tangent=unit(start-bank[:,0])
    travel=np.clip((.072-abs(scalp[:,0]))*1.04+.010,.006,.086)
    travel*=.93+.11*layer
    if mode=='layered_tuck':
        travel*=.93+.16*(1-layer)
    front=1.-smooth((roots[:,1]+.074)/.058)
    desired=blend_rows(np.array([-.25,-.19,-.04,.23,.48]) if sign<0 else
                       np.array([-.04,.12,.28,.46,.55]),lo,fraction)
    if mode=='layered_tuck':
        desired=desired+.16*(sign>0)*(1-.45*front)-.07*(sign<0)*layer
    rise=(.0022+.0020*layer)*(.87+.13*np.cos((lo+fraction)*1.36))
    lifted=np.zeros((len(bank),SCALP_STEPS+1,3),'f8')
    lifted[:,0]=start
    frozen=scalp[:,2]<1.490
    max_query=gap
    for i in range(1,SCALP_STEPS+1):
        t=(i-1)/(SCALP_STEPS-1)
        drop=-.24-.47*smooth((np.abs(scalp[:,0])-.047)/.032)
        field=unit(np.column_stack((np.full(len(scalp),sign),desired*(.68+.32*t),drop)))
        mix=smooth(t/.36)
        field=unit(root_tangent*(1-mix)+field*mix)
        tangent=unit(field-normal*np.einsum('ij,ij->i',field,normal)[:,None])
        candidate=scalp+tangent*(travel/SCALP_STEPS)[:,None]
        next_point,next_normal,distance=nearest(tree,candidate)
        max_query=max(max_query,distance)
        # Lower follicles transition to the free rail when they reach the
        # bottom of the scalp domain.
        frozen|=next_point[:,2]<1.490
        scalp[~frozen]=next_point[~frozen]
        normal[~frozen]=next_normal[~frozen]
        u=i/SCALP_STEPS
        lift=.0010+(rise-.0010)*smooth(u)
        proposed=scalp+normal*lift[:,None]
        attached=smooth(u/.23)
        linear=start+(proposed-start)*attached
        lifted[:,i]=linear
    # Build the exit tangent from the last valid movement. The artist's
    # default tangent supplies a direction if a lower root exits early.
    exit_tangent=unit(lifted[:,-1]-lifted[:,-5])
    default=unit(np.column_stack((np.full(len(bank),sign*.38),desired,np.full(len(bank),-.62))))
    bad=frozen | (np.linalg.norm(exit_tangent,axis=1)<.5)
    exit_tangent[bad]=default[bad]
    return lifted,exit_tangent,max_query


def rails_for(lo,fraction,sign,layer,ids,mode):
    landmarks=blend_rows(RAILS[sign]*.001,lo,fraction)
    local=lo+fraction
    n=2*np.pi*local
    phase=((ids.astype('u8')*np.uint64(2654435761))&np.uint64(0xffffffff)).astype('f8')/4294967296.
    fringe=.0041*np.sin(n+.6)+.0061*(phase-.5)
    landmarks[:,:,1]+=fringe[:,None]*np.array([.18,.49,1.])
    landmarks[:,:,0]+=(.0028*np.cos(n+.45)+.0022*layer)[:,None]*np.array([.35,1.,.53])
    landmarks[:,-1,2]+=.0058*(phase-.5)+.0032*np.sin(1.28*local+.40)
    if mode=='layered_tuck':
        # Positive-side routes travel behind the ear before dropping.
        # The shorter upper exits and the longer underlayer stay distinct.
        stagger=.006*np.cos(1.13*local+.35)+.009*layer
        landmarks[:,-1,2]+=stagger
        landmarks[:,:,1]+=((.0078 if sign>0 else -.0032)*(.4+.6*layer))[:,None]*np.array([.38,1.,.81])
        landmarks[:,:,0]+=(.0016+.0012*layer)[:,None]*np.array([.38,1.,.30])
    landmarks[:,:,0]*=sign
    return landmarks


def cubic_free(start,tangent,stations):
    points=np.concatenate((start[:,None],stations),axis=1)
    chords=np.linalg.norm(np.diff(points,axis=1),axis=2)
    slopes=np.gradient(points,axis=1)
    aim=unit(points[:,1]-points[:,0])
    forward=unit(.46*tangent+.54*aim)
    slopes[:,0]=forward*(chords[:,0]*.71)[:,None]
    slopes[:,-1]*=.74
    t=np.linspace(0.,1.,29)[None,:,None]
    path=[]
    for j in range(3):
        a,b=points[:,j,None],points[:,j+1,None]
        v,w=slopes[:,j,None],slopes[:,j+1,None]
        section=(2*t**3-3*t**2+1)*a+(t**3-2*t**2+t)*v+(-2*t**3+3*t**2)*b+(t**3-t**2)*w
        path.append(section if j==0 else section[:,1:])
    return np.concatenate(path,axis=1)


def resample(path,front):
    length=np.linalg.norm(np.diff(path,axis=1),axis=2)
    arc=np.column_stack((np.zeros(len(path)),np.cumsum(length,axis=1)))
    result=np.empty((len(path),80-PIN,3),'f8')
    t=np.arange(1,81-PIN)/(80-PIN)
    for i,track in enumerate(path):
        target=arc[i,-1]*t
        result[i]=np.stack([np.interp(target,arc[i],track[:,k]) for k in range(3)],axis=-1)
    return np.concatenate((front,result),axis=1),arc[:,-1]


def generate(base,ids,temple,rear,bridge,tree,mode):
    roots,side,coordinate,weight,owner,lower,fraction=past['locate'](base,temple,rear,bridge)
    layer=np.where(owner<0,-1,np.where(roots[:,2]>=1.537,0,1)).astype('i4')
    output=base.copy()
    query=0.
    lengths=[]
    for sign in (-1,1):
        rows=np.flatnonzero((side==sign)&(owner>=0))
        original=base[rows].astype('f8')
        tier=(layer[rows]==0).astype('f8')
        scalp,edge,maximum=walk(tree,original,sign,lower[rows],fraction[rows],tier,mode)
        rails=rails_for(lower[rows],fraction[rows],sign,tier,ids[rows],mode)
        free=cubic_free(scalp[:,-1],edge,rails)
        new,length=resample(np.concatenate((scalp,free[:,1:]),axis=1),original[:,:PIN])
        transition=1-smooth((roots[rows,1]+.040)/.056)
        # Complete new trajectories are used through the frontal core.
        # Only the rear boundary grades into the protected ear-to-nape bank.
        strength=np.where(roots[rows,1]<-.049,1.,np.maximum(.0005,transition))
        result=(original+strength[:,None,None]*(new-original)).astype('f4')
        output[rows]=result
        query=max(query,maximum)
        lengths.extend(length.tolist())
    assert np.isfinite(output).all() and np.array_equal(output[:,:PIN],base[:,:PIN])
    assert np.array_equal(output[rear|bridge],base[rear|bridge])
    assert np.array_equal(np.any(output!=base,axis=(1,2)),owner>=0)
    guides={}
    for sign in (-1,1):
        for j in range(len(LANES)):
            group=np.flatnonzero((side==sign)&(owner==j)&(layer==0))
            if not len(group):
                group=np.flatnonzero((side==sign)&(owner==j))
            median=np.median(output[group],axis=0)
            chosen=group[int(np.linalg.norm(output[group,::8]-median[::8],axis=(1,2)).argmin())]
            sampled=output[chosen].astype('f8')
            frame=previous['basis'](sampled)
            guides[sign,j]=(sampled,sampled,frame,frame,None)
    return output,guides,layer,owner,side.astype('i4'),dict(maxScalpQueryMetres=query,
        newLengthMm=(np.percentile(lengths,[0,10,50,90,100])*1000.).tolist())


def main():
    assert not DEST.exists()
    now=perf_counter()
    scene,body,gaze,rig,control,base=probe['open_baseline']()
    for obj in list(scene.objects):
        if obj.type=='CURVES' and obj!=control:
            assert obj.hide_render
            data=obj.data
            bpy.data.objects.remove(obj,do_unlink=True)
            if not data.users:
                bpy.data.hair_curves.remove(data)
    tree,skin_tris=scalp_tree(body,control)
    ids=attribute(control.data,'AFN409_CURVE_ID')
    radius=attribute(control.data,'radius')
    assert array_hash(ids)==old['idsHash'] and array_hash(radius)==old['radiusHash']
    rear=attribute(control.data,'AEVRYND_R507_LAYER')>=0
    bridge=attribute(control.data,'AEVRYND_R505_BRIDGE_WEIGHT')>0
    temple=attribute(control.data,'AEVRYND_R504_TEMPLE_GROUP')
    layout,bank={},{}
    for mode in MODES:
        result,guides,layer,owner,side,details=generate(base,ids,temple,rear,bridge,tree,mode)
        weight=np.where(owner<0,0.,np.where(base[:,0,1]<-.049,1.,
            np.maximum(.0005,1-smooth((base[:,0,1]+.040)/.056)))).astype('f4')
        active=owner>=0
        assert int(active.sum())==7502
        obj=control.copy()
        obj.data=control.data.copy()
        obj.name=f'R509 complete hair | {mode}'
        obj.data.name=obj.name
        scene.collection.objects.link(obj)
        set_positions(obj,result)
        guide=previous['guide_object'](scene,control,guides,mode)
        guide.name=f'R509 built routes | {mode}'
        guide.data.name=guide.name
        obj['Aevrynd_guide_reference']=guide.name
        for name,dtype,values in (('LAYER','INT',layer),('ROUTE','INT',owner),('SIDE','INT',side),('INFLUENCE','FLOAT',weight)):
            obj.data.attributes.new(PREFIX+name,dtype,'CURVE').data.foreach_set('value',values)
        bank[mode]=np.array([x[1] for x in guides.values()])
        d=np.linalg.norm(result[active]-base[active],axis=2)*1000.
        layout[mode]=dict(object=obj.name,guide=guide.name,positionHash=array_hash(result),
            layerHash=array_hash(layer),routeHash=array_hash(owner),sideHash=array_hash(side),influenceHash=array_hash(weight),
            changedStrands=int(active.sum()),protectedRearCount=int(rear.sum()),protectedBridgeCount=int(bridge.sum()),
            guideCount=len(guides),fullyReauthoredStrands=int((weight==1).sum()),upperRebuilt=int((layer==0).sum()),
            earSideRebuilt=int((layer==1).sum()),medianTipShiftMm=float(np.median(d[:,-1])),
            maximumPointShiftMm=float(d.max()),**details)
        print('R509_LAYOUT',mode,layout[mode],flush=True)
    active_obj=bpy.data.objects[layout[MODES[-1]]['object']]
    for obj in scene.objects:
        if obj.type=='CURVES':
            obj.hide_render=obj!=active_obj
            obj.hide_set(obj!=active_obj)
    bpy.ops.object.select_all(action='DESELECT')
    active_obj.select_set(True)
    bpy.context.view_layer.objects.active=active_obj
    scene.render.threads_mode='FIXED'
    scene.render.threads=4
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True)
    sidecar=ROOT/'scalp-flow-routes.npz'
    np.savez_compressed(sidecar,**bank,curveIDs=ids,route=owner,layer=layer,side=side)
    write_json(ROOT/'construction-receipt.json',dict(source=dict(path=str(DEST),sha256=digest(DEST),bytes=DEST.stat().st_size),
        parent=old['source'],workingRollback=old['workingRollback'],body=body.name,gaze=gaze.name,rig=rig.name,scalp=old['scalp'],
        controlObject=control.name,controlPositionHash=array_hash(base),idsHash=old['idsHash'],radiusHash=old['radiusHash'],
        rootHash=old['rootHash'],sourceBasisHash=old['sourceBasisHash'],sourceCheekHash=old['sourceCheekHash'],
        defaultVisible=MODES[-1],variants=layout,strands=len(base),pointsPerStrand=80,pinnedControls=PIN,
        scalpSurfaceTriangles=skin_tris,scalpIntegrationSteps=SCALP_STEPS,elapsedSeconds=perf_counter()-now,
        guideBank=dict(path=str(sidecar),sha256=digest(sidecar)),rights='Original Aevrynd scalp tangent and release trajectories on inherited native r0507 hair. Inherited licenses and attribution apply.'))
    print('R509_SAVED',str(DEST),flush=True)


if __name__=='__main__':
    main()

