"""Inspect the real follicle domains and a compact set of complete r500 hair paths."""
from pathlib import Path
from runpy import run_path

import bpy
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
BASELINE=ROOT.parent/'r0500-multi-pose-lid'
old=run_path(str(ROOT.parent/'r0497-feathered-rear-locks/author-r0497.py'))
read_json,write_json,digest,positions,attribute=(old[k] for k in ('read_json','write_json','digest','positions','read_attribute'))
SCALP=old['BODY']


def main():
    proof=read_json(BASELINE/'construction-receipt.json')
    path=Path(proof['source']['path'])
    assert digest(path)==proof['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    skin=bpy.data.objects[SCALP]
    hair=bpy.data.objects[proof['hair']['object']]
    base=positions(hair)
    ids=attribute(hair.data,'AFN409_CURVE_ID')
    owner=attribute(hair.data,'AEVRYND_SPATIAL_LOCK_ID')
    rear=attribute(hair.data,'AEVRYND_REAR_BLEND_GROUP')
    normals,tree,error=old['foundation']['binding_frame'](hair,skin,base[:,0])
    root=base[:,0]
    bands=[]
    for side in (-1,1):
        for low,high in zip((-.145,-.090,-.067,-.046,-.025,-.005,.015,.035),(-.090,-.067,-.046,-.025,-.005,.015,.035,.075)):
            use=(root[:,1]>=low)&(root[:,1]<high)&(root[:,0]*side>=0.)
            b=base[use][:,[0,8,16,26,38,52,66,79]]
            if len(b):
                bands.append(dict(side=side,yLimitsMetres=[low,high],count=len(b),
                    rootBoundsMetres=[b[:,0].min(0).tolist(),b[:,0].max(0).tolist()],
                    medianPathMm=np.round(np.median(b,axis=0)*1000,2).tolist(),
                    pathP10Mm=np.round(np.percentile(b,10,axis=0)*1000,2).tolist(),
                    pathP90Mm=np.round(np.percentile(b,90,axis=0)*1000,2).tolist(),
                    oldOwners=np.bincount(owner[use]).tolist(),retainedRear=int(np.count_nonzero(rear[use]>=0))))
    check={}
    origin=Vector((0.,-.031,1.502))
    for phi in (0,25,50,75,100,125,150,180):
        rows=[]
        for elev in (74,56,38,20,3,-15,-33):
            a,b=np.radians((phi,elev))
            d=Vector((np.sin(a)*np.cos(b),-np.cos(a)*np.cos(b),np.sin(b)))
            hit,n,_,_=tree.ray_cast(origin,d,.19)
            rows.append(None if hit is None else (np.array(hit)*1000.).round(2).tolist())
        check[str(phi)]=rows
    write_json(ROOT/'follicle-probe.json',dict(source=proof['source'],sourceHair=hair.name,sourceSkin=skin.name,
        body=proof['body'],hairTransform=[list(row) for row in hair.matrix_world],skinTransform=[list(row) for row in skin.matrix_world],
        bindingMaximumErrorMetres=error,count=len(base),pointsPerCurve=base.shape[1],bands=bands,
        rayOriginMetres=list(origin),positiveSideRayHitsMm=check,
        modifiers=[dict(name=m.name,type=m.type,render=m.show_render,viewport=m.show_viewport) for m in hair.modifiers],
        attributes=[dict(name=a.name,domain=a.domain,type=a.data_type) for a in hair.data.attributes]))
    np.savez_compressed(ROOT/'root-survey.npz',ids=ids,roots=root,normals=normals,owner=owner,rear=rear,
                        oldStations=base[:,[0,8,16,26,38,52,66,79]])
    print('R504_FOLLICLES',len(base),root.min(0).tolist(),root.max(0).tolist(),hair.name,skin.name,flush=True)


if __name__=='__main__':
    main()

