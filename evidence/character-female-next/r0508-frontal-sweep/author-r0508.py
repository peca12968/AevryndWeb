"""Author an asymmetric frontal sweep and overlapping temporal routes in native Blender Curves."""
from pathlib import Path
from runpy import run_path
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parent
probe=run_path(str(ROOT/'probe-r0508.py'))
read_json,write_json,digest,positions,attribute,array_hash,r500,set_positions,old,MODES=(
    probe[k] for k in ('read_json','write_json','digest','positions','attribute','array_hash','r500','set_positions','old','modes'))
prev=probe['prior']['author']
smooth,cubic_axis,basis=(prev[k] for k in ('smooth','cubic_axis','basis'))
STATIONS=prev['STATIONS']
DEST=ROOT/'female-next-r0508-frontal-sweep-UNACCEPTED.blend'
PREFIX='AEVRYND_R508_'
LANES=np.array([-.093,-.074,-.054,-.034,-.009])
# Each original lane is reauthored using (upper fore/aft, crown rise,
# lateral shoulder, ear fore/aft, hem lateral, hem fore/aft, hem rise) in mm.
# The heavy left front and softer right return use independent paths.
PATHS={
 -1:np.array([
     [-12,11,0,-14,-5,3,13],
     [-9,9,2,-12,-6,10,-11],
     [-6,8,-5,-4,-6,9,14],
     [1,5,-5,5,-4,7,19],
     [1,2,-2,2,-1,2,7],
 ]),
  1:np.array([
     [-2,5,-6,13,-9,15,17],
     [-1,7,-6,11,-8,15,23],
     [-3,5,-4,6,-7,11,13],
     [-1,4,-5,5,-4,7,16],
     [0,2,-2,2,-1,2,6],
 ]),
}


def locate(base,temple,rear,bridge):
    roots=base[:,0]
    side=np.where(base[:,20,0]<0,-1,1)
    coordinate=roots[:,1]+.15*(roots[:,2]-1.537)
    available=(temple>=0)&~rear&~bridge&(roots[:,1]<.014)
    strength=available*(1.-smooth((roots[:,1]+.030)/.044))
    strength*=.62+.38*smooth((roots[:,2]-1.478)/.056)
    distances=abs(coordinate[:,None]-LANES[None])
    strength[strength<.0005]=0.
    owner=np.where(strength>0,distances.argmin(1),-1).astype('i4')
    lower=np.clip(np.searchsorted(LANES,coordinate,side='right')-1,0,len(LANES)-2)
    blend=smooth((coordinate-LANES[lower])/(LANES[lower+1]-LANES[lower]))
    return roots,side,coordinate,strength,owner,lower,blend


def course(values,side,j,mode):
    cy,rise,shoulder,ear,tx,ty,tz=values*.001
    guide=np.array([
        [0.,0.,0.],
        [0.,-.0008,.0005],
        [-.10*shoulder,.48*min(cy,0.),.72*rise],
        [.16*shoulder,.86*cy,rise],
        [.57*shoulder,.68*cy+.23*ear,.64*rise],
        [shoulder,ear,.24*rise+.14*tz],
        [.64*shoulder+.36*tx,.69*ear+.33*ty,.29*tz],
        [.23*shoulder+.78*tx,.30*ear+.72*ty,.69*tz],
        [tx,ty,tz],
    ])
    if mode=='over_under':
        # A long forelock passes above a shorter companion on the heavy side.
        # The opposite side releases earlier beside the ear.
        top=np.array([0.,0.,.26,.59,1.,.88,.54,.22,0.])
        hem=np.array([0.,0.,0.,0.,.09,.24,.52,.82,1.])
        guide[:,1]+=top*((-.007 if side<0 else .003)*np.cos(.81*j+.25))
        guide[:,2]+=top*(.0038*np.sin(.88*j+.65))
        if side<0:
            guide[:,2]+=hem*np.array([-.003,.016,-.005,.008,0.])[j]
            guide[:,0]+=hem*np.array([-.002,.002,-.002,-.001,0.])[j]
        else:
            guide[:,2]+=hem*np.array([.012,-.007,.009,.005,0.])[j]
            guide[:,1]+=hem*np.array([.002,-.004,.006,.002,0.])[j]
    guide[:,0]*=side
    return guide


def axes(base,side,owner,mode):
    result={}
    for sign in (-1,1):
        for j,profile in enumerate(PATHS[sign]):
            rows=np.flatnonzero((side==sign)&(owner==j))
            assert len(rows)>40,(sign,j,len(rows))
            support=np.median(base[rows][:,STATIONS],axis=0).astype('f8')
            first=cubic_axis(support)
            new=cubic_axis(support+course(profile,sign,j,mode))
            result[sign,j]=(first,new,basis(first),basis(new))
    return result


def shape(strand,roots,ids,guide,sign,lane,mode):
    old_path,path,old_basis,new_basis=guide
    u=np.arange(80)/79.
    along=smooth((u-.22)/.48)
    tail=smooth((u-.59)/.41)
    root_phase=(ids.astype('u8')*np.uint64(2654435761)&np.uint64(0xffffffff)).astype('f8')/4294967296.
    upper=smooth((roots[:,2]-1.523)/.029)
    residual=np.einsum('npi,pij->npj',strand-old_path,old_basis)
    residual[:,:,0]*=(1.-(.13 if mode=='side_sweep' else .23)*along+.10*tail)
    residual[:,:,1]*=(1.-.12*along)
    shifted=path+np.einsum('npj,pij->npi',residual,new_basis)
    # Upper strands overlap the lower return, while the lower shafts support
    # the contour past the ear. Neither cohort loses roots or render density.
    if mode=='over_under':
        end=((.009 if sign>0 else .007)*(upper-.36)+.003*np.sin(lane*1.44))
        shifted[:,:,2]+=end[:,None]*tail
        shifted[:,:,1]+=(.0048*(1.-upper))[:,None]*tail
    shifted[:,:,2]+=(root_phase[:,None]-.50)*.0036*tail
    return shifted


def generate(base,ids,temple,rear,bridge,mode):
    roots,side,coordinate,weight,owner,lower,blend=locate(base,temple,rear,bridge)
    guides=axes(base,side,owner,mode)
    output=base.copy()
    ramp=smooth((np.arange(80)-5.)/19.)
    for sign in (-1,1):
        for j in range(len(LANES)-1):
            rows=np.flatnonzero((side==sign)&(lower==j)&(weight>0))
            if not len(rows):
                continue
            q=base[rows].astype('f8')
            first=shape(q,roots[rows],ids[rows],guides[sign,j],sign,j,mode)
            second=shape(q,roots[rows],ids[rows],guides[sign,j+1],sign,j+1,mode)
            combined=first+blend[rows,None,None]*(second-first)
            output[rows]=(q+weight[rows,None,None]*ramp[None,:,None]*(combined-q)).astype('f4')
    assert np.isfinite(output).all() and np.array_equal(output[:,:6],base[:,:6])
    assert np.array_equal(output[rear|bridge],base[rear|bridge])
    assert np.array_equal(output[weight==0],base[weight==0])
    layer=np.where(owner<0,-1,np.where(roots[:,2]>=1.537,0,1)).astype('i4')
    return output,guides,layer,owner,side.astype('i4'),weight.astype('f4')


def main():
    assert not DEST.exists()
    scene,skin,gaze,rig,control,base=probe['open_baseline']()
    original=control.name
    for obj in list(scene.objects):
        if obj.type=='CURVES' and obj!=control:
            assert obj.hide_render
            geom=obj.data
            bpy.data.objects.remove(obj,do_unlink=True)
            if not geom.users:
                bpy.data.hair_curves.remove(geom)
    temple=attribute(control.data,'AEVRYND_R504_TEMPLE_GROUP')
    rear=attribute(control.data,'AEVRYND_R507_LAYER')>=0
    bridge=attribute(control.data,'AEVRYND_R505_BRIDGE_WEIGHT')>0.
    ids=attribute(control.data,'AFN409_CURVE_ID')
    assert array_hash(ids)==old['idsHash']
    assert array_hash(attribute(control.data,'radius'))==old['radiusHash']
    layout={}
    guide_banks={}
    for mode in MODES:
        result,guides,layer,owner,side,weight=generate(base,ids,temple,rear,bridge,mode)
        obj=control.copy()
        obj.data=control.data.copy()
        obj.name=f'R508 complete hair | {mode}'
        obj.data.name=obj.name
        scene.collection.objects.link(obj)
        set_positions(obj,result)
        paths=[v[1] for v in guides.values()]
        guide=prev['guide_object'](scene,control,{key:(*value,None) for key,value in guides.items()},mode)
        guide.name=f'R508 frontal centres | {mode}'
        guide.data.name=guide.name
        obj['Aevrynd_guide_reference']=guide.name
        for name,typ,values in (('LAYER','INT',layer),('ROUTE','INT',owner),('SIDE','INT',side),('INFLUENCE','FLOAT',weight)):
            obj.data.attributes.new(PREFIX+name,typ,'CURVE').data.foreach_set('value',values)
        active=np.any(result!=base,axis=(1,2))
        assert np.array_equal(active,weight>0)
        displacement=np.linalg.norm(result[active]-base[active],axis=2)*1000.
        assert active.sum()>5000
        guide_banks[mode]=np.array(paths)
        layout[mode]=dict(object=obj.name,guide=guide.name,positionHash=array_hash(result),guideCount=len(paths),
            layerHash=array_hash(layer),routeHash=array_hash(owner),sideHash=array_hash(side),influenceHash=array_hash(weight),
            changedStrands=int(active.sum()),protectedRearCount=int(rear.sum()),protectedBridgeCount=int(bridge.sum()),
            medianTipShiftMm=float(np.median(displacement[:,-1])),maximumPointShiftMm=float(displacement.max()),
            upperRebuilt=int((layer==0).sum()),earSideRebuilt=int((layer==1).sum()))
        print('R508_LAYOUT',mode,layout[mode],flush=True)
    visible=bpy.data.objects[layout[MODES[-1]]['object']]
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
    bank=ROOT/'frontal-centres.npz'
    np.savez_compressed(bank,**guide_banks,layer=layer,route=owner,side=side,curveIDs=ids,station=STATIONS)
    write_json(ROOT/'construction-receipt.json',dict(source=dict(path=str(DEST),sha256=digest(DEST),bytes=DEST.stat().st_size),
        parent=old['source'],workingRollback=old['workingRollback'],body=skin.name,gaze=gaze.name,rig=rig.name,scalp=old['scalp'],
        controlObject=original,controlPositionHash=array_hash(base),rootHash=old['rootHash'],idsHash=old['idsHash'],
        radiusHash=old['radiusHash'],sourceBasisHash=old['sourceBasisHash'],sourceCheekHash=old['sourceCheekHash'],
        defaultVisible=MODES[-1],variants=layout,strands=len(base),pointsPerStrand=80,pinnedControls=6,
        guideBank=dict(path=str(bank),sha256=digest(bank)),rights='Original Aevrynd frontal construction on native r0507 curves. Inherited r0507 attribution and licenses apply.'))
    print('R508_SAVED',str(DEST),flush=True)


if __name__=='__main__':
    main()

