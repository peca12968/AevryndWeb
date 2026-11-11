"""Read the verified active r0507 woman's frontal and temporal trajectories."""
from pathlib import Path
from runpy import run_path
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parent
PARENT=ROOT.parent/'r0507-crown-overlap'
prior=run_path(str(PARENT/'preview-r0507.py'))
r505=run_path(str(ROOT.parent/'r0505-ear-nape-bridge'/'contact-r0505.py'))
read_json,write_json,digest,positions,attribute,array_hash,r500,set_positions=(
    prior[k] for k in ('read_json','write_json','digest','positions','attribute','array_hash','r500','set_positions'))
old=read_json(PARENT/'construction-receipt.json')
modes=('side_sweep','over_under')


def open_baseline():
    source=Path(old['source']['path'])
    assert digest(source)==old['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    skin,gaze,rig=(bpy.data.objects[old[key]] for key in ('body','gaze','rig'))
    r500['activate'](scene,gaze,'separated',0.,1.)
    hair=bpy.data.objects[old['variants'][old['defaultVisible']]['object']]
    base=positions(hair)
    assert array_hash(base)==old['variants'][old['defaultVisible']]['positionHash']
    assert hair.parent==rig and hair.parent_bone=='Head' and not hair.modifiers
    return scene,skin,gaze,rig,hair,base


def distribution(a):
    return np.round(np.percentile(a,[10,50,90],axis=0)*1000.,2).tolist()


def main():
    scene,skin,gaze,rig,hair,base=open_baseline()
    root=base[:,0]
    side=np.sign(base[:,20,0])
    previous=attribute(hair.data,'AEVRYND_R504_TEMPLE_GROUP')
    rear=attribute(hair.data,'AEVRYND_R507_LAYER')>=0
    bridge=attribute(hair.data,'AEVRYND_R505_BRIDGE_WEIGHT')>0
    rows=[]
    keys=[0,5,10,17,25,34,44,54,65,79]
    for hemi in (-1,1):
        for u in (-.10,-.078,-.055,-.032,-.010,.011):
            mask=(side==hemi)&(root[:,1]>=u)&(root[:,1]<u+.022)&(previous>=0)&~rear
            for label,group in [('upper',root[:,2]>=1.537),('lower',root[:,2]<1.537)]:
                keep=mask&group
                if keep.any():
                    v=base[keep]
                    rows.append(dict(side=hemi,rootBandMm=u*1000.,tier=label,curves=len(v),
                        protectedBridge=int((keep&bridge).sum()),path={str(k):distribution(v[:,k]) for k in keys}))
    ears=prior['author']['probe']['prior']['base']['old']['measure_ears'](bpy.data.objects[old['scalp']])
    stats=dict(source=old['source'],sourcePositionHash=array_hash(base),groom=hair.name,profileRows=rows,
               existingTempleCount=int((previous>=0).sum()),rearCount=int(rear.sum()),
               bridgeCount=int(bridge.sum()),pinnae=ears)
    write_json(ROOT/'frontal-probe.json',stats)
    print('R508_PROBE',len(base),len(rows),stats['existingTempleCount'],flush=True)


if __name__=='__main__':
    main()

