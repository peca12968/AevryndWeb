"""Author new root-to-tip posterior locks on the r0505 native groom."""
from pathlib import Path
from runpy import run_path
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parent
probe=run_path(str(ROOT/'probe-r0507.py'))
read_json,write_json,digest,positions,attribute,array_hash,r500,old=(
    probe[k] for k in ('read_json','write_json','digest','positions','attribute','array_hash','r500','old'))
set_positions=probe['prior']['set_positions']
DEST=ROOT/'female-next-r0507-crown-overlap-UNACCEPTED.blend'
STATIONS=np.array([0,7,15,24,35,46,57,68,79])
UPPER_EDGES=np.array([-.099,-.050,-.030,-.011,.008,.030,.052,.099])
LOWER_EDGES=np.array([-.099,-.042,-.018,.006,.029,.051,.099])
MODES=('separated','overlapping')
PREFIX='AEVRYND_R507_'

# Millimetres. Each row specifies one different posterior lock centre at its
# shoulder and released end. The top and underlayers interleave spatially.
# Entries are shoulder x, shoulder y, release x, release y, release z.
UPPER=np.array([
    [-6,5, -4,3, 9], [3,10,8,7,26], [-5,7,-11,4,16],
    [-4,10,4,8,29], [6,8,13,6,19], [-2,10,-8,8,23], [6,5,4,3,7],
],dtype='f8')*.001
LOWER=np.array([
    [-3,2,-7,5,-5], [-3,3,6,5,-13], [4,4,-7,8,-8],
    [5,5,5,7,-15], [3,4,8,5,-11], [5,2,6,4,-5],
],dtype='f8')*.001


def smooth(x):
    x=np.clip(x,0.,1.)
    return x*x*(3.-2.*x)


def unit(x):
    return x/np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1e-12)


def cubic_axis(points):
    """Cubic Hermite centreline on the same parameter as the native controls."""
    s=STATIONS.astype('f8')
    u=np.arange(80)
    lo=np.clip(np.searchsorted(s,u,side='right')-1,0,len(s)-2)
    dt=s[lo+1]-s[lo]
    t=((u-s[lo])/dt)[:,None]
    tangent=np.gradient(points,s,axis=0)
    p,q=points[lo],points[lo+1]
    return ((2*t**3-3*t**2+1)*p+(t**3-2*t**2+t)*dt[:,None]*tangent[lo]
        +(-2*t**3+3*t**2)*q+(t**3-t**2)*dt[:,None]*tangent[lo+1])


def basis(axis):
    tangent=unit(np.gradient(axis,axis=0))
    width=np.empty_like(axis)
    seed=np.array([1.,0.,0.])
    width[0]=unit(seed-np.dot(seed,tangent[0])*tangent[0])
    for i in range(1,len(axis)):
        prior=width[i-1]
        width[i]=unit(prior-np.dot(prior,tangent[i])*tangent[i])
    depth=unit(np.cross(width,tangent))
    if depth[45,1]<0:
        depth=-depth
    return np.stack((width,depth,tangent),axis=-1)


def assign(base,rear):
    lateral=.76*base[:,29,0]+.24*base[:,17,0]
    layer=np.where(rear<0,-1,(rear>=9).astype('i4'))
    lanes=np.full(len(base),-1,'i4')
    for tier,edges in enumerate((UPPER_EDGES,LOWER_EDGES)):
        mask=layer==tier
        lanes[mask]=np.clip(np.searchsorted(edges,lateral[mask],side='right')-1,0,len(edges)-2)
    return lateral,layer,lanes


def axis_set(base,layer,lane,mode):
    axes={}
    for tier,template in enumerate((UPPER,LOWER)):
        for j,profile in enumerate(template):
            rows=np.flatnonzero((layer==tier)&(lane==j))
            assert len(rows)>50,(tier,j,len(rows))
            landmarks=np.median(base[rows][:,STATIONS],axis=0).astype('f8')
            dx,dy,tx,ty,tz=profile
            course=np.array([
                [0.,0.,0.],[0.,0.,0.],[.21*dx,.26*dy,.0009 if tier==0 else 0.],
                [.55*dx,.58*dy,.0018 if tier==0 else 0.],
                [dx,dy,.10*tz],
                [.72*dx+.31*tx,.96*dy,.26*tz],
                [.30*dx+.82*tx,.80*dy+.25*ty,.48*tz],
                [1.18*tx,.44*dy+.64*ty,.76*tz],[tx,ty,tz],
            ])
            if mode=='overlapping':
                # The upper locks drape diagonally over offset lower lanes.
                bend=np.array([0.,0.,.12,.37,.68,1.,1.12,.83,.38])
                course[:,0]+=bend*((.0085 if tier==0 else -.0052)*np.cos(1.01*j+.38))
                course[:,1]+=bend*((.0028 if tier==0 else -.0008)*np.sin(1.26*j+.22))
                tip=np.array([0.,0.,0.,0.,.05,.22,.44,.76,1.])
                course[:,2]+=tip*((.008 if tier==0 else -.003)*np.cos(j*1.45+.38))
            original=cubic_axis(landmarks)
            new=cubic_axis(landmarks+course)
            axes[(tier,j)]=(original,new,basis(original),basis(new),landmarks+course)
    return axes


def target(strand,lateral,ids,axis,edges,j,tier,mode):
    old_path,new_path,old_basis,new_basis,_=axis
    u=np.arange(80,dtype='f8')/79
    weight=smooth((u-.09)/.32)
    tip=smooth((u-.51)/.49)
    band_mid=(edges[j]+edges[j+1])*.5
    half=(edges[j+1]-edges[j])*.5
    lane=np.clip((lateral-band_mid)/half,-1.,1.)
    volume=np.sqrt(np.maximum(0.,1.-lane*lane))[:,None]
    residual=np.einsum('npi,pij->npj',strand-old_path,old_basis)
    spread=(.24 if tier==0 else .11) if mode=='separated' else (.14 if tier==0 else .07)
    residual[:,:,0]*=1.-spread*weight+(.12 if mode=='overlapping' else .02)*tip
    residual[:,:,1]*=1.-(.19 if tier==0 else .11)*weight
    depth_profile=(.0015 if tier==1 else .0038)*weight*(.85+.15*np.sin(j*2.3))
    residual[:,:,1]+=(volume-.35)*depth_profile
    # Taper follows the lock's length, while neighbours retain a varied hem.
    phase=((ids.astype('u8')*np.uint64(2654435761))&np.uint64(0xffffffff)).astype('f8')/4294967296
    residual[:,:,2]*=1.-.22*tip
    residual[:,:,2]+=(phase[:,None]-.5)*(.0024 if tier==0 else .0031)*tip
    return new_path+np.einsum('npj,pij->npi',residual,new_basis)


def generate(base,ids,lateral,layer,lane,mode):
    result=base.copy()
    axes=axis_set(base,layer,lane,mode)
    share_all=np.zeros(len(base),'f4')
    near_all=np.full(len(base),-1,'i4')
    u=np.arange(80,dtype='f8')
    connect=smooth((u-7)/20)
    for (tier,j),axis in axes.items():
        rows=np.flatnonzero((layer==tier)&(lane==j))
        strand=base[rows].astype('f8')
        edges=(UPPER_EDGES,LOWER_EDGES)[tier]
        shaped=target(strand,lateral[rows],ids[rows],axis,edges,j,tier,mode)
        if mode=='overlapping':
            edge_width=min(.008,(edges[j+1]-edges[j])*.31)
            for adj,boundary in ((j-1,edges[j]),(j+1,edges[j+1])):
                if (tier,adj) not in axes:
                    continue
                local=np.flatnonzero(np.abs(lateral[rows]-boundary)<edge_width)
                if not len(local):
                    continue
                selected=rows[local]
                share=.5*(1-smooth(np.abs(lateral[selected]-boundary)/edge_width))
                alternate=target(strand[local],lateral[selected],ids[selected],axes[tier,adj],edges,adj,tier,mode)
                shaped[local]+=share[:,None,None]*(alternate-shaped[local])
                share_all[selected]=share
                near_all[selected]=adj
        result[rows]=(strand+(shaped-strand)*connect[None,:,None]).astype('f4')
    assert np.isfinite(result).all() and np.array_equal(result[:,:8],base[:,:8])
    assert np.array_equal(result[layer<0],base[layer<0])
    return result,axes,share_all,near_all


def guide_object(scene,source,axes,mode):
    data=bpy.data.curves.new(f'R507 centres | {mode}','CURVE')
    data.dimensions='3D'
    data.resolution_u=4
    for _,path,_,_,_ in axes.values():
        line=data.splines.new('POLY')
        line.points.add(len(path)-1)
        coords=np.concatenate((path,np.ones((len(path),1))),axis=1).astype('f4')
        line.points.foreach_set('co',coords.ravel())
    obj=bpy.data.objects.new(data.name,data)
    scene.collection.objects.link(obj)
    obj.parent=source.parent
    obj.parent_type=source.parent_type
    obj.parent_bone=source.parent_bone
    obj.matrix_parent_inverse=source.matrix_parent_inverse
    obj.matrix_basis=source.matrix_basis
    obj.hide_render=True
    obj.hide_set(True)
    obj['Aevrynd role']='Construction centrelines for the stored native Curves. Regenerate with author-r0507.py.'
    return obj


def add_field(obj,name,dtype,values):
    attr=obj.data.attributes.new(PREFIX+name,dtype,'CURVE')
    attr.data.foreach_set('value',values)


def main():
    assert not DEST.exists()
    scene,skin,gaze,control,base=probe['open_baseline']()
    ids=attribute(control.data,'AFN409_CURVE_ID')
    radii=attribute(control.data,'radius')
    assert array_hash(ids)==old['idsHash'] and array_hash(radii)==old['radiusHash']
    rear=attribute(control.data,'AEVRYND_REAR_BLEND_GROUP')
    bridge=attribute(control.data,'AEVRYND_R505_BRIDGE_WEIGHT')>0
    assert not ((rear>=0)&bridge).any()
    lateral,layer,lane=assign(base,rear)
    layouts={}
    guide_banks={}
    active=None
    for mode in MODES:
        result,axes,shares,neighbors=generate(base,ids,lateral,layer,lane,mode)
        assert np.array_equal(result[bridge],base[bridge])
        guide=guide_object(scene,control,axes,mode)
        obj=control.copy()
        obj.data=control.data.copy()
        obj.name=f'R507 complete hair | {mode}'
        obj.data.name=obj.name
        scene.collection.objects.link(obj)
        set_positions(obj,result)
        for name,dtype,values in (('LAYER','INT',layer.astype('i4')),('LOCK','INT',lane),('NEIGHBOR','INT',neighbors),
                                 ('OVERLAP','FLOAT',shares)):
            add_field(obj,name,dtype,values)
        obj['Aevrynd_guide_reference']=guide.name
        changed=np.any(base!=result,axis=(1,2))
        delta=np.linalg.norm(result[changed]-base[changed],axis=2)
        length0=np.linalg.norm(np.diff(base[changed],axis=1),axis=2).sum(1)
        length1=np.linalg.norm(np.diff(result[changed],axis=1),axis=2).sum(1)
        guide_banks[mode]=np.array([x[1] for x in axes.values()])
        layouts[mode]=dict(object=obj.name,guide=guide.name,positionHash=array_hash(result),
            layerHash=array_hash(layer.astype('i4')),lockHash=array_hash(lane),neighborHash=array_hash(neighbors),
            overlapHash=array_hash(shares),changedStrands=int(changed.sum()),protectedBridgeStrands=int(bridge.sum()),
            medianTipShiftMm=float(np.median(delta[:,-1])*1000.),maximumPointShiftMm=float(delta.max()*1000.),
            lengthChangeMm=(np.percentile((length1-length0)*1000,[0,10,50,90,100])).tolist(),
            blendedStrands=int((shares>0).sum()),guideCount=len(axes),
            laneCounts={f'{a}:{b}':int(((layer==a)&(lane==b)).sum()) for a,b in axes})
        print('R507_LAYOUT',mode,layouts[mode],flush=True)
        active=obj
    for obj in scene.objects:
        if obj.type=='CURVES':
            obj.hide_render=obj!=active
            obj.hide_set(obj!=active)
    bpy.ops.object.select_all(action='DESELECT')
    active.select_set(True)
    bpy.context.view_layer.objects.active=active
    scene.render.threads_mode='FIXED'
    scene.render.threads=4
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True)
    bank=ROOT/'guide-centres.npz'
    np.savez_compressed(bank,**guide_banks,station=STATIONS,
        layer=layer,lock=lane,lateral=lateral,curveIDs=ids)
    write_json(ROOT/'construction-receipt.json',dict(source=dict(path=str(DEST),sha256=digest(DEST),bytes=DEST.stat().st_size),
        parent=old['source'],workingRollback=old['fullWorkingRollback'],body=skin.name,gaze=gaze.name,
        scalp=old['scalp'],rig=old['rig'],controlObject=control.name,controlPositionHash=array_hash(base),
        rootHash=old['rootHash'],radiusHash=old['radiusHash'],idsHash=old['idsHash'],sourceBasisHash=old['sourceBasisHash'],
        sourceCheekHash=old['sourceCheekHash'],defaultVisible=MODES[-1],strands=len(base),pointsPerStrand=base.shape[1],
        pinnedControls=8,variants=layouts,guideBank=dict(path=str(bank),sha256=digest(bank)),
        rights='Original Aevrynd guide construction on inherited r0505 native curves. Blender manual describes the general guide/child workflow. Inherited r0505 licenses and reference attribution apply.'))
    print('R507_SAVED',str(DEST),flush=True)


if __name__=='__main__':
    main()

