"""Measure which source shafts span the side-to-nape length step."""
from pathlib import Path
from runpy import run_path

import bpy
import numpy as np

ROOT=Path(__file__).resolve().parent
PREVIOUS=ROOT.parent/'r0504-temple-locks'
base=run_path(str(PREVIOUS/'author-r0504.py'))
r500=run_path(str(base['BASELINE']/'author-r0500.py'))
read_json,write_json,digest,positions,attribute=(base[k] for k in ('read_json','write_json','digest','positions','attribute'))


def crossing(bank,height):
    z=bank[:,:,2]
    crossed=(z[:,:-1]>=height)&(z[:,1:]<height)
    index=np.where(crossed,np.arange(z.shape[1]-1),-1).max(axis=1)
    j=np.maximum(index,0)
    i=np.arange(len(bank))
    x,y=bank[i,j],bank[i,j+1]
    u=np.clip((x[:,2]-height)/np.maximum(x[:,2]-y[:,2],1e-9),0.,1.)
    return x+(y-x)*u[:,None],index


def main():
    prior=read_json(PREVIOUS/'construction-receipt.json')
    source=Path(prior['source']['path'])
    assert digest(source)==prior['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    body,gaze,skin=(bpy.data.objects[prior[k]] for k in ('body','gaze','scalp'))
    control=bpy.data.objects[prior['controlObject']]
    groom=bpy.data.objects[prior['variants']['returned']['object']]
    bank=positions(groom)
    previous=positions(control)
    root=bank[:,0]
    old_group=attribute(groom.data,'AEVRYND_R504_TEMPLE_GROUP')
    old_rear=attribute(groom.data,'AEVRYND_REAR_BLEND_GROUP')
    rig=next(m.object for m in body.modifiers if m.type=='ARMATURE' and 'Head' in m.object.pose.bones)
    heads={}
    for frame in (1.,12.,20.,32.,36.75,37.):
        r500['activate'](scene,gaze,'separated',0.,frame)
        H=rig.matrix_world@rig.pose.bones['Head'].matrix
        heads[str(frame)]=[list(row) for row in H]
    r500['activate'](scene,gaze,'separated',0.,1.)
    ears=base['old']['measure_ears'](skin)
    survey=[]
    for sign,ear in zip((-1,1),ears):
        midpoint=(ear['top']+ear['bottom'])/2
        current,ci=crossing(bank,midpoint)
        archived,_=crossing(previous,midpoint)
        for y in np.arange(-.046,.057,.010):
            match=(root[:,0]*sign>0)&(ci>=0)&(current[:,1]>=y)&(current[:,1]<y+.010)&(sign*current[:,0]>.058)
            a=match&(old_group>=0)
            b=match&(old_rear>=0)
            if not np.any(match):
                continue
            def stats(mask):
                if not mask.any():
                    return None
                delta=bank[mask,-1,2]-previous[mask,-1,2]
                return dict(count=int(mask.sum()),tipZMm=np.round(np.percentile(bank[mask,-1,2],[10,50,90])*1000.,3).tolist(),
                    tipChangeZMm=np.round(np.percentile(delta,[10,50,90])*1000.,3).tolist(),
                    earPlaneXyMm=(np.median(current[mask,:2],axis=0)*1000.).tolist(),
                    originalEarPlaneXyMm=(np.median(archived[mask,:2],axis=0)*1000.).tolist())
            survey.append(dict(side=sign,yLimitsMm=[y*1000.,(y+.010)*1000.],sideGroup=stats(a),rearGroup=stats(b)))
    note=dict(source=prior['source'],body=body.name,scalp=skin.name,rig=rig.name,headBone='Head',
        visible=groom.name,sourceHairMatrix=[list(row) for row in groom.matrix_world],
        sourceHairParent=groom.parent.name if groom.parent else None,
        sourceHairConstraints=[x.type for x in groom.constraints],
        heads=heads,ears=ears,tipSurvey=survey)
    write_json(ROOT/'ear-join-probe.json',note)
    print('R505_EAR_JOIN',rig.name,groom.name,len(survey),ears,flush=True)


if __name__=='__main__':
    main()

