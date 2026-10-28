"""Minimum frozen r202 failure reproduction through F-hosted access paths.
No new candidate, no changed guard, no retry of the failed whole-groom emission.
"""
from pathlib import Path
import json,os,hashlib,datetime,shutil,bpy,numpy as np
from mathutils import Vector,Matrix
access=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'))
A=Path(access['directCharacterArchiveAccess']);R=Path(access['directProjectAccess']);E=A/'evidence/character-female-next/r0202-independent-complete-groom';F=Path('F:/AevryndEvidence/r0202-independent-complete-groom');F.mkdir(parents=True,exist_ok=True)
import importlib.util,time
C=A;OUT=A/'assets-source/aevrynd-character/female-next/r0202-source/aevrynd-female-next-r0202-rejected-correspondence-diagnostic.blend';assert not OUT.exists()
sp=importlib.util.spec_from_file_location('r202base',A/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
def attr(d,n,typ,v,prop='value',domain='POINT'):
 at=d.attributes.new(n,typ,domain);at.data.foreach_set(prop,np.asarray(v).ravel());return at
tick=time.time();scriptSHA=sha(E/'first-authoring.failed.py.txt');t=json.loads((E/'before.json').read_text('utf-8'));source=A/'assets-source/aevrynd-character/female-next/r0201-source/aevrynd-female-next-r0201-full-rest-native-volume.blend';assert sha(source)==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.context.scene;s.frame_set(1);skin=bpy.data.objects[a.FIXED[0]];old=bpy.data.objects[a.FIXED[1]];previous=bpy.data.objects['AFN198_ACTUAL_SURFACE_BORN_NATIVE_GROOM'];protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING}
n=np.load(E/'failed-root-domain-lineage.npz');guideRoots=n['sourceGuideRoots'];guideSeeds=n['sourceGuideSeeds'];guideTargets=n['currentTargets'];gf=n['currentFaces'];gb=n['currentBC'];gg=n['sourceSeedGapsM'];coef=n['quadraticCoefficients'];sourceCentre=n['sourceCentre'];targetCentre=n['targetCentre'];scale=n['axisScale'];W,T=a.geometry(skin);assert np.array_equal(T[gf],n['currentTriangles']);normalizer=.1
u=(guideRoots-sourceCentre)/normalizer;x,y,z=u.T;B=np.column_stack([np.ones(len(x)),x,y,z,x*x,x*y,x*z,y*y,y*z,z*z]);fitError=np.linalg.norm((guideRoots-sourceCentre)*scale+targetCentre+B@coef-guideTargets,axis=1)
assert float(gg.max())>.035
failedIDs=np.flatnonzero(gg>=.035);assert len(failedIDs)>0
rows=[{'sourceGuideID':int(i),'actualSourceRootWorld':guideRoots[i].tolist(),'unqualifiedBoxSeedWorld':guideSeeds[i].tolist(),'nearestCurrentScalpWorld':guideTargets[i].tolist(),'currentSkinFace':int(gf[i]),'currentSkinTriangle':T[gf[i]].tolist(),'currentBC':gb[i].tolist(),'sourceSeedDistanceM':float(gg[i]),'sourceVolumeFitResidualM':float(fitError[i])} for i in failedIDs]
save('diagnostic-reopened-domains.json',{'UTC':stamp(),'originalFailedScriptSHA256':scriptSHA,'originalGuardM':.035,'failedGuides':len(failedIDs),'allGuideCount':418,'failedRows':rows,'rootCorrespondenceRejectedBeforeAnyNewHairEmission':True,'noSourceGuideOrFailedDomainDropped':True,'diagnosticMinimumReproductionOnly':True,'noClaimOfAnatomicallyQualifiedNearestTargets':True,'originalClockNotReset':True})
np.savez_compressed(E/'diagnostic-reopened-lineage.npz',sourceGuideRoots=guideRoots.astype('f4'),sourceGuideSeeds=guideSeeds.astype('f4'),currentTargets=guideTargets.astype('f4'),currentFaces=gf,currentBC=gb.astype('f4'),currentTriangles=T[gf],sourceSeedGapsM=gg.astype('f4'),failedSourceGuideIDs=failedIDs,quadraticCoefficients=coef,sourceCentre=sourceCentre,targetCentre=targetCentre,axisScale=scale)
collection=bpy.data.collections.new('AFN202_UNACCEPTED_SOURCE_CORRESPONDENCE_DIAGNOSTIC');s.collection.children.link(collection)
def pointmesh(name,points):
 me=bpy.data.meshes.new(name);me.from_pydata(points.tolist(),[],[]);me.update();ob=bpy.data.objects.new(name,me);collection.objects.link(ob);return ob
seed=pointmesh('AFN202_UNQUALIFIED_SOURCE_GUIDE_SEEDS',guideSeeds);target=pointmesh('AFN202_CURRENT_SCALP_REFERENCE_TARGETS',guideTargets)
for ob in [seed,target]:
 attr(ob.data,'AFN202_SOURCE_GUIDE_ID','INT',np.arange(418,dtype='i4'));attr(ob.data,'AFN202_FAILED_SOURCE_DOMAIN','BOOLEAN',(gg>=.035))
for k in range(3):attr(target.data,'AFN198_CAP_I'+str(k),'INT',T[gf,k]);attr(target.data,'AFN198_CAP_W'+str(k),'FLOAT',gb[:,k].astype('f4'))
attr(target.data,'AFN198_ROOT_BIND_WORLD','FLOAT_VECTOR',guideTargets.astype('f4'),'vector');target.modifiers.new('AFN202_ACTUAL_CURRENT_SKIN_REFERENCE_BINDING','NODES').node_group=previous.modifiers['AFN198_ACTUAL_GUIDE_CAP_BINDING'].node_group.copy()
# Literal complete source/current correspondences, not a visible groom.
me=bpy.data.meshes.new('AFN202_EXACT_UNQUALIFIED_SEED_TARGET_PAIRS');me.from_pydata(np.vstack([guideSeeds,guideTargets]).tolist(),[(i,i+418) for i in range(418)],[]);me.update();pairs=bpy.data.objects.new(me.name,me);collection.objects.link(pairs)
for ob in collection.objects:ob.hide_render=True;ob.hide_set(True)
np.savez_compressed(E/'current-diagnostic-control-baseline.npz',positions=guideTargets.astype('f4'))
old.hide_render=False;old.hide_set(False);previous.hide_render=True
# Diagnostic rendered witnesses show only failed pairs. Original Hair is
# hidden only for explicitly labelled diagnosis, restored before source save.
markers=[]
for tag,color in [('SOURCE',(1,.015,.01,1)),('TARGET',(.01,.7,.12,1))]:
 mat=bpy.data.materials.new('AFN202_DIAGNOSTIC_'+tag);mat.diffuse_color=color;mat.use_nodes=True;bs=mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=mat.node_tree.nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(bs.outputs['BSDF'],out.inputs['Surface']);bs.inputs['Base Color'].default_value=color;bs.inputs['Roughness'].default_value=.5
 for i in failedIDs:
  bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=.004,location=guideSeeds[i] if tag=='SOURCE' else guideTargets[i]);ob=bpy.context.object;ob.name='AFN202_DIAGNOSTIC_'+tag+'_GUIDE_'+str(int(i));ob.data.materials.append(mat);markers.append(ob)
lineMat=bpy.data.materials.new('AFN202_DIAGNOSTIC_FAILED_LINK');lineMat.diffuse_color=(1,.45,.01,1)
for i in failedIDs:
 cu=bpy.data.curves.new('AFN202_FAILED_REFERENCE_LINK_'+str(int(i)),'CURVE');cu.dimensions='3D';cu.bevel_depth=.001;sp=cu.splines.new('POLY');sp.points.add(1)
 for pt,p in zip(sp.points,[guideSeeds[i],guideTargets[i]]):pt.co=(*p,1)
 ob=bpy.data.objects.new(cu.name,cu);s.collection.objects.link(ob);cu.materials.append(lineMat);markers.append(ob)
old.hide_render=True;a.b.u.v.E=F
captures=[]
def capture(scene):
 captures.append({'UTC':stamp(),'loadedSource':bpy.data.filepath,'output':scene.render.filepath,'frame':scene.frame_current,'cameraMatrixWorld':[list(v) for v in scene.camera.matrix_world],'lens':scene.camera.data.lens,'exposure':scene.view_settings.exposure,'scope':'Explicit failed-root reference diagnostic, Hair hidden only to inspect source/current positions. Not a new complete-woman appearance candidate.'});save('diagnostic-render-pre-states.json',captures)
bpy.app.handlers.render_pre.append(capture)
for v in ['face','profile']:s.camera.data.type='PERSP';a.b.u.v.image('diagnostic-failed-source-current-domain',v)
bpy.app.handlers.render_pre.remove(capture)
for ob in markers:ob.hide_render=True;ob.hide_set(True)
old.hide_render=False;previous.hide_render=True
s.camera.matrix_world=Matrix(captures[0]['cameraMatrixWorld']);s.camera.data.lens=captures[0]['lens'];s.camera.data.type='PERSP'
for f in F.glob('matched-diagnostic-*.png'):shutil.copyfile(f,E/f.name)
for f in E.glob('original-cc0-short-reference-*.png'):shutil.copyfile(f,F/f.name)
OUTPUT=F/'aevrynd-female-next-r0202-rejected-correspondence-diagnostic.blend';OUT=A/'assets-source/aevrynd-character/female-next/r0202-source'/OUTPUT.name;OUT.parent.mkdir(parents=True,exist_ok=True);assert not OUT.exists();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),compress=True);shutil.copyfile(OUTPUT,OUT)
assert sha(OUTPUT)==sha(OUT) and protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected}
save('diagnostic-build-summary.json',{'UTC':stamp(),'output':str(OUT),'userReviewSource':str(OUTPUT),'sha256':sha(OUT),'bytes':OUT.stat().st_size,'actualSkin':skin.name,'actualTargetControl':target.name,'actualSourceReference':seed.name,'actualPairs':pairs.name,'allSevenRawMeshUVSignaturesUnchanged':protected,'controlCount':418,'sourceDomainFailedCount':len(failedIDs),'sourceDomainMaximumM':float(gg.max()),'originalGuardM':.035,'completeHairstyleCandidates':0,'newHairCurvesEmitted':0,'originalHairRestoredBeforeSave':True,'diagnosticOnlyNotAppearanceResult':True,'sourceSavedThroughFDriveOnlyAndCopiedToFHostedNTFS':True,'elapsedJobSeconds':time.time()-tick})
print('R202_FAILED_DOMAIN_REOPENABLE_DIAGNOSTIC_SAVED',json.dumps({'failedGuides':len(failedIDs),'maxSeedM':float(gg.max()),'source':str(OUTPUT)}),flush=True)