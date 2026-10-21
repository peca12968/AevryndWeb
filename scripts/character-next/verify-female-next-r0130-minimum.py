"""Minimum recovery/current displayed-geometry operations after visible rejection."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0130-artist-native-groom';S=R/'engine/assets/characters/female-next/source'
sp=importlib.util.spec_from_file_location('r130verifybase',Path(__file__).with_name('build-female-next-r0116-native-eye-character.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item())+'\n',encoding='utf-8')
def rawmesh(o):return q.arr(o.data.vertices,'co',len(o.data.vertices),3)
def put(o,V):o.data.vertices.foreach_set('co',V.ravel());o.data.update();bpy.context.view_layer.update()
def main():
 tick=time.time();result={}
 for tag in ['a','b']:
  summary=json.loads((E/(tag+'-build-summary.json')).read_text('utf-8'));src=Path(summary['output']);assert a.sha(src)==summary['sha256'];bpy.ops.wm.open_mainfile(filepath=str(src));skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'];hair=bpy.data.objects[summary['hairObject']];cap=bpy.data.objects[summary['capObject']];carrier=bpy.data.objects[summary['carrierObject']];protected=a.protected();data=np.load(E/(tag+'-native-emitter-field-lineage.npz'));bpy.context.view_layer.update();_,W,T=b.u.b.geom(skin);W=W.copy();T=T.copy();before=q.hair(hair).copy();r=q.arr(hair.data.attributes['radius'].data,'value',len(before));counts=np.array([c.points_length for c in hair.data.curves]);assert np.array_equal(counts,data['sourceCounts']);assert np.max(np.linalg.norm(before-data['mappedWorld'],axis=1))<3e-6;assert [a.hasharray(W),a.hasharray(T)]==summary['currentSkinHashes'];ops={}
  # Actual stored path edit; a bound deformation may ignore input edits. Record it.
  V=rawmesh(carrier);edited=V.copy();j=int(counts[0]-1);edited[j,1]+=.001;put(carrier,edited);delta=np.linalg.norm(q.hair(hair)-before,axis=1);ops['actualStoredPathFreePointEdit']={'requestedOffsetM':.001,'actualVisibleHairMaxM':float(delta.max()),'pointsAbove1um':int(np.count_nonzero(delta>1e-6))};put(carrier,V);assert np.array_equal(q.hair(hair),before)
  # Actual original-source scalp edit, through current-skin binding and field.
  C=rawmesh(cap);edited=C.copy();k=int(np.argmax(C[:,2]));edited[k,0]+=.001;put(cap,edited);delta=np.linalg.norm(q.hair(hair)-before,axis=1);ops['actualSourceCapVertexEdit']={'vertex':k,'requestedOffsetM':.001,'actualVisibleHairMaxM':float(delta.max()),'pointsAbove1um':int(np.count_nonzero(delta>1e-6))};put(cap,C);assert np.array_equal(q.hair(hair),before)
  # Current visible head must drive the actual bound cap, not hidden r117 skin.
  raw=rawmesh(skin);ids=data['currentSkinVertexIDs'];weights=data['currentSkinBarycentric'];k=int(np.argmax(data['currentSkinFittedCapWorld'][:,2]));vertex=int(ids[k,int(np.argmax(weights[k]))]);edited=raw.copy();edited[vertex,2]+=.0002;put(skin,edited);_,movedSkin,_=b.u.b.geom(skin);_,movedCap,_=b.u.b.geom(cap);expected=np.einsum('ij,ijk->ik',weights,movedSkin[ids]);bindingError=float(np.linalg.norm(movedCap-expected,axis=1).max());delta=np.linalg.norm(q.hair(hair)-before,axis=1);ops['actualCurrentVisibleSkinVertexEdit']={'vertex':vertex,'requestedOffsetM':.0002,'actualBoundCapVsOwnTriangleExpectMaxErrorM':bindingError,'actualVisibleHairMaxM':float(delta.max()),'pointsAbove1um':int(np.count_nonzero(delta>1e-6))};assert bindingError<3e-6;put(skin,raw);assert np.array_equal(q.hair(hair),before);_,restored,RT=b.u.b.geom(skin);assert np.array_equal(W,restored) and np.array_equal(T,RT) and a.protected()==protected;assert np.array_equal(r,q.arr(hair.data.attributes['radius'].data,'value',len(before)))
  images=[]
  for image in bpy.data.images:
   if image.source=='FILE' and not image.packed_file and image.filepath:
    p=Path(bpy.path.abspath(image.filepath));assert p.is_file(),str(p);images.append({'relative':image.filepath,'absolute':str(p),'bytes':p.stat().st_size,'sha256':a.sha(p)})
  assert a.sha(src)==summary['sha256'];result[tag]={'source':str(src),'sha256':summary['sha256'],'bytes':src.stat().st_size,'independentlyReopened':True,'actualVisibleHairPointsAndAllSourceCountsRecovered':True,'curves':len(counts),'points':len(before),'operations':ops,'actualSkinSourceCapCarrierVisibleHairAndRadiiRestoredExactly':True,'originalHiddenRollbackExact':True,'allReferencedExternalTextures':images,'completeUsableHairstyleOperationAccepted':False,'naturalMotionFiniteSelfContinuousContactAndRuntimeAccepted':False}
  save('minimum-saved-emitter-field-readback.json',{'sources':result,'scope':'Actual same-woman source recovery and bounded edit observations ONLY. Both full appearances rejected. No complete usable operation, biological dynamics, finite or continuous collision or runtime proof.','seconds':time.time()-tick})
 print('R130_COMPLETE_REJECTED_SOURCES_MINIMUM_REOPEN_RESTORE_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
