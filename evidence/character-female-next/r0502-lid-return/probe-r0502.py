"""Identify the connected return strips, attachment surface and source topology."""
from collections import Counter
from pathlib import Path
from runpy import run_path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
PREVIOUS = ROOT.parent / 'r0501-lid-rim'
probe = run_path(str(PREVIOUS / 'probe-r0501.py'))
stage = probe['stage']
read_json, write_json, digest = (probe[name] for name in ('read_json','write_json','digest'))
mesh_data, tree = (probe[name] for name in ('mesh_data','tree'))
WITNESS = (186365, 186477, 186717, 186766, 186945)


def main():
    parent = read_json(probe['PARENT']/'construction-receipt.json')
    path = Path(parent['source']['path'])
    assert digest(path)==parent['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    skin,gaze=(bpy.data.objects[parent[name]] for name in ('body','gaze'))
    mesh=skin.data
    binding=probe['anchors']()
    keys=[(1.,p) for p in (0.,.5,.75,.875,1.)]+[(36.75,1.),(37.,.875),(37.,1.)]
    positions={}
    data={}
    for index,(frame,amount) in enumerate(keys):
        stage['activate'](scene,gaze,'separated',amount,frame)
        v,f,fp=mesh_data(skin)
        positions[index]=(v,f,fp)
        for label,name in zip(('eye','cornea'),stage['previous']['LAYERS']):
            v0,f0,_=mesh_data(bpy.data.objects[name])
            data[f'{index}/{label}']=v0
            data[f'{index}/{label}Faces']=f0
    v,f,fp=positions[0]
    roots=probe['rim_sites'](v,binding)
    mask=np.zeros(len(v),dtype=bool)
    for sign in (-1,1):
        r=roots[binding['side']==sign]
        lo=r.min(0)-[.009,.012,.013]
        hi=r.max(0)+[.009,.017,.014]
        mask|=((v>=lo)&(v<=hi)).all(1)
    roi=set(np.flatnonzero(mask[f].any(1)).tolist())
    face_ids=sorted(set(fp[list(roi)].tolist())|set(WITNESS))
    rings={i:list(mesh.polygons[i].vertices) for i in face_ids}
    ref=np.unique([v for ring in rings.values() for v in ring])
    report=dict(parent=parent['source'], materials=[m.name if m else None for m in mesh.materials],
        vertexCount=len(mesh.vertices), sourcePolygons=len(mesh.polygons), poseKeys=keys,
        rings=rings,faceMaterials={str(i):mesh.polygons[i].material_index for i in face_ids},
        radiusBoundsBySide={str(i):[roots[binding['side']==i].min(0).tolist(),roots[binding['side']==i].max(0).tolist()] for i in (-1,1)},
        witnesses={str(i):dict(ring=rings[i], material=mesh.polygons[i].material_index, neutral=v[rings[i]].tolist(),
            at075=positions[2][0][rings[i]].tolist(),closed=positions[4][0][rings[i]].tolist()) for i in WITNESS})
    data.update(binding)
    data['ids']=ref
    data['matrix']=np.asarray(skin.matrix_world)
    for index,(v,f,fp) in positions.items():
        m=np.isin(fp,face_ids)
        data[f'{index}/skin']=v[ref]
        data[f'{index}/face']=f[m]
        data[f'{index}/polygon']=fp[m]
    write_json(ROOT/'return-topology.json',report)
    np.savez_compressed(ROOT/'return-topology.npz',**data)
    print('R502_TOPOLOGY',len(ref),len(face_ids),Counter(report['faceMaterials'].values()),report['materials'],flush=True)


if __name__=='__main__':
    main()

