"""Reconstruct complete strands from the same woman's inspected spatial strips."""
from pathlib import Path
from hashlib import file_digest,sha256
import json
import numpy as np
import bpy
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parent
DEST=ROOT/'female-next-r0484-spatial-lock-reconstruction-UNACCEPTED.blend'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return file_digest(f,'sha256').hexdigest()
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1.e-12)

def reconstruct(base,normals):
    data=np.load(ROOT/'original-strip-guides.npz',allow_pickle=False)
    source=data['position'];guides=[]
    for line in source:
        arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(line,axis=0),axis=1))]
        guides.append(np.stack([np.interp(np.linspace(0.,arc[-1],80),arc,line[:,axis]) for axis in range(3)],axis=1))
    guides=np.asarray(guides,dtype='f4')
    # Find an entry on an actual source guide, rather than forcing every follicle to its root.
    prefix=53;kd=KDTree(len(guides)*prefix)
    for i,p in enumerate(guides[:,:prefix].reshape(-1,3)):kd.insert(p,i)
    kd.balance();roots=base[:,0]
    closest=[kd.find(root) for root in roots]
    index=np.array([item[1] for item in closest],dtype='i4')
    owner,start=index//prefix,index%prefix
    phase=np.linspace(0.,1.,80,dtype='f4')[None,:]
    sample=start[:,None]+(79-start[:,None])*phase
    lo=np.minimum(sample.astype('i4'),78);mix=(sample-lo)[:,:,None]
    ref=guides[owner[:,None],lo]*(1.-mix)+guides[owner[:,None],lo+1]*mix
    tangents=unit(np.gradient(ref,axis=1))
    u=np.empty_like(ref);v=np.empty_like(ref)
    initial=np.cross(tangents[:,0],normals)
    degenerate=np.linalg.norm(initial,axis=1)<1.e-5
    initial[degenerate]=np.cross(tangents[degenerate,0],np.array((1.,0.,0.)))
    u[:,0]=unit(initial);v[:,0]=unit(np.cross(tangents[:,0],u[:,0]))
    for k in range(1,80):
        cross=np.cross(tangents[:,k-1],tangents[:,k]);dot=(tangents[:,k-1]*tangents[:,k]).sum(1)
        previous=u[:,k-1]
        rotated=previous+np.cross(cross,previous)+np.cross(cross,np.cross(cross,previous))/np.maximum(1.+dot[:,None],1.e-5)
        u[:,k]=unit(rotated-tangents[:,k]*(rotated*tangents[:,k]).sum(1)[:,None])
        v[:,k]=unit(np.cross(tangents[:,k],u[:,k]))
    offset=roots-ref[:,0]
    du=(offset*u[:,0]).sum(1);dv=(offset*v[:,0]).sum(1);dt=(offset*tangents[:,0]).sum(1)
    width=.65+.35*(1.-phase)
    q=ref+u*du[:,None,None]*width[:,:,None]+v*dv[:,None,None]*width[:,:,None]+tangents*dt[:,None,None]*(1.-phase[:,:,None])**2
    # A finite outward emergence joins each original follicle to the new full spatial path.
    end=11;delta=q[:,end]-roots;length=np.linalg.norm(np.diff(q[:,:end+1],axis=1),axis=2).sum(1)
    tangent=tangents[:,0]-normals*(tangents[:,0]*normals).sum(1)[:,None]
    m0=unit(unit(tangent)+.25*normals)*length[:,None]
    m1=unit(q[:,end+2]-q[:,end-2])*length[:,None]
    t=np.linspace(0.,1.,end+1,dtype='f4')[None,:,None]
    q[:,:end+1]=(2*t**3-3*t**2+1)*roots[:,None]+(t**3-2*t**2+t)*m0[:,None]+(-2*t**3+3*t**2)*q[:,end,None]+(t**3-t**2)*m1[:,None]
    q=q.astype('f4');q[:,0]=roots
    assert np.isfinite(q).all() and np.array_equal(q[:,0],base[:,0])
    np.savez_compressed(ROOT/'spatial-lock-A.npz',position=q,guideIndex=owner,guideEntryIndex=start,
        sourceComponent=data['component'][owner],sourceColumn=data['column'][owner])
    return q,dict(referenceGuides=len(guides),usedGuides=len(np.unique(owner)),
        changedStrands=int(np.any(q!=base,axis=(1,2)).sum()),
        rootToGuideEntryDistanceMmP0P50P95P100=(np.quantile([i[2] for i in closest],[0,.5,.95,1])*1000.).tolist(),
        newArcLengthMmP0P50P95P100=(np.quantile(np.linalg.norm(np.diff(q,axis=1),axis=2).sum(1),[0,.5,.95,1])*1000.).tolist())

def main():
    proof=read(ROOT/'assembled-source-receipt.json');assert sha(Path(proof['source']['path']))==proof['source']['sha256']
    assert not DEST.exists()
    bpy.ops.wm.open_mainfile(filepath=proof['source']['path'],load_ui=False,use_scripts=False)
    hair=bpy.data.objects['R484 complete hair | control'];data=hair.data
    base=np.empty((24831,80,3),dtype='f4');data.position_data.foreach_get('vector',base.ravel())
    fixture=bpy.data.objects['R482 archived complete neutral skin'].data
    skin=np.empty((len(fixture.vertices),3),dtype='f4');fixture.vertices.foreach_get('co',skin.ravel())
    faces=np.empty(24831,dtype='i4');data.attributes['AFN409_SKIN_TRIANGLE_ID'].data.foreach_get('value',faces)
    triangles=np.asarray([p.vertices[:] for p in fixture.polygons],dtype='i4')
    points=skin[triangles[faces]]
    normal=unit(np.cross(points[:,1]-points[:,0],points[:,2]-points[:,0]))
    q,metrics=reconstruct(base,normal)
    obj=hair.copy();obj.data=data.copy();obj.name='R484 complete hair | A';obj.data.name='R484 spatial locks | A'
    bpy.context.scene.collection.objects.link(obj)
    obj.data.position_data.foreach_set('vector',q.ravel());obj.data.update_tag();obj.update_tag()
    obj.hide_render=False;obj.hide_set(False);hair.hide_render=True;hair.hide_set(True)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    note=bpy.data.texts.new('Aevrynd_R484_Spatial_Lock_Provenance')
    note.write('Unaccepted root-to-tip fibre reconstruction using inspected original Angelica hair-strip 3D paths. Retain DarkNik / original NikZava284 CC BY4.0 attribution and all inherited notices. Original artist mesh is hidden reference, never a covering render layer. Every follicle, curve/point ID and radius is retained from r482 B. Neutral appearance, collisions, animation and runtime are not accepted. Native brush input has not been performed.\n')
    bpy.context.scene['R484_Status']='Unaccepted full spatial reconstruction. Static appearance and all collision/motion/runtime gates pending.'
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True,copy=True)
    (ROOT/'authored-source-receipt.json').write_bytes(json.dumps(dict(source=dict(path=str(DEST),bytes=DEST.stat().st_size,sha256=sha(DEST)),
        parent=proof['source'],metrics=metrics,positionHashes=dict(control=sha256(base.tobytes()).hexdigest(),A=sha256(q.tobytes()).hexdigest()),
        originalMeshHidden=True,allOriginalRootsExact=True,scalpContactChecked=False,motionChecked=False),indent=2).encode('utf8'))
    print(json.dumps(metrics,indent=2),flush=True)

if __name__=='__main__':main()
