from pathlib import Path
from runpy import run_path
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parent
l=run_path(str(ROOT/'solve-r0482.py'))
old,groom=l['old'],l['groom']
barycentric=run_path(str(l['R481']/'root-control-r0481.py'))['barycentric']


def bind(tree,body,tri,roots,radius):
    faces=np.empty(len(roots),dtype='i4'); weights=np.empty((len(roots),3),dtype='f4'); offset=np.empty((len(roots),3),dtype='f4')
    reconstructed=np.empty_like(roots)
    for i,x in enumerate(roots):
        hit,n,face,_=tree.find_nearest(Vector(x))
        triangle=body[tri[face]].astype('f8')
        w=barycentric(np.asarray(hit),triangle)
        assert w.min()>-2.e-4
        w=np.maximum(w,0.);w/=w.sum()
        faces[i]=face;weights[i]=w.astype('f4')
        anchor=(triangle*weights[i,:,None]).sum(0)
        normal=np.cross(triangle[1]-triangle[0],triangle[2]-triangle[0]);normal/=np.linalg.norm(normal)
        u=triangle[1]-triangle[0];u/=np.linalg.norm(u);v=np.cross(normal,u)
        frame=np.column_stack((u,v,normal))
        offset[i]=(x-anchor)@frame
        reconstructed[i]=(anchor+frame@offset[i]).astype('f4')
    error=np.linalg.norm(reconstructed.astype('f8')-roots.astype('f8'),axis=1)
    assert error.max()<.0000006,(error.max(),int(error.argmax()))
    return faces,weights,offset,dict(maxReconstructedRootErrorMm=float(error.max()*1000.),
        medianRootNormalOffsetMm=float(np.median(offset[:,2])*1000.),minRootSphereScalpGapMm=float(np.min(np.linalg.norm(offset,axis=1)-radius)*1000.))


def main():
    _,radius,ids,_,_,_,body,tri=l['l']['p']['raw_data']()
    tree=l['l']['solver']['body_tree'](body,tri)
    surface=old.read(ROOT/'surface-receipt.json')
    rows={}; reference=None
    for tag,item in surface['variants'].items():
        path=ROOT/item['file'];assert old.file_sha(path)==item['sha256']
        with np.load(path,allow_pickle=False) as f: bank=dict(f)
        roots=bank['position'][:,0]
        if reference is None:
            reference=roots.copy();faces,weights,offset,metrics=bind(tree,body,tri,roots,radius[:,0])
        else:
            assert np.array_equal(roots,reference)
        changed=int((faces!=bank['skinTriangle']).sum())
        bank['skinTriangle']=faces;bank['barycentric']=weights;bank['rootNormalOffset']=offset[:,2];bank['rootLocalOffset']=offset
        file=ROOT/f'bound-{tag}.npz';assert not file.exists();np.savez_compressed(file,**bank)
        rows[tag]=dict(file=file.name,sha256=old.file_sha(file),positionHash=groom.arr_sha(bank['position']),changedTriangleIDs=changed,**metrics)
        print('R482_BOUND_ROOTS',tag,rows[tag],flush=True)
    entry=old.read(l['R480']/'projection-receipt.json')['variants']['B'];path=l['R480']/entry['file'];assert old.file_sha(path)==entry['sha256']
    with np.load(path,allow_pickle=False) as f: roots=f['position'][:,0]
    faces,weights,offset,metrics=bind(tree,body,tri,roots,radius[:,0])
    base=ROOT/'bound-base-roots.npz';np.savez_compressed(base,skinTriangle=faces,barycentric=weights,rootNormalOffset=offset[:,2],rootLocalOffset=offset)
    old.save(ROOT/'binding-receipt.json',dict(variants=rows,controlRootBinding=dict(file=base.name,sha256=old.file_sha(base),**metrics),
        surfaceReceiptSha256=old.file_sha(ROOT/'surface-receipt.json'),skinStamp=[groom.arr_sha(x) for x in (body,tri)],
        schema=dict(triangleAttribute='AFN409_SKIN_TRIANGLE_ID',barycentricAttribute='AFN409_SKIN_BARYCENTRIC',normalOffsetAttribute='AEVRYND_ROOT_NORMAL_OFFSET',localOffsetAttribute='AEVRYND_ROOT_OFFSET_LOCAL',offsetUnits='metres'),
        scope='Every root is remapped to the actual archived skin triangle order. Reconstruction uses the triangle vertices, barycentric weights, orthonormal triangle frame and stored local vector offset. U follows vertex 0 to 1, N is the geometric outward normal, V is N cross U. Hair positions and radii are unchanged.'))


if __name__=='__main__':
    main()
