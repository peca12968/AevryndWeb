"""Author full temple locks with scalp-projected upper paths and independent free routes."""
from pathlib import Path
from runpy import run_path

import bpy
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
probe=run_path(str(ROOT/'probe-r0504.py'))
old=probe['old']
BASELINE=probe['BASELINE']
read_json,write_json,digest,positions,attribute=(probe[k] for k in ('read_json','write_json','digest','positions','attribute'))
array_hash,set_positions,smooth=(old[k] for k in ('array_hash','set_positions','smooth'))
DEST=ROOT/'female-next-r0504-temple-locks-UNACCEPTED.blend'
SCALP=probe['SCALP']
MODES=('swept','returned')
ORIGIN=np.array((0.,-.031,1.502))
BANDS=np.array([-105.,-88.,-71.,-54.,-36.,-19.,-2.])
EXIT_ANGLE=np.array([55.,61.,69.,79.,90.,101.,109.])
EXIT_ELEV=np.array([12.,17.,22.,25.,24.,21.,18.])
LIFT_MM=np.array([5.9,7.8,9.7,8.0,9.7,7.8,6.5])
WIDTH_MM=np.array([5.0,6.2,6.0,7.1,6.0,6.6,5.9])

# Editable free-path stations in head-local millimetres, from the upper turn
# toward the tip. Each root cluster gets its own two or three stages.
FREE={
 'swept':[
  [(91,-69,1473),(96,-62,1423),(82,-57,1370)],
  [(93,-52,1471),(99,-41,1428),(86,-42,1385)],
  [(95,-41,1465),(98,-27,1425),(83,-27,1373)],
  [(95,-23,1475),(97,-11,1432),(81,-13,1393)],
  [(96,-5,1466),(98,3,1425),(82,0,1383)],
  [(96,11,1470),(93,18,1431),(78,16,1392)],
  [(90,26,1473),(86,37,1426),(75,31,1378)]],
 'returned':[
  [(94,-65,1476),(102,-56,1445),(88,-54,1412),(80,-65,1374)],
  [(92,-57,1477),(105,-41,1449),(86,-32,1416),(84,-39,1391)],
  [(97,-43,1472),(102,-27,1441),(91,-24,1411),(78,-33,1378)],
  [(93,-29,1480),(101,-14,1445),(87,-1,1418),(82,-13,1395)],
  [(96,-13,1475),(103,6,1442),(88,16,1410),(81,4,1381)],
  [(96,6,1480),(98,25,1447),(84,31,1418),(77,23,1397)],
  [(89,24,1476),(92,43,1445),(82,48,1409),(74,35,1379)]],
}


def normalized(v):
    return v/np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1.e-12)


def spherical_angles(points):
    q=points-ORIGIN
    return np.arctan2(q[:,0],-q[:,1]),np.arctan2(q[:,2],np.linalg.norm(q[:,:2],axis=1))


def guide_map(root,base,rear):
    front_height=smooth((root[:,2]-1.486)/.039)
    # Persistent part direction follows the previously authored departure in
    # the narrow central band. The follicles themselves stay fixed.
    direction=np.sign(root[:,0]-.003)
    part=abs(root[:,0]-.003)<.012
    direction[part]=np.sign(base[part,9,0]-root[part,0])
    direction[direction==0]=1.
    coordinate=root[:,1]*1000.+8.*(1.-front_height)+3.0*direction*smooth((root[:,1]+.084)/.080)
    distances=abs(coordinate[:,None]-BANDS[None,:])
    primary=distances.argmin(1)
    low=np.clip(np.searchsorted(BANDS,coordinate)-1,0,len(BANDS)-2)
    blend=smooth((coordinate-BANDS[low])/(BANDS[low+1]-BANDS[low]))
    span=1-smooth((root[:,1]+.012)/.029)
    span*=.53+.47*front_height
    span=np.where(rear>=0,0.,span)
    span=np.where((root[:,1]>.018)|(root[:,2]<1.469),0.,span)
    lane=np.clip((coordinate-BANDS[primary])/8.8,-1,1)
    return direction,coordinate,primary,low,blend,span,lane


def interpolate(values,low,blend):
    first,last=values[low],values[low+1]
    f=blend.reshape((-1,)+(1,)*(first.ndim-1))
    return first+(last-first)*f


def hermite(a,b,u,d0,d1):
    return ((2*u**3-3*u*u+1)*a+(u**3-2*u*u+u)*d0+
            (-2*u**3+3*u*u)*b+(u**3-u*u)*d1)


def make_surface(tree,root,theta,elev,exit_theta,exit_elev,loft,steps=17):
    u=np.linspace(0.,1.,steps)
    da=exit_theta-theta
    db=exit_elev-elev
    theta_path=theta[:,None]+da[:,None]*(.64*u+.36*smooth(u))
    beta_path=elev[:,None]+db[:,None]*(.39*u+.61*smooth(u))
    direction=np.stack((np.sin(theta_path)*np.cos(beta_path),-np.cos(theta_path)*np.cos(beta_path),
                        np.sin(beta_path)),axis=-1)
    output=np.empty_like(direction)
    misses=0
    origin=Vector(ORIGIN)
    for j in range(steps):
        for i in range(len(root)):
            p,_,_,_=tree.ray_cast(origin,Vector(direction[i,j]),.19)
            if p is None:
                misses+=1
                output[i,j]=root[i] if j==0 else output[i,j-1]
            else:
                output[i,j]=p
    assert misses==0,misses
    # Filter sharp changes along the real scalp while keeping the endpoint.
    for _ in range(2):
        output[:,1:-1]=.17*output[:,:-2]+.66*output[:,1:-1]+.17*output[:,2:]
    true_offset=root-output[:,0]
    outward=.00085*smooth(u/.20)[None,:]+loft[:,None]*(smooth(u)**.81)[None,:]
    output+=direction*outward[:,:,None]+true_offset[:,None,:]*(1-smooth(u/.30))[None,:,None]
    output[:,0]=root
    return output


def build_free(surface,stations,free_count=40):
    bank=np.concatenate((surface[:,-1,None,:],stations),axis=1)
    differences=np.diff(bank,axis=1)
    lengths=np.linalg.norm(differences,axis=2)
    tangent=np.gradient(bank,axis=1)
    # Follow the actual final surface tangent into the loose hair.
    tip_tangent=normalized(surface[:,-1]-surface[:,-3])
    tangent[:,0]=tip_tangent*(lengths[:,0]*.76)[:,None]
    tangent[:,-1]*=.68
    u=np.linspace(0,1,free_count)[None,:,None]
    curves=[]
    for j in range(bank.shape[1]-1):
        seg=hermite(bank[:,j,None],bank[:,j+1,None],u,tangent[:,j,None],tangent[:,j+1,None])
        curves.append(seg if j==0 else seg[:,1:])
    return np.concatenate(curves,axis=1),bank


def resample(path,n=80):
    step=np.linalg.norm(np.diff(path,axis=1),axis=2)
    arc=np.c_[np.zeros(len(path)),np.cumsum(step,axis=1)]
    result=np.empty((len(path),n,3),'f8')
    phase=np.linspace(0.,1.,n)
    for i,row in enumerate(path):
        q=phase*arc[i,-1]
        result[i]=np.column_stack([np.interp(q,arc[i],row[:,k]) for k in range(3)])
    return result,arc[:,-1]


def local_clearance(coords,selected,radii,tree):
    corrected=0
    max_move=0.
    residual=0
    # Small corrections affect the actual penetrating control alone, followed
    # by a partial neighbour interpolation to avoid local kinks in the path.
    for row in selected:
        curve=coords[row]
        delta=np.zeros_like(curve)
        for j in range(1,len(curve)):
            p=Vector(curve[j])
            hit,normal,_,d=tree.find_nearest(p,.0075)
            if hit is None:
                continue
            s=d if (p-hit).dot(normal)>=0 else -d
            gap=s-float(radii[row,j])
            if gap<.00018:
                value=.00020-gap
                if value>.0043:
                    residual+=1
                    continue
                delta[j]=np.asarray(normal)*value
                corrected+=1
                max_move=max(max_move,value)
        delta[1:-1]+=.21*(delta[:-2]+delta[2:])
        curve+=delta.astype(curve.dtype)
    return dict(correctedControls=corrected,maximumLocalMoveMetres=max_move,largeWarningsLeft=residual)


def generate(base,ids,rear,radii,tree,mode):
    root=base[:,0].astype('f8')
    side,coordinate,owner,lo,blend,weight,lane=guide_map(root,base,rear)
    active=np.flatnonzero(weight>0)
    q=root[active]
    sigma=side[active]
    a,b=spherical_angles(q)
    p=lo[active]
    f=blend[active]
    lane0=lane[active]
    cross=np.sin(np.pi*lane0)
    # A close lane remains covered by adjacent roots. Near the crown the
    # part splits using the original side and the scalp stays the sole support.
    an=interpolate(EXIT_ANGLE,p,f)
    e=interpolate(EXIT_ELEV,p,f)
    exit_az=np.radians(an+2.3*cross+1.7*sigma)
    exit_az=np.maximum(abs(a)+np.radians(6.),exit_az)
    exit_az=np.minimum(exit_az,np.radians(124.))
    exit_az*=sigma
    exit_z=np.minimum(np.radians(e),b-np.radians(19.))
    exit_z=np.maximum(exit_z,np.radians(-42.))
    random=((ids[active].astype('u8')*np.uint64(2654435761))&np.uint64(0xffffffff))/4294967296.
    lob=np.cos(lane0*np.pi*.5)**2
    loft=(interpolate(LIFT_MM,p,f)*(1+.28*lob)+3.0*(random-.50))*.001
    if mode=='returned':
        loft+=.0015*(.48+lob)
    surface=make_surface(tree,q,a,b,exit_az,exit_z,loft)
    stations=interpolate(np.asarray(FREE[mode],dtype='f8')*.001,p,f)
    width=interpolate(WIDTH_MM,p,f)*.001
    stations[:,:,0]*=sigma[:,None]
    stations[:,:,0]+=sigma[:,None]*(.0045*lob+.0025*(random-.5))[:,None]
    stations[:,:,1]+=width[:,None]*(.46*cross+.18*np.sin(owner[active]*1.36))[:,None]
    # The left/right directions and tip lengths stagger without changing density.
    tip=(.0078*(random-.50)+.0021*cross+.0046*sigma*np.sin((owner[active]+1)*.96))
    stations[:,-1,2]+=tip
    stations[:,-1,1]+=.004*np.sin((owner[active]+1)*1.08)*sigma
    stations[:,0,2]=np.minimum(stations[:,0,2],surface[:,-1,2]-.017)
    for j in range(1,stations.shape[1]):
        stations[:,j,2]=np.minimum(stations[:,j,2],stations[:,j-1,2]-.016)
    free,guide=build_free(surface,stations)
    shaped,arc=resample(np.concatenate((surface,free[:,1:]),axis=1))
    output=base.copy()
    output[active]=base[active]+weight[active,None,None]*(shaped-base[active])
    info=local_clearance(output,active,radii,tree)
    assert np.isfinite(output).all()
    assert np.array_equal(output[:,0],base[:,0])
    assert np.array_equal(output[rear>=0],base[rear>=0])
    assert np.array_equal(output[weight==0],base[weight==0])
    return output,owner,side,weight,active,guide,arc,info


def create_guides(scene,mode,owner,side,active,stations,bank):
    data=bpy.data.curves.new(f'R504 {mode} measured temple routes','CURVE')
    data.dimensions='3D'
    names=[]
    for sign in (-1,1):
        for label in range(len(BANDS)):
            rows=np.flatnonzero((side[active]==sign)&(owner[active]==label))
            if not len(rows):
                continue
            centroid=np.mean(stations[rows],axis=0)
            reference=stations[rows]
            i=rows[np.linalg.norm(reference-centroid,axis=(1,2)).argmin()]
            full=bank[active[i],::8]
            full=np.vstack([full,bank[active[i],-1]])
            spl=data.splines.new('POLY')
            spl.points.add(len(full)-1)
            for p,xyz in zip(spl.points,full):
                p.co=(*xyz,1.)
            names.append(dict(side=sign,band=label,sourceRow=int(active[i]),stations=stations[i].tolist()))
    obj=bpy.data.objects.new(data.name,data)
    scene.collection.objects.link(obj)
    obj.hide_render=True
    obj.hide_set(True)
    return obj,names


def main():
    parent=read_json(BASELINE/'construction-receipt.json')
    source=Path(parent['source']['path'])
    survey=read_json(ROOT/'follicle-probe.json')
    assert survey['source']==parent['source'] and digest(source)==parent['source']['sha256'] and not DEST.exists()
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    control=bpy.data.objects[parent['hair']['object']]
    scalp=bpy.data.objects[SCALP]
    base=positions(control)
    assert array_hash(base)==parent['hair']['positionHash']
    rear=attribute(control.data,'AEVRYND_REAR_BLEND_GROUP')
    ids=attribute(control.data,'AFN409_CURVE_ID')
    radii=attribute(control.data,'radius').reshape(base.shape[:2])
    _,tree,error=old['foundation']['binding_frame'](control,scalp,base[:,0])
    assert len(np.unique(ids))==len(ids)
    variants={}
    for mode in MODES:
        bank,owner,side,weight,active,stations,arc,info=generate(base,ids,rear,radii,tree,mode)
        obj=control.copy()
        obj.data=control.data.copy()
        obj.name=f'R504 full hair | {mode}'
        obj.data.name=f'R504 native temporal locks | {mode}'
        scene.collection.objects.link(obj)
        set_positions(obj,bank)
        group=owner+np.where(side<0.,0,len(BANDS))
        group=np.where(weight>0.,group,-1).astype('i4')
        for name,kind,values in (
            ('AEVRYND_R504_TEMPLE_GROUP','INT',group),
            ('AEVRYND_R504_TEMPLE_WEIGHT','FLOAT',weight.astype('f4'))):
            obj.data.attributes.new(name,kind,'CURVE').data.foreach_set('value',values)
        guide,guides=create_guides(scene,mode,owner,side,active,stations,bank)
        obj['Aevrynd_R504_Measured_Route_Reference']=guide.name
        variants[mode]=dict(object=obj.name,guide=guide.name,guideWitnesses=guides,
            positionHash=array_hash(bank),groupHash=array_hash(group),weightHash=array_hash(weight.astype('f4')),
            changedStrands=int(np.any(bank!=base,axis=(1,2)).sum()),
            changedTips=int(np.any(bank[:,-1]!=base[:,-1],axis=1).sum()),
            candidatePathLengthMmP10P50P90=(np.percentile(arc,[10,50,90])*1000.).tolist(),
            groupCounts=np.bincount(group+1).tolist(),**info)
        print('R504_GROOM',mode,variants[mode]['changedTips'],variants[mode]['candidatePathLengthMmP10P50P90'],info,flush=True)
    default=bpy.data.objects[variants['returned']['object']]
    for obj in scene.objects:
        if obj.type=='CURVES':
            obj.hide_render=obj!=default
            obj.hide_set(obj!=default)
    bpy.ops.object.select_all(action='DESELECT')
    default.select_set(True)
    bpy.context.view_layer.objects.active=default
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True)
    write_json(ROOT/'construction-receipt.json',dict(source=dict(path=str(DEST),sha256=digest(DEST),bytes=DEST.stat().st_size),
        parent=parent['source'],body=parent['body'],gaze=parent['gaze'],scalp=scalp.name,controlObject=control.name,
        controlPositionHash=array_hash(base),rootHash=array_hash(base[:,0]),idsHash=array_hash(ids),radiusHash=array_hash(radii),
        bindingMaximumErrorMetres=error,rearStrandsExact=int(np.count_nonzero(rear>=0)),pointsPerStrand=80,strands=len(base),
        defaultVisible='returned',variants=variants,sourceBasisHash=parent['basisHash'],sourceCheekHash=parent['cheekCoordinateHash']))


if __name__=='__main__':
    main()

