"""Reconstruct continuous native temple shafts with constrained cubic splines."""
from pathlib import Path
from runpy import run_path
from time import perf_counter
import bpy
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
PREVIOUS=ROOT.parent/'r0509-scalp-flow'
past=run_path(str(PREVIOUS/'author-r0509.py'))
read_json,write_json,digest,positions,attribute,array_hash,r500,set_positions=(
    past[k] for k in ('read_json','write_json','digest','positions','attribute','array_hash','r500','set_positions'))
guide_object=past['previous']['guide_object']
basis=past['previous']['basis']
smooth,unit,contact=(past[k] for k in ('smooth','unit','contact'))
MODES=('continuous','layered')
PREFIX='AEVRYND_R510_'
PIN=4
N_CONTROL=20
DEGREE=3
DEST=ROOT/'female-next-r0510-temple-continuity-UNACCEPTED.blend'


def open_source():
    old=read_json(PREVIOUS/'construction-receipt.json')
    source=Path(old['source']['path'])
    assert digest(source)==old['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    control,body,gaze,rig=(bpy.data.objects[old[k]] for k in ('controlObject','body','gaze','rig'))
    previous=bpy.data.objects[old['variants']['layered_tuck']['object']]
    r500['activate'](scene,gaze,'separated',0.,1.)
    base,scaffold=positions(control),positions(previous)
    assert array_hash(base)==old['controlPositionHash']
    assert array_hash(scaffold)==old['variants']['layered_tuck']['positionHash']
    return old,scene,control,previous,body,gaze,rig,base,scaffold


def spline_matrix():
    """Open uniform clamped cubic basis, including its exact end points."""
    breaks=np.linspace(0.,1.,N_CONTROL-DEGREE+1)
    knot=np.r_[np.zeros(DEGREE),breaks,np.ones(DEGREE)]
    t=np.linspace(0.,1.,81-PIN)
    b=((t[:,None]>=knot[:-1])&(t[:,None]<knot[1:])).astype('f8')
    for degree in range(1,DEGREE+1):
        n=b.shape[1]-1
        h0=knot[degree:degree+n]-knot[:n]
        h1=knot[degree+1:degree+1+n]-knot[1:1+n]
        left=np.divide(t[:,None]-knot[:n],h0,out=np.zeros((len(t),n)),where=h0>0.)
        right=np.divide(knot[degree+1:degree+1+n]-t[:,None],h1,out=np.zeros((len(t),n)),where=h1>0.)
        b=left*b[:,:n]+right*b[:,1:]
    b[-1,-1]=1.
    assert b.shape==(81-PIN,N_CONTROL) and np.allclose(b.sum(1),1.)
    return b


def baseline_at_height(reference,height):
    """Evaluate each previous descending lock at comparable physical heights."""
    result=np.empty((*height.shape,2),'f8')
    for i,source in enumerate(reference):
        j=int(source[:,2].argmax())
        path=source[j:]
        if len(path)<2:
            path=source
        z=path[:,2]
        order=np.argsort(z,kind='stable')
        for axis in (0,1):
            result[i,:,axis]=np.interp(height[i],z[order],path[order,axis])
    return result


def shape_support(seed,base,side,layer,route,ids,mode):
    target=seed[:,PIN-1:].astype('f8').copy()
    x,y,z=np.moveaxis(target,-1,0)
    ax=abs(x)
    # Lift develops on the lateral scalp before release, and dissipates into
    # the free lock. The upper roof and original part receive zero target lift.
    lateral=smooth((ax-.052)/.022)*(1-smooth((ax-.086)/.021))
    cap=1-smooth((z-1.534)/.022)
    band=smooth((z-1.471)/.028)*(1-smooth((z-1.526)/.033))*lateral*cap
    lower=layer.astype('f8')[:,None]
    lane=route.astype('f8')[:,None]
    signed=side[:,None]
    phase=(((ids.astype('u8')*np.uint64(2654435761))&np.uint64(0xffffffff)).astype('f8')/4294967296.)[:,None]
    target[:,:,0]+=signed*band*(.0024+.0007*np.cos(lane*1.34))
    target[:,:,1]+=band*(.0031*np.sin(lane*.91+.45)+.0012*(2*lower-1))
    free=smooth((1.519-z)/.047)*smooth((ax-.066)/.024)
    tip=smooth((1.428-z)/.051)
    target[:,:,1]+=free*(.0048*np.sin(lane*1.4+signed*.6)+.0035*(phase-.5))
    target[:,:,2]+=tip*(.0055*np.cos(lane*1.22+.65*lower)+.0028*(phase-.5))
    if mode=='layered':
        # The original anatomical side envelope supplies a spatial boundary
        # in the forehead-to-ear band. The spline carries new paths through
        # it, with underlayer and upper layer following different releases.
        old=baseline_at_height(base,z)
        spatial=(.46+.19*lower)*smooth((1.55-z)/.031)*smooth((z-1.466)/.040)*lateral
        delta=np.clip(old-target[:,:,:2],-.020,.020)
        target[:,:,:2]+=spatial[:,:,None]*delta
        offset=(.0038+.0014*np.sin(lane*1.03))*(1.-.49*lower)
        target[:,:,1]+=free*offset*(signed*.64+.36)
        target[:,:,0]-=free*signed*(.0027+.0009*lower)*(1-.57*tip)
        target[:,:,2]+=tip*(.0070*lower-.0050*(1.-lower))*np.sin(lane*1.14+.86)
    return target


def coefficients(b,target,original,mode):
    fixed=(0,1,N_CONTROL-1)
    free=np.arange(2,N_CONTROL-1)
    d2=np.diff(np.eye(N_CONTROL),n=2,axis=0)
    weight=np.ones(len(b))
    weight[:8]=2.8
    weight[8:20]=1.65
    weight[-13:]=1.20
    regularization=.42 if mode=='continuous' else .52
    m=b[:,free]
    h=m.T@(m*weight[:,None])+regularization*(d2[:,free].T@d2[:,free])
    coeff=np.empty((len(target),N_CONTROL,3),'f8')
    start=original[:,PIN-1]
    tangent=unit(start-original[:,PIN-2])
    length=np.linalg.norm(np.diff(target,axis=1),axis=2).sum(1)
    coeff[:,0]=start
    coeff[:,1]=start+tangent*(length/(DEGREE*(N_CONTROL-DEGREE)))[:,None]
    coeff[:,-1]=target[:,-1]
    const=coeff[:,fixed]
    goal=target-np.einsum('pi,nij->npj',b[:,fixed],const)
    rhs=np.einsum('pq,npj->nqj',m*weight[:,None],goal)
    rhs-=regularization*np.einsum('qi,nij->nqj',d2[:,free].T@d2[:,fixed],const)
    coeff[:,free]=np.linalg.solve(h,rhs)
    gain=np.linalg.solve(h,m.T).T
    leverage=np.einsum('ij,ij->i',m,gain)
    return coeff,free,gain,leverage


def contact_bounds(tree,b,coef,free,gain,leverage,radius):
    """Constrain close local samples in coefficient space; preserve all roots."""
    adjusted=0
    largest=0.
    exceeded=set()
    for _ in range(2):
        curves=np.einsum('pi,nij->npj',b,coef)
        # Each iteration makes at most one bounded correction per shaft.
        for i,curve in enumerate(curves):
            nearest=None
            strongest=0.
            for j in range(2,len(curve)-1):
                x=curve[j]
                if x[2]<1.425 or x[2]>1.588 or abs(x[0])>.103:
                    continue
                p=Vector(x)
                hit,n,_,distance=tree.find_nearest(p,.0021)
                if hit is None:
                    continue
                signed=distance if (p-hit).dot(n)>=0 else -distance
                need=float(radius[i,j]+.00016-signed)
                if need>strongest:
                    nearest=(j,np.asarray(n))
                    strongest=need
            if nearest is None:
                continue
            j,n=nearest
            if strongest>.0014 or leverage[j]<.018:
                exceeded.add(i)
                continue
            coef[i,free]+=gain[j,:,None]*n[None,:]*(strongest/leverage[j])
            adjusted+=1
            largest=max(largest,strongest)
    return dict(localConstraintsApplied=adjusted,largestLocalConstraintMetres=largest,
                curvesBeyondConstraintLimit=len(exceeded))


def generate(base,seed,layer,owner,side,ids,radius,tree,mode):
    active=layer>=0
    original=base[active].astype('f8')
    target=shape_support(seed[active],original,side[active],layer[active],owner[active],ids[active],mode)
    b=spline_matrix()
    coef,free,gain,leverage=coefficients(b,target,original,mode)
    details=contact_bounds(tree,b,coef,free,gain,leverage,radius[active,PIN-1:])
    bank=base.copy()
    bank[active,PIN:]=np.einsum('pi,nij->npj',b[1:],coef).astype('f4')
    assert np.isfinite(bank).all() and np.array_equal(bank[:,:PIN],base[:,:PIN])
    assert np.array_equal(np.any(bank!=base,axis=(1,2)),active)
    return bank,details


def main():
    assert not DEST.exists()
    now=perf_counter()
    old,scene,control,previous,body,gaze,rig,base,seed=open_source()
    ids=attribute(control.data,'AFN409_CURVE_ID')
    radius=attribute(control.data,'radius').reshape(base.shape[:2])
    assert array_hash(ids)==old['idsHash'] and array_hash(radius)==old['radiusHash']
    layer,owner,side,weight=(attribute(previous.data,'AEVRYND_R509_'+key)
                            for key in ('LAYER','ROUTE','SIDE','INFLUENCE'))
    rear=attribute(control.data,'AEVRYND_R507_LAYER')>=0
    bridge=attribute(control.data,'AEVRYND_R505_BRIDGE_WEIGHT')>0
    assert not np.any((layer>=0)&(rear|bridge))
    mesh,faces,_=contact['mesh_data'](body)
    mesh=contact['xform'](mesh,np.asarray(control.matrix_world.inverted()))
    tree=contact['tree'](mesh,faces)
    variants,guide_bank={},{}
    active=layer>=0
    for mode in MODES:
        bank,details=generate(base,seed,layer,owner,side,ids,radius,tree,mode)
        assert np.array_equal(bank[rear|bridge],base[rear|bridge])
        obj=control.copy()
        obj.data=control.data.copy()
        obj.name=f'R510 complete hair | {mode}'
        obj.data.name=obj.name
        scene.collection.objects.link(obj)
        set_positions(obj,bank)
        guides={}
        for sign in (-1,1):
            for j in range(5):
                rows=np.flatnonzero((side==sign)&(owner==j)&(layer==0))
                mid=np.median(bank[rows],axis=0)
                k=rows[int(np.linalg.norm(bank[rows,::8]-mid[::8],axis=(1,2)).argmin())]
                path=bank[k].astype('f8')
                frame=basis(path)
                guides[sign,j]=(path,path,frame,frame,None)
        guide=guide_object(scene,control,guides,mode)
        guide.name=f'R510 temple routes | {mode}'
        guide.data.name=guide.name
        obj['Aevrynd_guide_reference']=guide.name
        guide_bank[mode]=np.array([x[1] for x in guides.values()])
        for name,typ,values in (('LAYER','INT',layer),('ROUTE','INT',owner),('SIDE','INT',side),('INFLUENCE','FLOAT',weight)):
            obj.data.attributes.new(PREFIX+name,typ,'CURVE').data.foreach_set('value',values)
        d=np.linalg.norm(bank[active]-base[active],axis=2)*1000.
        variants[mode]=dict(object=obj.name,guide=guide.name,positionHash=array_hash(bank),
            layerHash=array_hash(layer),routeHash=array_hash(owner),sideHash=array_hash(side),influenceHash=array_hash(weight),
            changedStrands=int(active.sum()),protectedRearCount=int(rear.sum()),protectedBridgeCount=int(bridge.sum()),
            guideCount=len(guides),medianTipShiftMm=float(np.median(d[:,-1])),
            maximumPointShiftMm=float(d.max()),**details)
        print('R510_LAYOUT',mode,variants[mode],flush=True)
    for obj in list(scene.objects):
        if obj.type=='CURVES' and obj not in (control,previous) and obj.name not in {v['object'] for v in variants.values()}:
            assert obj.hide_render
            data=obj.data
            bpy.data.objects.remove(obj,do_unlink=True)
            if not data.users:
                bpy.data.hair_curves.remove(data)
    visible=bpy.data.objects[variants[MODES[-1]]['object']]
    for obj in scene.objects:
        if obj.type=='CURVES':
            obj.hide_render=obj!=visible
            obj.hide_set(obj!=visible)
    bpy.ops.object.select_all(action='DESELECT')
    visible.select_set(True)
    bpy.context.view_layer.objects.active=visible
    scene.render.threads_mode='FIXED'
    scene.render.threads=4
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True)
    sidecar=ROOT/'continuous-temple-routes.npz'
    np.savez_compressed(sidecar,**guide_bank,curveIDs=ids,route=owner,layer=layer,side=side)
    write_json(ROOT/'construction-receipt.json',dict(source=dict(path=str(DEST),sha256=digest(DEST),bytes=DEST.stat().st_size),
        parent=old['source'],comparisonSource=old['parent'],workingRollback=old['workingRollback'],
        body=body.name,gaze=gaze.name,rig=rig.name,scalp=old['scalp'],
        controlObject=control.name,controlPositionHash=array_hash(base),
        previousObject=previous.name,previousPositionHash=array_hash(seed),
        idsHash=old['idsHash'],radiusHash=old['radiusHash'],rootHash=old['rootHash'],
        sourceBasisHash=old['sourceBasisHash'],sourceCheekHash=old['sourceCheekHash'],
        defaultVisible=MODES[-1],variants=variants,strands=len(base),pointsPerStrand=80,pinnedControls=PIN,
        splineDegree=DEGREE,splineControls=N_CONTROL,elapsedSeconds=perf_counter()-now,
        guideBank=dict(path=str(sidecar),sha256=digest(sidecar)),rights='Original Aevrynd continuous temple path construction on r0509 research and r0507 source. Inherited licenses apply.'))
    print('R510_SAVED',str(DEST),flush=True)


if __name__=='__main__':
    main()

