"""Original artist rest-curvature full-shaft fitting against actual current Skin.
One deterministic constraint construction, not a gravity-grown new hair field.
"""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time,datetime,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0187-source-emitter-domain';OUT=C/'assets-source/aevrynd-character/female-next/r0187-source/aevrynd-female-next-r0187-a-source-curvature-contact-fit.blend'
sp=importlib.util.spec_from_file_location('r169',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def save(n,q):(E/n).write_bytes((json.dumps(q,indent=2)+'\n').encode())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 tick=time.time();timing=json.loads((E/'before.json').read_text());assert not OUT.exists() and sha(timing['source'])==timing['sourceSha256'];check=json.loads((E/'actual-emitter-domain-inspection.json').read_text());assert check['actualRawVersusAssumedMaximumM']==0 and check['reopened248ParentRootsVersusRecordedMaximumM']==0;cacheFile=R/'Evidence/character-female-next/r0096-artist-bob-foundation/native-Bob-source-and-children.npz';cache=np.load(cacheFile);raw=cache['nativeRawAPI'].astype('f8');counts=cache['validCacheCounts'];assert raw.shape==(25048,17,3);base=np.empty_like(raw)
 for i,(path,n) in enumerate(zip(raw,counts)):
  path=path[:int(n)];length=np.r_[0,np.linalg.norm(np.diff(path,axis=0),axis=1).cumsum()];base[i]=np.stack([np.interp(np.linspace(0,length[-1],17),length,path[:,j]) for j in range(3)],1)
 sourceWidths=json.loads((R/'Evidence/character-female-next/r0096-artist-bob-foundation/native-Bob-extraction.json').read_text('utf-8'))['originalSettings'];spw=importlib.util.spec_from_file_location('width',R/'engine/character/groom_import_semantics.py');width=importlib.util.module_from_spec(spw);spw.loader.exec_module(width);A=np.load(R/'Evidence/character-female-next/r0094-authored-growth-routing/b-source-width-lineage.npz')['objectMatrix'];rad=np.array(width.legacy_particle_point_radii(sourceWidths,17))*np.linalg.norm(A[:3,0]);assert rad[0]>.00005
 bpy.ops.wm.open_mainfile(filepath=timing['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[a.FIXED[0]];old=bpy.data.objects[a.FIXED[1]];old.material_slots[0].link='DATA';bpy.data.objects[a.FIXED[2]].hide_render=False;bpy.data.objects[a.FIXED[2]].hide_set(False);bpy.data.objects['AFN184_ACTUAL_NATIVE_DEFORMED_LASHES'].hide_render=True;bpy.data.objects['AFN184_ACTUAL_NATIVE_DEFORMED_LASHES'].hide_set(True);protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};W,T=a.geometry(skin);sf=np.load(E.parent/'r0171-actual-scalp-chart/actual-scalp-groom-lineage.npz')['actualScalpFaces'];scalp=BVHTree.FromPolygons(W.tolist(),T[sf].tolist(),all_triangles=True);body=BVHTree.FromPolygons(W.tolist(),T.tolist(),all_triangles=True);rootT=[];BC=[];root=[];normals=[]
 for p in base[:,0]:
  hit,no,fi,dist=scalp.find_nearest(Vector(p));f=int(sf[fi]);B=W[T[f]];uv=np.linalg.lstsq(np.column_stack((B[1]-B[0],B[2]-B[0])),np.array(hit)-B[0],rcond=None)[0];bc=np.clip(np.array([1-uv.sum(),*uv]),0,1);bc/=bc.sum();normal=np.cross(B[1]-B[0],B[2]-B[0]);normal/=np.linalg.norm(normal);rootT.append(T[f]);BC.append(bc);root.append(bc@B);normals.append(normal)
 rootT=np.array(rootT,'i4');BC=np.array(BC);root=np.array(root);normals=np.array(normals);centre=root+normals*(rad[0]+.000002);shift=centre-base[:,0];u=np.linspace(0,1,17);preferred=base+shift[:,None]*(1-u)[None,:,None]**2;P=preferred.copy();restLength=np.linalg.norm(np.diff(base,axis=1),axis=2);restLap=base[:,:-2]+base[:,2:]-2*base[:,1:-1];records=[];direction=Vector((.3187,1.0,.1371)).normalized()
 def parity(point):
  origin=Vector(point);hits=0
  for _ in range(24):
   q,no,fi,dist=body.ray_cast(origin,direction,3.)
   if q is None:break
   hits+=1;origin=q+direction*1e-6
  return hits%2==1
 # Local finite-centre contact corrections and rest-curvature/length coupling
 # move complete shafts; there is no uniform outward shift, deleted fibre,
 # hidden failed layer or reduction of artist radius/action/count.
 for iteration in range(10):
  P[:,1:-1]+=.10*(P[:,:-2]+P[:,2:]-2*P[:,1:-1]-restLap);P[:,1:]+=.015*(preferred[:,1:]-P[:,1:])
  for sweep in range(2):
   for j in range(16):
    delta=P[:,j+1]-P[:,j];length=np.linalg.norm(delta,axis=1);correction=delta*((length-restLength[:,j])/np.maximum(length,1e-10))[:,None]
    if j==0:P[:,1]-=correction
    else:P[:,j]+=.5*correction;P[:,j+1]-=.5*correction
  P[:,0]=centre;corrections=0;insideCandidates=0;maxCorrection=0.
  for cid,path in enumerate(P):
   for j in range(1,17):
    point=path[j];hit,no,fi,distance=body.find_nearest(Vector(point));normal=np.array(no);signed=float((point-np.array(hit))@normal);near=distance<rad[j]+.000002;inside=False
    if signed<0:
     insideCandidates+=1;inside=parity(point)
    if near or inside:
     destination=np.array(hit)+normal*(rad[j]+.000002);amount=float(np.linalg.norm(destination-point));path[j]=destination;corrections+=1;maxCorrection=max(maxCorrection,amount)
  relative=np.abs(np.linalg.norm(np.diff(P,axis=1),axis=2)-restLength)/np.maximum(restLength,1e-9);records.append({'iteration':iteration,'actualLocalPointContactCorrections':corrections,'insideCandidateParityTests':insideCandidates,'maximumLocalCorrectionM':maxCorrection,'relativeSegmentLengthErrorQuantiles':np.quantile(relative,[.5,.9,1]).tolist(),'localContactModelNotExactRenderedSplineOrGlobalSignedProof':True});print('R187_ARTIST_CURVATURE_CONTACT_ITERATION',iteration,corrections,round(time.time()-tick,2),flush=True)
 N=24800;hd=bpy.data.hair_curves.new('AFN187_ARTIST_CURVATURE_CONTACT_FIT_DATA');hd.add_curves([17]*N);hd.position_data.foreach_set('vector',P[248:].astype('f4').ravel());hd.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.tile(rad,N).astype('f4'));hd.attributes.new('AFN187_SOURCE_CACHE_ID','INT','CURVE').data.foreach_set('value',np.arange(248,25048,dtype='i4'))
 for j in range(3):hd.attributes.new('AFN187_SkinVertex'+str(j),'INT','CURVE').data.foreach_set('value',rootT[248:,j])
 hd.attributes.new('AFN187_RootBarycentric','FLOAT_VECTOR','CURVE').data.foreach_set('vector',BC[248:].astype('f4').ravel());hd.surface=skin;hd.surface_uv_map=skin.data.uv_layers.active.name;hair=bpy.data.objects.new('AFN187_ACTUAL_ARTIST_CURVATURE_CONTACT_HAIR',hd);s.collection.objects.link(hair);gd=bpy.data.hair_curves.new('AFN187_ALL248_FITTED_ARTIST_GUIDES_DATA');gd.add_curves([17]*248);gd.position_data.foreach_set('vector',P[:248].astype('f4').ravel());go=bpy.data.objects.new('AFN187_COMPLETE_SOURCE_GUIDES',gd);s.collection.objects.link(go);go.hide_render=True;go.hide_set(True);mat=bpy.data.materials.new('AFN187_OWN_NATIVE_BROWN_HAIR_SHADER');mat.use_nodes=True;ns=mat.node_tree.nodes;ns.clear();bs=ns.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='MELANIN';bs.inputs['Melanin'].default_value=.75;bs.inputs['Melanin Redness'].default_value=.15;bs.inputs['Roughness'].default_value=.35;bs.inputs['Radial Roughness'].default_value=.45;output=ns.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(bs.outputs[0],output.inputs[0]);hd.materials.append(mat);old.hide_render=True;old.hide_set(True);s.camera.data.type='PERSP';s.render.hair_type='STRIP';bpy.context.view_layer.update();actual,off=m.curveworld(hair);error=float(np.linalg.norm(actual-P[248:].reshape(-1,3),axis=1).max());assert error<3e-6 and protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected}
 np.savez_compressed(E/'source-curvature-contact-lineage.npz',rootTriangles=rootT,rootBC=BC,rootWorld=root,rootNormal=normals,rootCentre=centre,sourceRootDisplacement=shift,sourceSegmentLengths=restLength.astype('f4'),sourceParentGuidesWorld=base[:248].astype('f4'),actualParentGuidesWorld=P[:248].astype('f4'),radius=rad)
 save('direct-source-curvature-contact-authoring.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceCache':str(cacheFile),'sourceCacheSHA256':sha(cacheFile),'actualSourceEmitterMatchesPreviousSource':True,'initialOriginalToCurrentRootDisplacementQuantilesM':np.quantile(np.linalg.norm(shift,axis=1),[0,.5,.9,1]).tolist(),'actualIterations':records,'nativeDisplayMaximumErrorM':error,'all24800SourceChildrenAnd248SourceGuidesRetained':True,'changedFailedPremise':'Source mismatch hypothesis falsified. No retry of nearest-Skin volumetric field. Direct complete original artist rest-curvature/edge-length constraints plus current-Skin local contact adjustments move full shafts, preserving source preferred curvature without freezing failed free sections. No new normal-growth/gravity style field, blanket push, culling or shader/radius/density sweep.','sourceRadiusAndRootCentreOffsetM':[float(rad[0]),float(rad[0]+.000002)],'localNearestNormalAndRayParityEngineeringModelNotGlobalContactCertificate':True,'headFollowNaturalDynamicsRuntimeNotClaimed':True,'secondsBeforePreview':time.time()-tick})
 hair['scope']='Unaccepted static original artist rest-curvature/length contact fit. All24800 children/248 guides, source-backed width/native own shader. Complete finite rendered/self/continuous contact, natural motion/head follow/runtime not proved.';a.b.u.v.E=E;views=[a.b.u.v.image('a-source-curvature-contact-fit','face')];bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=True);save('a-build-summary.json',{'source':timing['source'],'output':str(OUT),'sha256':sha(OUT),'bytes':OUT.stat().st_size,'engineAlias':str(R/'engine/assets/characters/female-next/source/r0187-source'/OUT.name),'actualSkin':skin.name,'actualRig':'AFN138_ACTUAL_CURRENT_GAZE_RIG','actualHair':hair.name,'actualGuides':go.name,'retainedSourceHair':old.name,'nativeStrands':N,'sourceParentGuides':248,'points':len(actual),'completeWomanCandidates':1,'fullNativeGroomCandidate':True,'unaccepted':True,'nativeDisplayMaximumErrorM':error,'secondsBeforeOtherViews':time.time()-tick});assert OUT.stat().st_size<timing['sourceBudgetBytes']
 for v in ['body-face','profile','back','oblique']:views.append(a.b.u.v.image('a-source-curvature-contact-fit',v));save('source-curvature-preview-controls.json',views)
 print('R187_COMPLETE_SOURCE_CURVATURE_CONTACT_FIT_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
