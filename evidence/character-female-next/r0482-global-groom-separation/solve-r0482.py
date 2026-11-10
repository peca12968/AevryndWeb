from pathlib import Path
from runpy import run_path
from time import perf_counter
import os
import subprocess
import json
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
R480=ROOT.parent/'r0480-lock-clearance-projection'
R481=ROOT.parent/'r0481-motion-conditioned-clearance'
l=run_path(str(ROOT.parent/'r0479-parallel-transport-locks'/'layout-r0479.py'))
p=run_path(str(R480/'project-r0480.py'))
old,groom=l['old'],l['groom']
MASK=np.uint64((1<<21)-1); KEY_MASK=np.uint64((1<<42)-1); FLAG=np.uint64(1<<42)
PRESETS={'A':dict(limitMm=.45,smoothing=.15,lengthStiffness=.23),
         'B':dict(limitMm=.95,smoothing=.045,lengthStiffness=.08)}


def evaluate(folder,q,r,ids,source):
    folder.mkdir()
    for name,array in (('rest.f32',q),('radius.f32',r),('curve-ids.i32',ids)):
        array.tofile(folder/name)
    old.save(folder/'capture-source.json',dict(source=source,variant=folder.name,dimensions=list(q.shape),
        poses=[dict(label='rest',name='rest.f32',sha256=old.file_sha(folder/'rest.f32'))],rigidStopCoordinatesExactlyEqualToRest=False))
    env=os.environ|{'DOTNET_CLI_HOME':str(ROOT),'DOTNET_PROCESSOR_COUNT':'4','DOTNET_SKIP_FIRST_TIME_EXPERIENCE':'1',
        'DOTNET_GENERATE_ASPNET_CERTIFICATE':'false','DOTNET_CLI_TELEMETRY_OPTOUT':'1','TEMP':str(ROOT),'TMP':str(ROOT)}
    with (folder/'solver.log').open('x',encoding='utf8') as f:
        subprocess.run([r'C:\Program Files\dotnet\dotnet.exe',str(ROOT/'contact-auditor/bin/Release/net8.0/HairContact.dll'),str(folder)],
            check=True,env=env,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
    meta=old.read(folder/'self-contact-audit.json')
    assert meta['firstSegment']==0 and meta['syntheticTestsPassed'] and meta['source']==source
    keys=np.fromfile(folder/'rest-contact-keys.u64',dtype='<u8')
    return keys&KEY_MASK,old.read(folder/'rest-result.json')


def skin_planes(tree,q):
    hits=np.empty_like(q); normals=np.empty_like(q)
    for row in range(len(q)):
        for k in range(q.shape[1]):
            hit,n,_,_=tree.find_nearest(Vector(q[row,k]))
            assert hit is not None
            hits[row,k],normals[row,k]=hit,n
        if row and row%5000==0:
            print('R482_SKIN_PLANES',row,flush=True)
    return hits,normals


def project(q,r,keys,reference,settings):
    left=(keys>>np.uint64(21)).astype('i4'); right=(keys&MASK).astype('i4')
    rows=np.column_stack((left//80,left//80,right//80,right//80))
    knots=np.column_stack((left%80,left%80+1,right%80,right%80+1))
    points=q[rows,knots].astype('f8')
    s,t=p['fit']['closest'](*points.transpose(1,0,2))
    bary=np.column_stack((1.-s,s,t-1.,-t))
    delta=np.sum(points*bary[:,:,None],axis=1)
    distance=np.linalg.norm(delta,axis=1)
    direction=delta/np.maximum(distance[:,None],1.e-13)
    close=distance<1.e-7
    if close.any():
        previous=np.sum(reference[rows[close],knots[close]]*bary[close,:,None],axis=1)
        cross=np.cross(points[close,1]-points[close,0],points[close,3]-points[close,2])
        good=np.linalg.norm(cross,axis=1)>1.e-13
        cross=np.where(good[:,None],cross,previous)
        cross*=np.where(np.sum(cross*previous,axis=1)>=0.,1.,-1.)[:,None]
        direction[close]=cross/np.maximum(np.linalg.norm(cross,axis=1,keepdims=True),1.e-13)
    desired=np.sum(abs(bary)*r[rows,knots],axis=1)+.000004
    gradients=bary*(knots!=0)
    size=np.maximum(desired-distance,0.)/np.maximum(np.sum(gradients*gradients,axis=1),.04)
    move=(gradients[:,:,None]*size[:,None,None]*direction[:,None,:]).astype('f4')
    correction=np.zeros_like(q); weight=np.zeros(q.shape[:2],dtype='f4')
    np.add.at(correction,(rows.ravel(),knots.ravel()),move.reshape(-1,3))
    np.add.at(weight,(rows.ravel(),knots.ravel()),(np.linalg.norm(move,axis=2)>1.e-10).ravel())
    correction/=np.sqrt(np.maximum(weight,1.))[:,:,None]
    alpha=settings['smoothing']
    correction[:,1:-1]+=alpha*(correction[:,:-2]+correction[:,2:])
    correction[:,0]=0.
    return p['vector_limit'](correction,.000060)


def length_projection(q,edge,stiffness):
    vector=np.diff(q,axis=1)
    length=np.linalg.norm(vector,axis=2)
    error=vector*((length-edge)/np.maximum(length,1.e-10))[:,:,None]*stiffness
    delta=np.zeros_like(q)
    delta[:,1:]-=.5*error; delta[:,:-1]+=.5*error
    delta[:,1]-=.5*error[:,0]; delta[:,0]=0.
    return delta


def main():
    start=perf_counter()
    original,r,ids,keep,_,_,body,tri=l['p']['raw_data']()
    parent=old.read(R480/'source-receipt.json')
    cfg=old.read(R480/'projection-receipt.json')
    entry=cfg['variants']['B']; path=R480/entry['file']; assert old.file_sha(path)==entry['sha256']
    with np.load(path,allow_pickle=False) as f:
        template,yaw=(f[k] for k in ('position','cap'))
    rootproof=old.read(R481/'root-separation-control.json'); path=R481/rootproof['file']
    assert old.file_sha(path)==rootproof['sha256']
    with np.load(path,allow_pickle=False) as f:
        roots=f['roots'].astype('f4'); original_roots=f['original'].astype('f4'); changed=f['changed']; newface=f['skinTriangle']; newbary=f['barycentric'].astype('f4')
    assert np.array_equal(template[:,0],original_roots)
    binding=old.read(l['R469']/'groom-probe.json')['restAttributes']; path=l['R469']/binding['path']
    assert old.file_sha(path)==binding['sha256']
    with np.load(path,allow_pickle=False) as f:
        faces,weights=f['face'][keep].copy(),f['weights'][keep].copy()
    faces[changed]=newface[changed]; weights[changed]=newbary[changed]
    assert np.isfinite(weights).all() and np.abs(weights.sum(1)-1.).max()<1.e-5
    t=np.arange(80,dtype='f4')/19.
    fade=1.-l['solver']['smooth'](t)
    seeded=(template+(roots-template[:,0])[:,None,:]*fade[None,:,None]).astype('f4')
    seeded[:,0]=roots
    tree=l['solver']['body_tree'](body,tri)
    hits,normals=skin_planes(tree,seeded)
    edge=np.linalg.norm(np.diff(seeded,axis=1),axis=2)
    sphere_gap=np.sum((seeded-hits)*normals,axis=2)-r
    print('R482_INITIAL_SKIN_POINT_MIN_MM',float(sphere_gap[:,1:].min()*1000.),flush=True)
    folder=ROOT/'contacts'; folder.mkdir(exist_ok=True)
    baseline_keys,baseline=evaluate(folder/'r480B',template,r,ids,parent['source'])
    root_keys,root_result=evaluate(folder/'root-patched',seeded,r,ids,parent['source'])
    print('R482_BASELINE',baseline['NearAxis'],baseline['finiteOverlapWitnesses'],flush=True)
    print('R482_ROOT_PATCH',root_result['NearAxis'],root_result['finiteOverlapWitnesses'],flush=True)
    outcomes={}
    for tag,settings in PRESETS.items():
        q=seeded.copy(); constraints=root_keys.copy(); best=None; trials=[]
        for checkpoint in range(1,7):
            for _ in range(7):
                move=project(q,r,constraints,seeded,settings)
                q+=.84*move
                q+=length_projection(q,edge,settings['lengthStiffness'])
                depth=np.sum((q-hits)*normals,axis=2)
                q+=normals*np.maximum(r+.000007-depth,0.)[:,:,None]
                delta=p['vector_limit'](q-seeded,settings['limitMm']*.001)
                q=(seeded+delta).astype('f4'); q[:,0]=roots
            keys,meta=evaluate(folder/f'{tag}{checkpoint}',q,r,ids,parent['source'])
            score=(int(meta['NearAxis']),int(meta['finiteOverlapWitnesses']))
            trials.append(dict(passNumber=checkpoint,nearAxis=score[0],finite=score[1],minSignedMm=meta['MinSignedM']*1000.))
            if best is None or score<best[0]:
                best=score,q.copy(),checkpoint
            constraints=np.union1d(constraints,keys)
            print('R482_GLOBAL',tag,checkpoint,score,flush=True)
        score,q,index=best
        assert np.array_equal(q[:,0],roots) and np.isfinite(q).all()
        file=ROOT/f'global-{tag}.npz'; assert not file.exists()
        np.savez_compressed(file,position=q,radius=r,curveIDs=ids,pointIDs=(ids[:,None]*80+np.arange(80,dtype='i4')[None,:]),
            keep=keep,skinTriangle=faces,barycentric=weights,cap=yaw)
        ratio=np.linalg.norm(np.diff(q,axis=1),axis=2)/np.maximum(edge,1.e-10)
        outcomes[tag]=dict(file=file.name,sha256=old.file_sha(file),selectedPass=index,score=score,settings=settings,
            maxShiftFromSeedMm=float(np.linalg.norm(q-seeded,axis=2).max()*1000.),
            arcLengthRatioP01P50P99=np.quantile(np.linalg.norm(np.diff(q,axis=1),axis=2).sum(1)/edge.sum(1),[.01,.5,.99]).tolist(),
            spanLengthRatioP01P50P99=np.quantile(ratio,[.01,.5,.99]).tolist(),trials=trials)
    old.save(ROOT/'global-receipt.json',dict(parent=parent['source'],rootControl=rootproof,bodySource=l['SOURCE'],
        baseline=baseline,rootPatched=root_result,variants=outcomes,curves=len(q),seconds=perf_counter()-start,
        scope='Global neutral rest reconstruction. Every strand is editable after its fixed scalp root. All hair capsule spans from 0 are audited. Skin planes are local collision guides, with exact mesh verification still required. Motion caps are inherited and unverified for the rebuilt routes.'))


if __name__=='__main__':
    main()