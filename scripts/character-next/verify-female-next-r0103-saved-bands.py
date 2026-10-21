"""Independent complete source readback and affected sampled contact only."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0103-anatomical-front-lid-bands';OLD=E.parent/'r0102-facet-aware-lid-surface';S=R/'engine/assets/characters/female-next/source'
sp=importlib.util.spec_from_file_location('r103check',Path(__file__).with_name('verify-female-next-r0101-saved-lids.py'));f=importlib.util.module_from_spec(sp);sp.loader.exec_module(f);f.E=E;f.v.E=E;q=f.q
def save(n,x):f.save(n,x)
def sha(p):
 with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def lashes(V):
 helper=bpy.data.objects['AFN59_LASHES_NATIVE_POINT_POSES'];H=q.geom(helper)[1];worst=0.
 for row in json.loads((E/'a-retained-lash-bindings.json').read_text('utf8')):
  tri=V[np.array(row['actualSkinTriangle'])];normal=np.cross(tri[1]-tri[0],tri[2]-tri[0]);normal/=np.linalg.norm(normal);radius=row['sourceRootRadiusNative']*np.linalg.norm(np.array(helper.matrix_world)[:3,0]);expected=np.array(row['barycentric'])@tri+normal*radius;worst=max(worst,float(np.linalg.norm(H[row['pointStart']]-expected)))
 return worst
def main():
 tick=time.time();f.calibration();save('contact-sat-calibration.json',{'source':'Unchanged r101 vector SAT with four positive/negative calibration cases','passed':True,'numericSATIntervalToleranceM':1e-10,'scope':'Triangle surfaces, no finite-volume or continuous proof.'})
 summary=json.loads((E/'a-build-summary.json').read_text('utf8'));base=Path(summary['source']);path=Path(summary['output']);bpy.ops.wm.open_mainfile(filepath=str(base));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();names=f.m.m.rig.native_names();native={name:q.signature(bpy.data.objects[name]) for name in names};rig=f.h.rig_signature();d,V0,T0=f.geom(bpy.data.objects[summary['renderSkin']]);V0=V0.copy();retained=json.loads((E.parent/'r0101-articulated-eyelid-topology/b-build-summary.json').read_text('utf8'))['retainedFineFaces'];uv0={u.name:hashlib.sha256(q.arr(u.data,'uv',len(u.data),2).reshape(-1,3,2)[:retained].tobytes()).hexdigest() for u in d.uv_layers};P0=q.hair(bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN']).copy();textures0={im.filepath:sha(Path(bpy.path.abspath(im.filepath))) for im in bpy.data.images if im.source=='FILE' and not im.packed_file and im.filepath}
 bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[summary['renderSkin']];hair=bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'];d,V,T=f.geom(skin);mapping=np.load(E/'a-front-band-lineage.npz')['originalActualToNewActual'];valid=mapping>=0;assert (~valid).sum()==320;diff=float(np.linalg.norm(V[mapping[valid]]-V0[valid],axis=1).max());hairDiff=float(np.linalg.norm(q.hair(hair)-P0,axis=1).max());uv={u.name:hashlib.sha256(q.arr(u.data,'uv',len(u.data),2).reshape(-1,3,2)[:retained].tobytes()).hexdigest() for u in d.uv_layers};assert diff<4e-6 and hairDiff<6e-6 and uv==uv0;assert rig==f.h.rig_signature() and all(native[name]==q.signature(bpy.data.objects[name]) for name in names);textures=[]
 for im in bpy.data.images:
  if im.source=='FILE' and not im.packed_file and im.filepath:
   p=Path(bpy.path.abspath(im.filepath));assert sha(p)==textures0[im.filepath];textures.append({'relative':im.filepath,'sha256':sha(p),'bytes':p.stat().st_size})
 assert len(textures)==15;edges=np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]);lo=np.minimum(edges[:,0],edges[:,1]);hi=np.maximum(edges[:,0],edges[:,1]);un,ix,inc=np.unique(lo.astype('u8')*len(V)+hi,return_inverse=True,return_counts=True);orientation=np.bincount(ix,weights=np.where(edges[:,0]<edges[:,1],1,-1));readback={'source':str(path),'sha256':sha(path),'bytes':path.stat().st_size,'openedIndependently':True,'vertices':len(V),'triangles':len(T),'finite':bool(np.isfinite(V).all()),'retainedActualVertexMaximumWorldDifferenceM':diff,'allGroomControlsMaximumWorldDifferenceM':hairDiff,'retainedOriginalBodyUVExact':uv==uv0,'originalNativeBodyOpticsMeshKeysUVWeightsAndRig52Preserved':True,'actualUnusedVertices':len(V)-len(np.unique(T)),'openEdges':int((inc==1).sum()),'nonTwoIncidentEdges':int((inc!=2).sum()),'orientationConflictEdges':int(((inc==2)&(orientation!=0)).sum()),'closedEdgesNotSelfOrFiniteContactCertificate':True,'externalTextures':textures,'completeOperationAppearanceContactRuntimeAccepted':False};save('minimum-saved-readback.json',readback);print('R103_INDEPENDENT_SOURCE_READBACK_DONE',flush=True)
 face=bpy.data.objects['AFN59_FACE_CONTROLS'];oral=bpy.data.objects['AFN74_ORAL_CONTROLS']
 for ob in [face,oral]:
  if ob.animation_data:ob.animation_data.action=None
 rows=[];baseline=None;contactFailed=False
 for i,value in enumerate([0.,.5,1.,0.]):
  f.deliver(value);dd,W,TT=f.geom(skin);HP=q.hair(hair);assert np.array_equal(TT,T);actual=float(face.evaluated_get(bpy.context.evaluated_depsgraph_get())['blink_left']);assert actual==value
  if baseline is None:baseline=(W.copy(),HP.copy())
  row={'blink':value,'evaluatedBlinkLeft':actual,'actualWholeSkinMaximumWorldMoveM':float(np.linalg.norm(W-baseline[0],axis=1).max()),'actualGroomMaximumWorldMoveM':float(np.linalg.norm(HP-baseline[1],axis=1).max()),'all24800RootCentreMaximumWorldErrorM':f.r99.root_error(hair,W),'all412LashRootCentreFrameMaximumWorldErrorM':lashes(W),'finite':bool(np.isfinite(W).all() and np.isfinite(HP).all())}
  if i<3 and not contactFailed:
   row['scopedOpticalSurfaceContact']=f.contact(W,TT);contactFailed=any(x['triangleSurfaceIntersectionOrTouchWitnesses'] or not x['allCandidatesInspected'] for x in row['scopedOpticalSurfaceContact'])
  row['file']=str(E/('matched-a-anatomical-bands'+('' if value==0 else '-half' if value==.5 else '-closed')+'-face.png'));row['usesAlreadyRenderedSourcePosePreviewNotAnotherRender']=True;rows.append(row);save('evaluated-blink-and-contact.json',{'source':str(path),'sourceSha256':readback['sha256'],'states':rows,'completeOperationAccepted':False,'globalFiniteSelfHairClothingContinuousRuntimeCertified':False,'scope':'Actual complete saved woman; exact assigned/evaluated blink samples, actual whole-skin nearby faces against each current evaluated optical mesh. Rejected appearance candidate: only0/half/closed plus neutral restore; reuse existing actual previews rather than expand animation. Stop contact checks after first failure. Not global signed-distance, finite thickness, continuous time or natural-motion proof.'});print('R103_SAMPLED_BLINK',i,value,'contactFailed',contactFailed,flush=True)
 save('neutral-restore.json',{'actualSkinMaximumWorldErrorM':float(np.linalg.norm(W-baseline[0],axis=1).max()),'actualGroomMaximumWorldErrorM':float(np.linalg.norm(HP-baseline[1],axis=1).max()),'seconds':time.time()-tick,'sourceUnmodifiedDuringReadback':sha(path)==readback['sha256']})
 print('R103_SAVED_LINING_VERIFICATION_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
