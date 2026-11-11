"""Reconstruct a graded side-to-nape release on the actual r504 woman."""
from pathlib import Path
from runpy import run_path

import bpy
import numpy as np
from mathutils import Matrix

ROOT=Path(__file__).resolve().parent
survey=run_path(str(ROOT/'probe-r0505.py'))
base=survey['base']
r500=survey['r500']
read_json,write_json,digest,positions,attribute=(survey[k] for k in ('read_json','write_json','digest','positions','attribute'))
set_positions,array_hash,smooth=(base[k] for k in ('set_positions','array_hash','smooth'))
SOURCE_ROUND=survey['PREVIOUS']
DEST=ROOT/'female-next-r0505-ear-nape-bridge-UNACCEPTED.blend'
MODES=('graded','layered')
TIP_Y=np.array([.005,.014,.024,.033,.044,.055])
TIP_HEIGHT=np.array([1.389,1.386,1.380,1.378,1.376,1.373])


def bind_head(obj,rig):
    # Calibrate against the actual bone-parent matrix at the neutral frame.
    target=obj.matrix_world.copy()
    obj.parent=rig
    obj.parent_type='BONE'
    obj.parent_bone='Head'
    obj.matrix_parent_inverse=Matrix.Identity(4)
    obj.matrix_basis=Matrix.Identity(4)
    obj.update_tag()
    bpy.context.view_layer.update()
    parent=obj.matrix_world.copy()
    obj.matrix_parent_inverse=parent.inverted()@target
    obj.update_tag()
    bpy.context.view_layer.update()
    assert np.max(np.abs(np.asarray(obj.matrix_world)-np.asarray(target)))<3e-7
    return parent


def cubic_path(start,tangent,stations):
    bank=np.concatenate((start[:,None],stations),axis=1)
    edges=np.diff(bank,axis=1)
    length=np.linalg.norm(edges,axis=2)
    units=base['normalized'](edges)
    slope=np.empty_like(bank)
    slope[:,0]=tangent*(.83*length[:,0])[:,None]
    for j in range(1,bank.shape[1]-1):
        along=base['normalized'](units[:,j-1]+units[:,j])
        slope[:,j]=along*(.90*np.minimum(length[:,j-1],length[:,j]))[:,None]
    slope[:,-1]=edges[:,-1]*.83
    u=np.linspace(0,1,26)[None,:,None]
    pieces=[]
    for j in range(bank.shape[1]-1):
        curves=base['hermite'](bank[:,j,None],bank[:,j+1,None],u,slope[:,j,None],slope[:,j+1,None])
        pieces.append(curves if j==0 else curves[:,1:])
    return np.concatenate(pieces,axis=1)


def length_profile(y):
    return np.interp(y,TIP_Y,TIP_HEIGHT)


def join_stats(bank,side,group,height):
    sample,step=survey['crossing'](bank,height)
    report=[]
    for sign in (-1,1):
        for low in (.014,.024,.034,.044):
            valid=(side==sign)&(step>=0)&(group>=0)&(sample[:,1]>=low)&(sample[:,1]<low+.010)
            if valid.any():
                report.append(dict(side=sign,yBinStartMm=low*1000.,strands=int(valid.sum()),
                    medianTipHeightMm=float(np.median(bank[valid,-1,2])*1000.)))
    return report


def generate(prior,ids,temple,rear,ears,mode):
    side=np.where(prior[:,0,0]<0.,-1,1)
    rand=((ids.astype('u8')*np.uint64(2654435761))&np.uint64(0xffffffff))/4294967296.
    weights=np.zeros(len(prior),'f4')
    start_idx=np.full(len(prior),-1,'i4')
    family=np.full(len(prior),-1,'i4')
    out=prior.copy()
    witnesses=[]
    for sign,ear in zip((-1,1),ears):
        height=(ear['top']+ear['bottom'])*.5
        ear_cross,ear_idx=survey['crossing'](prior,height)
        _,exit_index=survey['crossing'](prior,ear['top']+.014)
        lower,lower_index=survey['crossing'](prior,ear['bottom']-.012)
        y=ear_cross[:,1]
        bridge=smooth((y+.000)/.021)*smooth((.056-y)/.023)
        above=np.maximum(prior[:,-1,2]-length_profile(y),0.)
        bridge*=smooth(above/.009)
        # Lower rooted strands become an independent underlayer. Higher
        # follicle routes keep the visible temple wave and overlap it above.
        low_layer=1.-smooth((prior[:,0,2]-1.508)/.037)
        ear_side=np.clip((y-(ear['front']-.008))/.013,0.,1.)
        ear_side*=smooth(((ear['back']+.016)-y)/.017)
        ear_side*=smooth((sign*ear_cross[:,0]-(ear['outer']-.006))/.016)
        if mode=='layered':
            bridge=np.maximum(bridge,.74*ear_side*low_layer)
        eligible=(side==sign)&(temple>=0)&(rear<0)&(ear_idx>=0)&(exit_index>=6)&(exit_index<58)&(lower_index>=0)&(bridge>.002)
        rows=np.flatnonzero(eligible)
        start=exit_index[rows]
        assert len(rows)>400
        current=prior[rows].astype('f8')
        y0=y[rows]
        influence=bridge[rows]
        close=ear_side[rows]
        under=low_layer[rows]
        u=np.arange(len(rows))
        before=current[u,start]
        tangent=base['normalized'](current[u,start+1]-current[u,start-1])
        tips=current[:,-1].copy()
        target_z=np.minimum(tips[:,2],length_profile(y0)+.0035*(rand[rows]-.5))
        behind=.004+.004*smooth((y0-.014)/.023)
        lane=.004*(rand[rows]-.5)
        if mode=='layered':
            target_z-=.0037*under*smooth((y0-.002)/.026)
            behind+=.012*close*under
            lane+=.004*(.45-under)
        tips[:,2]=target_z
        tips[:,1]+=behind*.68+lane
        tips[:,0]+=sign*(.0015+.0028*(.5-under))
        # Above the lobe preserve the measured volume, then turn into a
        # longer route with a genuine spatial bend and its own endpoint.
        pinna=ear_cross[rows].astype('f8')
        pinna[:,0]=sign*np.maximum(sign*pinna[:,0]+.0015,ear['outer']+.0065)
        pinna[:,1]+=behind*(.70 if mode=='layered' else .35)
        pinna[:,2]=height-.001
        release=lower[rows].astype('f8')
        release[:,1]+=behind+lane*.65
        release[:,0]+=sign*(.0018+(2.7e-3*(.5-under) if mode=='layered' else 0.))
        release[:,2]=np.maximum(tips[:,2]+.014,release[:,2]-.0025)
        path=cubic_path(before,tangent,np.stack((pinna,release,tips),axis=1))
        for i,row in enumerate(rows):
            n=len(current[i])-start[i]
            q=path[i]
            distance=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))]
            target=np.linspace(0.,distance[-1],n)
            shape=np.column_stack([np.interp(target,distance,q[:,j]) for j in range(3)])
            # Feather adjacent root groups without moving any protected roots.
            weight=influence[i]
            gate=smooth(np.linspace(0.,1.,n)/.21)
            tail=current[i,start[i]:]
            out[row,start[i]:]=(tail+(weight*gate[:,None])*(shape-tail)).astype('f4')
        weights[rows]=influence.astype('f4')
        start_idx[rows]=start
        family[rows]=(sign>0)*2+(under>.52)
        chosen=np.argsort(abs(y0-.029))[:10]
        for i in chosen[::2]:
            witnesses.append(dict(curveID=int(ids[rows[i]]),row=int(rows[i]),side=int(sign),
                controls=np.stack((before[i],pinna[i],release[i],tips[i])).tolist()))
    active=np.flatnonzero(weights>0.)
    # Keep the upper release, baseline front and original posterior curves.
    bound=np.arange(prior.shape[1])[None,:] <= start_idx[:,None]
    assert np.array_equal(out[bound],prior[bound])
    assert np.array_equal(out[rear>=0],prior[rear>=0])
    assert np.array_equal(out[weights==0],prior[weights==0]) and np.array_equal(out[:,0],prior[:,0])
    assert np.isfinite(out).all()
    report=dict(editedCurves=len(active),lengthenedTips=int(np.count_nonzero(out[:,-1,2]<prior[:,-1,2]-1e-6)),
        largestTipLoweringMm=float(np.max(prior[:,-1,2]-out[:,-1,2])*1000.),
        joinProfile=join_stats(out,side,temple,(ears[0]['top']+ears[0]['bottom'])/2),
        nativeRouteWitnesses=witnesses)
    return out,weights,start_idx,family,report


def guide(scene,mode,paths):
    data=bpy.data.curves.new(f'R505 measured pinna routes | {mode}','CURVE')
    data.dimensions='3D'
    for spec in paths:
        points=spec['controls']
        s=data.splines.new('POLY')
        s.points.add(len(points)-1)
        for p,co in zip(s.points,points):
            p.co=(*co,1.)
    obj=bpy.data.objects.new(data.name,data)
    scene.collection.objects.link(obj)
    obj.hide_render=True
    obj.hide_set(True)
    return obj.name


def main():
    old=read_json(SOURCE_ROUND/'construction-receipt.json')
    p=Path(old['source']['path'])
    measured=read_json(ROOT/'ear-join-probe.json')
    assert old['source']==measured['source'] and digest(p)==old['source']['sha256'] and not DEST.exists()
    bpy.ops.wm.open_mainfile(filepath=str(p),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    scalp=bpy.data.objects[old['scalp']]
    body,gaze,rig=(bpy.data.objects[name] for name in (old['body'],old['gaze'],measured['rig']))
    source=bpy.data.objects[old['variants']['returned']['object']]
    r500['activate'](scene,gaze,'separated',0.,1.)
    hair=positions(source)
    assert array_hash(hair)==old['variants']['returned']['positionHash']
    ids=attribute(source.data,'AFN409_CURVE_ID')
    rear=attribute(source.data,'AEVRYND_REAR_BLEND_GROUP')
    temple=attribute(source.data,'AEVRYND_R504_TEMPLE_GROUP')
    radii=attribute(source.data,'radius').reshape(hair.shape[:2])
    assert array_hash(radii)==old['radiusHash']
    assert array_hash(ids)==old['idsHash']
    variants={}
    for mode in MODES:
        bank,weights,start,family,info=generate(hair,ids,temple,rear,measured['ears'],mode)
        obj=source.copy()
        obj.data=source.data.copy()
        obj.name=f'R505 full hair | {mode}'
        obj.data.name=f'R505 pinna-nape transition | {mode}'
        scene.collection.objects.link(obj)
        set_positions(obj,bank)
        for name,kind,arr in (('AEVRYND_R505_BRIDGE_WEIGHT','FLOAT',weights),
                              ('AEVRYND_R505_BRIDGE_START','INT',start),('AEVRYND_R505_BRIDGE_LAYER','INT',family)):
            obj.data.attributes.new(name,kind,'CURVE').data.foreach_set('value',arr)
        guide_name=guide(scene,mode,info['nativeRouteWitnesses'])
        obj['Aevrynd_R505_Route_Reference']=guide_name
        matrix=bind_head(obj,rig)
        variants[mode]=dict(object=obj.name,guide=guide_name,positionHash=array_hash(bank),
            rootHash=array_hash(bank[:,0]),weightHash=array_hash(weights),startHash=array_hash(start),familyHash=array_hash(family),
            neutralBoneParentMatrix=[list(row) for row in matrix],**info)
        print('R505_GROOM',mode,info['editedCurves'],info['lengthenedTips'],info['largestTipLoweringMm'],flush=True)
    carrier=bpy.data.objects[variants['layered']['object']]
    for obj in scene.objects:
        if obj.type=='CURVES':
            obj.hide_set(obj!=carrier)
            obj.hide_render=obj!=carrier
    bpy.ops.object.select_all(action='DESELECT')
    carrier.select_set(True)
    bpy.context.view_layer.objects.active=carrier
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True)
    _,_,error=base['old']['foundation']['binding_frame'](source,scalp,hair[:,0])
    write_json(ROOT/'construction-receipt.json',dict(source=dict(path=str(DEST),sha256=digest(DEST),bytes=DEST.stat().st_size),
        parent=old['source'],fullWorkingRollback=old['parent'],body=body.name,gaze=gaze.name,rig=rig.name,scalp=scalp.name,
        controlObject=source.name,controlPositionHash=array_hash(hair),defaultVisible='layered',strands=len(hair),pointsPerStrand=hair.shape[1],
        radiusHash=array_hash(radii),idsHash=array_hash(ids),rootHash=array_hash(hair[:,0]),originalPosteriorCount=int((rear>=0).sum()),
        sourceBasisHash=old['sourceBasisHash'],sourceCheekHash=old['sourceCheekHash'],
        neutralFollicleFixtureErrorMetres=error,
        baselineJoinProfile=join_stats(hair,np.where(hair[:,0,0]<0.,-1,1),temple,(measured['ears'][0]['top']+measured['ears'][0]['bottom'])/2),
        variants=variants))


if __name__=='__main__':
    main()

