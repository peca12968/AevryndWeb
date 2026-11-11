"""Locate where rebuilt return triangles cross the cornea between their vertices."""
from pathlib import Path
from runpy import run_path

import bpy
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
fixture=run_path(str(ROOT/'contact-r0502.py'))
model,stage=(fixture[k] for k in ('model','stage'))
read_json,write_json,digest=(fixture[k] for k in ('read_json','write_json','digest'))
mesh_data,tree=(fixture[k] for k in ('mesh_data','tree'))


def signed(point,bvh):
    point=Vector(point)
    near,normal,_,d=bvh.find_nearest(point)
    return float(d if (point-near).dot(normal)>=0 else -d)


def cuts(x,vertices,faces):
    xyz=vertices[faces]
    xs=xyz[:,:,0]
    segments=[]
    for tri in xyz[(xs.min(1)<x)&(xs.max(1)>x)]:
        endpoints=[]
        for i in range(3):
            a,b=tri[i],tri[(i+1)%3]
            if (a[0]<x)==(b[0]<x):
                continue
            p=a+(b-a)*((x-a[0])/(b[0]-a[0]))
            endpoints.append(p[1:].tolist())
        if len(endpoints)==2:
            segments.append(endpoints)
    return segments


def main():
    proof=read_json(ROOT/'construction-receipt.json')
    contact=read_json(ROOT/'contact-receipt.json')
    assert contact['source']==proof['source']
    scene,skin,gaze,layers=fixture['open_model'](proof['source'],proof)
    receipt={}
    selected_pose=contact['poses']['1:0']
    for mode in model['MODES']:
        model['activate'](scene,gaze,mode,0.,1.)
        v,f,p=mesh_data(skin)
        cv,cf,cp=mesh_data(layers['cornea'])
        bvh=tree(cv,cf)
        row=selected_pose[mode]
        assert row['skinHash']==stage['array_hash'](v.astype('f4'))
        by_wall={}
        for witness in row['layer']['cornea']['witnesses']:
            a,b=witness['actual']
            by_wall.setdefault(a,set()).add(b)
        grades=[]
        for a,bs in by_wall.items():
            for tri in f[p==a]:
                axyz=v[tri]
                grades.append((signed(axyz.mean(0),bvh),a,tri,bs))
        grades.sort(key=lambda x:x[0])
        worst=None
        for gap,a,tri,bs in grades:
            if gap>=0.:
                break
            axyz=v[tri]
            for b in sorted(bs):
                for bc in cf[cp==b]:
                    bxyz=cv[bc]
                    _,projection=stage['best_axis'](axyz,bxyz)
                    if projection>=-1.e-8:
                        continue
                    worst=dict(wallFace=a,corneaFace=b,wallTriangleVertices=tri.tolist(),
                        corneaTriangleVertices=bc.tolist(),vertexSignedMetres=[signed(pt,bvh) for pt in axyz],
                        faceCentreSignedMetres=gap,axisProjectionMetres=projection,
                        positionMetres=axyz.mean(0).tolist())
                    break
                if worst is not None:
                    break
            if worst is not None:
                break
        assert worst is not None,mode
        x=worst['positionMetres'][0]
        owner=model['array'](skin.data.attributes[model['FACE_SOURCE']].data,'value',dtype='i4')
        receipt[mode]=dict(witness=worst,sectionXMetres=x,
            rebuiltReturn=cuts(x,v,f[owner[p]==-1]),cornea=cuts(x,cv,cf))
        print('R502_FINITE',mode,worst,flush=True)
    scene,skin,gaze,layers=fixture['open_model'](proof['parent'],proof)
    stage['activate'](scene,gaze,'separated',0.,1.)
    v,f,p=mesh_data(skin)
    face_material=read_json(ROOT/'return-topology.json')['faceMaterials']
    walls=np.array([int(i) for i,mat in face_material.items() if mat==0])
    for mode,item in receipt.items():
        x=item['sectionXMetres']
        item['baselineReturn']=cuts(x,v,f[np.isin(p,walls)])
    binding=fixture['probe']['probe']['anchors']()
    lv,lf,lp=mesh_data(layers['lashes'])
    assert np.array_equal(lf,binding['faces'])
    roots=fixture['probe']['probe']['rim_sites'](v,binding)
    flags=np.zeros(len(v),dtype=bool)
    for side in np.unique(binding['side']):
        r=roots[binding['side']==side]
        low=r.min(0)-[.0075,.008,.009]
        high=r.max(0)+[.0075,.012,.012]
        flags|=np.all((v>=low)&(v<=high),axis=1)
    subset=np.flatnonzero(flags[f].any(1))
    skin_tree=tree(v,f[subset])
    lash_tree=tree(lv,lf)
    left={(int(subset[a]),int(b)) for a,b in skin_tree.overlap(lash_tree)}
    right={(int(subset[a]),int(b)) for b,a in lash_tree.overlap(skin_tree)}
    shaft=lambda pairs:{(a,b) for a,b in pairs if binding['segment'][b]>0}
    oriented=shaft(left)
    reversed_=shaft(right)
    verified=[]
    for a,b in sorted(oriented|reversed_):
        _,margin=stage['best_axis'](v[f[a]],lv[lf[b]])
        if margin < -1.e-8:
            verified.append(dict(skinTriangle=a,lashTriangle=b,
                site=int(binding['siteID'][binding['owner'][b]]),segment=int(binding['segment'][b]),
                skinToLash=(a,b) in oriented,lashToSkin=(a,b) in reversed_,
                axisProjectionMetres=margin,positionMetres=(.5*(v[f[a]].mean(0)+lv[lf[b]].mean(0))).tolist()))
    audit=dict(pose='1:0',sameSpatialScopeAsR501=True,skinToLashShaftPairs=len(oriented),
        lashToSkinShaftPairs=len(reversed_),orderCommonShaftPairs=len(oriented&reversed_),
        strictSATWitnessCount=len(verified),firstWitnesses=verified[:12])
    print('R502_LASH_AUDIT',audit,flush=True)
    write_json(ROOT/'finite-face-witness.json',dict(source=proof['source'],parent=proof['parent'],
        pose='1:0',results=receipt,lashOrderAudit=audit,definition='Exact cross section of native Blender triangles. Point signs use closest cornea triangles. Triangle-pair separation additionally checked with separating axes.'))


if __name__=='__main__':
    main()

