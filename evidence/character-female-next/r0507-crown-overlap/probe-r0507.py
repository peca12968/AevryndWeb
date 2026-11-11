"""Inspect the actual scalp, root groups and longitudinal shaft landmarks."""
from pathlib import Path
from runpy import run_path
import bpy
import numpy as np
ROOT=Path(__file__).resolve().parent
prior=run_path(str(ROOT.parent/'r0505-ear-nape-bridge'/'author-r0505.py'))
read_json,write_json,digest,positions,attribute,array_hash,r500=(
    prior[k] for k in ('read_json','write_json','digest','positions','attribute','array_hash','r500'))
PARENT=ROOT.parent/'r0505-ear-nape-bridge'
old=read_json(PARENT/'construction-receipt.json')


def open_baseline():
    source=Path(old['source']['path'])
    assert digest(source)==old['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    skin,gaze=(bpy.data.objects[old[k]] for k in ('body','gaze'))
    r500['activate'](scene,gaze,'separated',0.,1.)
    hair=bpy.data.objects[old['variants']['layered']['object']]
    base=positions(hair)
    assert array_hash(base)==old['variants']['layered']['positionHash']
    assert hair.parent.name==old['rig'] and hair.parent_bone=='Head' and not hair.modifiers
    return scene,skin,gaze,hair,base


def quantiles(a):
    return np.round(np.percentile(a,[0,10,50,90,100],axis=0)*1000.,2).tolist()


def main():
    scene,skin,gaze,hair,base=open_baseline()
    row_ids=attribute(hair.data,'AFN409_CURVE_ID')
    fields=sorted((a.name,a.data_type,a.domain) for a in hair.data.attributes)
    rear=attribute(hair.data,'AEVRYND_REAR_BLEND_GROUP')
    side=attribute(hair.data,'AEVRYND_R504_TEMPLE_GROUP')
    bridge=attribute(hair.data,'AEVRYND_R505_BRIDGE_LAYER')
    stations=[0,8,18,29,41,53,65,79]
    profiles={}
    for name,mask in [('all',np.ones(len(base),bool)),('rear',rear>=0),('side',side>=0),
                      ('bridge',bridge>=0),('mid_crown', (base[:,0,2]>1.535)&(base[:,0,1]>.010)),
                      *[(f'rear_{i}',rear==i) for i in sorted(set(rear.tolist())-{-1})]]:
        if mask.any():
            p=base[mask]
            profiles[name]=dict(count=len(p),ranges={str(i):quantiles(p[:,i]) for i in stations},
                lengthMm=quantiles(np.linalg.norm(np.diff(p,axis=1),axis=2).sum(1)))
    report=dict(source=old['source'],hair=hair.name,body=skin.name,scalp=old['scalp'],fields=fields,
        sourcePositionHash=array_hash(base),matrix=[list(row) for row in hair.matrix_world],profiles=profiles,
        rearIdCounts={str(i):int((rear==i).sum()) for i in np.unique(rear)})
    write_json(ROOT/'groom-probe.json',report)
    # Packed snapshots let the author locate original 3D guide paths without repeated full opens.
    np.savez_compressed(ROOT/'baseline-guide-probe.npz',positions=base[:,stations],stations=stations,
        rear=rear,side=side,bridge=bridge,curveIDs=row_ids)
    print('R507_PROBE',len(base),{key:x['count'] for key,x in profiles.items()},flush=True)


if __name__=='__main__':
    main()

