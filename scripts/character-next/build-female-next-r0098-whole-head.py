"""Whole craniofacial scan-envelope reconstruction, not a facial-weight scan.
The inspected Dan Ulrich female source supplies the actual complete head form.
Existing skin topology/UV stays; eye anchors are protected and internal/facial
attachments are explicitly transported by a common old->new skin cage.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0098-whole-head-foundation';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0097-neutral-scalp-control-reference.blend';OUT=S/'aevrynd-female-next-r0098-a-whole-scan-head-reconstruction.blend'
def mod(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);return a
v=mod('r98headviews','render-female-next-r0091-matched.py');v.E=E;m=v.m;q=m.q
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8')
def smooth(x):x=np.clip(x,0,1);return x*x*(3-2*x)
def main():
 tick=time.time();assert not OUT.exists() and sha(SRC)=='353a3067e87bd6617cabb709ac5e8fc23f947f6841d2af95e835824369cec69b';source=read=json.loads((E/'official-female-reference.json').read_text('utf8'));z=np.load(E/'official-female-reference-geometry.npz');sourceV=z['world'];sourceT=z['triangles'];bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];A=np.array(body.matrix_world);native=np.load(R/'Reference/character/charmorph-vitruvian-cc0/Default.npy');current=np.empty_like(native,dtype='f8');coverage=np.zeros(len(native),'i4');nativeInfo={}
 for name in m.rig.native_names():
  ob=bpy.data.objects[name];ids=q.arr(ob.data.attributes['AFN60_NativeVertexID'].data,'value',len(ob.data.vertices),dtype='i4');flags=[]
  for md in ob.modifiers:
   if md.type in ['SUBSURF','NODES']:flags.append((md,md.show_viewport));md.show_viewport=False
  bpy.context.view_layer.update();_,world=q.geom(ob);assert len(world)==len(ids);current[ids]=world;coverage[ids]+=1;nativeInfo[name]={'ids':ids,'flags':flags}
  for md,flag in flags:md.show_viewport=flag
 assert np.all(coverage==1);bpy.context.view_layer.update()
 # One complete-source similarity placement using the two actual geometric
 # eye shell centres. These are registration landmarks, not anatomy measures.
 targetEyes=[];sourceEyes=[]
 for side in ['L','R']:
  _,points=q.geom(bpy.data.objects['AFN60_'+side+'_EYE_OUTER_SHELL_APPROX']);targetEyes.append((points.min(0)+points.max(0))/2);row=next(row for name,row in source['eyes'].items() if name.endswith('.'+side));sourceEyes.append(np.mean(row['bounds'],axis=0))
 targetEyes=np.array(targetEyes);sourceEyes=np.array(sourceEyes);diff=sourceEyes[0]-sourceEyes[1];tdiff=targetEyes[0]-targetEyes[1];scale=float(np.linalg.norm(tdiff)/np.linalg.norm(diff));rotation=np.array(Vector(diff).rotation_difference(Vector(tdiff)).to_matrix());sourceMean=sourceEyes.mean(0);targetMean=targetEyes.mean(0);aligned=(sourceV-sourceMean)@rotation.T*scale+targetMean;keep=aligned[sourceT,2].min(1)>targetMean[2]-.26;tree=BVHTree.FromPolygons(aligned.tolist(),sourceT[keep].tolist(),all_triangles=True)
 canonical=np.load(R/'Evidence/character-female-next/r0057-coherent-foundation/canonical-mesh-data.npz');oldNative=np.load(E.parent/'r0092-native-compatible-groom/native-Eve-source.npz');T=oldNative['triangles'];mi=np.repeat(canonical['materials'],oldNative['sourceFaceCounts']-2);skinT=T[np.isin(mi,[4,5])];skinIDs=np.unique(skinT);eligible=skinIDs[current[skinIDs,2]>1.32];desired=current.copy();projectionDistance=[];weights=[]
 for i in eligible:
  point=current[i];co,no,face,gap=tree.find_nearest(Vector(point));neck=float(smooth((point[2]-1.32)/.055));eyeDistance=float(np.linalg.norm(targetEyes-point,axis=1).min());eyeProtection=float(smooth((eyeDistance-.018)/.010));weight=neck*eyeProtection;desired[i]=point+(np.array(co)-point)*weight;projectionDistance.append(gap);weights.append(weight)
 move=np.linalg.norm(desired-current,axis=1);save('a-head-envelope-plan.json',{'sourceCollection':source['collection'],'sourceMetadata':source['metadata'],'registration':'Single two-eye geometric centre similarity; full inspected source head envelope, no source/morph-weight variants. Centres are AABB geometric proxies, not biological measurements.','sourceEyeCentres':sourceEyes,'targetEyeCentres':targetEyes,'sourceScale':scale,'sourceRotation':rotation,'sourceMean':sourceMean,'targetMean':targetMean,'sourceHeadTriangles':int(keep.sum()),'skinHeadVertices':len(eligible),'neckTransitionWorldM':[1.32,1.375],'eyeAnchorProtectedRadiusM':.018,'eyeTransitionEndRadiusM':.028,'maximumAppliedHeadDeltaM':float(move.max()),'sourceNearestDistanceQuantilesM':np.quantile(projectionDistance,[0,.5,.95,1]),'purpose':'Adopt the coherent donor forehead/zygoma/maxilla/nose/mandible/chin/skull envelope on the existing full woman, preserving body/eye anchors and UV. Not an exact scan/digital-double reconstruction or new contact qualification.'});assert np.isfinite(desired).all() and move.max()<.035,('Head correspondence guard',float(move.max()))
 # A common old/new full skin cage transports head interiors, rigid teeth,
 # and the actual brows/lash point helpers; no invented closure faces.
 cageTri=skinT[current[skinT,2].min(1)>1.0];used,idx=np.unique(cageTri,return_inverse=True);F=idx.reshape(-1,3);cm=bpy.data.meshes.new('AFN98_TEMP_OLD_CRANIOFACIAL_SKIN_CAGE');cm.from_pydata(current[used].tolist(),[],F.tolist());cm.update();cage=bpy.data.objects.new(cm.name,cm);s.collection.objects.link(cage);cage.hide_render=True;groups=[];arrays=[current.copy()];offset=len(current)
 for name in ['AFN59_BROWS_NATIVE_POINT_POSES','AFN59_LASHES_NATIVE_POINT_POSES','AFN74_UPPER_TEETH_RIGID','AFN74_LOWER_TEETH_RIGID']:
  ob=bpy.data.objects[name];_,P=q.geom(ob);groups.append({'name':name,'start':offset,'count':len(P),'oldWorld':P.copy(),'matrix':np.array(ob.matrix_world)});arrays.append(P);offset+=len(P)
 allP=np.concatenate(arrays);mesh=bpy.data.meshes.new('AFN98_TEMP_ATTACHMENT_POINTS');mesh.vertices.add(len(allP));mesh.vertices.foreach_set('co',allP.astype('f4').ravel());mesh.update();carrier=bpy.data.objects.new(mesh.name,mesh);s.collection.objects.link(carrier);carrier.hide_render=True;sd=carrier.modifiers.new('AFN98_COMMON_SKIN_ENVELOPE_TRANSFER','SURFACE_DEFORM');sd.target=cage
 for ob in bpy.context.selected_objects:ob.select_set(False)
 carrier.select_set(True);bpy.context.view_layer.objects.active=carrier;bpy.context.view_layer.update();bpy.ops.object.surfacedeform_bind(modifier=sd.name);assert sd.is_bound;cm.vertices.foreach_set('co',desired[used].astype('f4').ravel());cm.update();bpy.context.view_layer.update();mapped=q.arr(carrier.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices,'co',len(allP),3).astype('f8');delta=mapped-allP;delta[allP[:,2]<=1.32]=0
 # Direct skin reconstruction takes precedence over the common cage's skin
 # interpolation. Preserve original optical shells exactly; protect their
 # immediate skin/lining anchors as declared rather than warping eyeballs.
 delta[skinIDs]=desired[skinIDs]-current[skinIDs];protect=np.linalg.norm(current[:,None,:]-targetEyes[None,:,:],axis=2).min(1)<.018;delta[:len(current)][protect]=0
 bodyIDs=nativeInfo[body.name]['ids'];localDelta=delta[bodyIDs]@np.linalg.inv(A[:3,:3]).T;basis=q.arr(body.data.shape_keys.key_blocks[0].data,'co',len(bodyIDs),3);key=body.shape_key_add(name='AFN98_Whole_Craniofacial_Scan_Envelope');key.data.foreach_set('co',(basis+localDelta).astype('f4').ravel());key.value=1;attachments={}
 for group in groups:
  ob=bpy.data.objects[group['name']];d=delta[group['start']:group['start']+group['count']]@np.linalg.inv(group['matrix'][:3,:3]).T
  if ob.data.shape_keys:
   for block in ob.data.shape_keys.key_blocks:
    old=q.arr(block.data,'co',group['count'],3);block.data.foreach_set('co',(old+d).astype('f4').ravel())
  else:
   old=q.arr(ob.data.vertices,'co',group['count'],3);ob.data.vertices.foreach_set('co',(old+d).astype('f4').ravel());ob.data.update()
  attachments[group['name']]={'points':group['count'],'maximumAppliedWorldDeltaM':float(np.linalg.norm(delta[group['start']:group['start']+group['count']],axis=1).max()),'method':'Common old/new craniofacial skin SurfaceDeform field; identical static offset added to retained expression key positions, or to the rigid tooth mesh. Existing topology, UV, weights/drivers and key differences retained; full new motion/contact still unqualified.'}
 bpy.data.objects.remove(carrier,do_unlink=True);bpy.data.meshes.remove(mesh);bpy.data.objects.remove(cage,do_unlink=True);bpy.data.meshes.remove(cm);bpy.context.view_layer.update();hair=bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'];HP=q.hair(hair);assert np.isfinite(HP).all();body['AFN98_scope']='Full inspected Dan Ulrich CC0 female head scan-envelope reconstruction with original body topology/UV and protected optical centres. Common cage explicitly retargets interiors/brows/lashes/teeth. Original skull/head geometry retained by prior immutable source and new sculpt key. Retained live scalp root IDs refer to unchanged evaluated topology but the changed head/contact scope must be reverified.';m.rig.shade.settings();m.rig.k.b.camera('face');s.camera.data.lens=85;s.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
 np.savez_compressed(E/'a-whole-head-lineage.npz',oldNativeWorld=current,desiredSkinNativeWorld=desired,appliedNativeWorldDelta=delta[:len(current)],bodyNativeIDs=bodyIDs,sourceHeadAlignedWorld=aligned,sourceHeadTriangles=sourceT[keep],cageNativeIDs=used,cageTriangles=F,targetEyeCentres=targetEyes,sourceEyeCentres=sourceEyes,objectMatrix=A,attachmentOldWorld=allP[len(current):],attachmentAppliedWorldDelta=delta[len(current):]);save('a-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'bodyObject':body.name,'newHeadShapeKey':key.name,'referenceSource':source['source'],'referenceSourceSha256':source['sourceSha256'],'referenceAssetMetadata':source['metadata'],'construction':'One coherent complete female scan-head envelope, two-eye similarity placement, native craniofacial skin reconstruction, common-cage attachment retarget. No L2 coefficient/crease/aperture/shape parameter sweep.','changedOuterSkinVertices':int(np.count_nonzero(move>1e-7)),'maximumAppliedSkinWorldDeltaM':float(move.max()),'allBodyBelowWorldZ1_32Unchanged':bool(np.all(delta[:len(current)][current[:,2]<=1.32]==0)),'originalOpticalShellAndIrisGeometryUnedited':True,'originalTopologyUVSourceWeightsBoneRestAndMaterialsUnedited':True,'attachments':attachments,'sourceEyeProtectionAndGeometryProxiesNotAnatomicalValidation':True,'hairExistingCurrentScalpFramesFollowSameUnchangedTopology':'Root triangle indices stable by topology, live current geometry responds to new head. Rest frames are the retained pre-morph reference; no inherited contact certificate.','appearanceMotionContactsRuntimeOrCompleteOperationAccepted':False,'secondsBeforePreview':time.time()-tick});rows=[]
 for view in ['face','profile','oblique','body-face']:rows.append(v.image('a-whole-head',view));save('a-view-controls.json',rows)
 print('R98_COMPLETE_WHOLE_HEAD_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
