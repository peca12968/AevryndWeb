"""Own current-scalp regional swept-path construction; no demo asset import."""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,hashlib,importlib.util,shutil
from mathutils import Matrix
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);E=A/'evidence/character-female-next/r0211-complete-regional-lock-foundation';F=Path('F:/AevryndEvidence/r0211-complete-regional-lock-foundation');t=json.loads((E/'before.json').read_text('utf-8'));tick=time.time()
def sha(f):return hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
def digest(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,d):(E/n).write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
assert sha(t['source'])==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);spec=importlib.util.spec_from_file_location('r211base',A/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);a=m.a;h=m.h;old=bpy.data.objects[a.FIXED[1]];skin=bpy.data.objects[a.FIXED[0]];previous=bpy.data.objects['AFN210_ACTUAL_NATIVE_WHOLE_PATH_PART_GROOM'];oldBirths=bpy.data.objects['AFN210_CURRENT_SKIN_OWNED_PART_BIRTHS'];protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};oldRaw=h.arr(previous.data.position_data,'vector',4032,3).reshape(252,16,3);roots=oldRaw[:,0].copy();birthRaw=h.arr(oldBirths.data.vertices,'co',10191,3)
def sections(R):
 angle=np.arctan2(R[:,0],R[:,1]+.025);side=(R[:,0]>=0).astype('i4');labels=np.full(len(R),6,'i4');ab=np.abs(angle);labels[ab>2.15]=side[ab>2.15];labels[(ab>1)&(ab<=2.15)]=2+side[(ab>1)&(ab<=2.15)];labels[(ab>.32)&(ab<=1)]=4+side[(ab>.32)&(ab<=1)];return labels,angle
gd,ga=sections(roots);bd,ba=sections(birthRaw);pre,poff=m.curveworld(previous);de=previous.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;preIDs=h.arr(de.attributes['AFN198_PERSISTENT_BIRTH_ID'].data,'value',10191,dtype='i4');preUV=h.arr(de.attributes['surface_uv_coordinate'].data,'vector',10191,2);preClosest=h.arr(de.attributes['AFN198_ACTUAL_CLOSEST_GUIDE_ID'].data,'value',10191,dtype='i4');crossBefore=int(np.sum(gd[preClosest]!=bd[preIDs]));assert all(np.sum(gd==k)>=2 for k in range(7));save('changed-premise-before-authoring.json',{'UTC':stamp(),'previousActualDisplayedCrossNewAnatomicalPatchGuideAffiliations':crossBefore,'previousActualGuideAffiliationMeasuredNotAssumed':True,'newGuidePatchCounts':np.bincount(gd,minlength=7).tolist(),'newBirthPatchCounts':np.bincount(bd,minlength=7).tolist(),'newRegionalTopologyNot203Nearest22PathBankOr210BinarySplit':True,'supportBudgetOriginalDeadline':t['supportDeadlineUTC'],'withinOriginalSupportDeadline':datetime.datetime.now(datetime.timezone.utc)<=datetime.datetime.fromisoformat(t['supportDeadlineUTC']),'genericLearningOnlyNoBystedtDataImported':True})
# Independently authored world-space patch spines, with posterior bridge
# across the sagittal plane. Free lengths are rebuilt, not held from210.
leftFront=np.array([[-.026,-.091,1.553],[-.041,-.106,1.572],[-.073,-.116,1.543],[-.088,-.110,1.503],[-.092,-.098,1.455],[-.103,-.077,1.404],[-.085,-.067,1.353]])
leftSide=np.array([[-.065,-.027,1.531],[-.084,-.029,1.550],[-.103,-.023,1.515],[-.110,-.013,1.474],[-.108,.005,1.433],[-.107,.026,1.388],[-.087,.023,1.340]])
leftRear=np.array([[-.044,.030,1.528],[-.057,.056,1.546],[-.079,.079,1.511],[-.088,.087,1.468],[-.085,.086,1.425],[-.073,.088,1.378],[-.055,.069,1.333]])
bridge=np.array([[0,.049,1.521],[.003,.076,1.535],[.001,.098,1.502],[-.002,.105,1.462],[.001,.107,1.415],[.002,.098,1.369],[-.004,.077,1.329]])
def mirrored(C,dx,dz):
 B=C.copy();B[:,0]*=-1;B[2:,1]+=dx;B[2:,2]+=dz;return B
controls=np.array([leftFront,mirrored(leftFront,.009,.005),leftSide,mirrored(leftSide,.006,.004),leftRear,mirrored(leftRear,.003,.003),bridge]);names=['L_FACE_FRAME','R_FACE_FRAME','L_TEMPORAL_SIDE','R_TEMPORAL_SIDE','L_OCCIPITAL','R_OCCIPITAL','POSTERIOR_CONTINUOUS_BRIDGE'];K=64;u=np.linspace(0,1,K);smooth=u*u*(3-2*u)
def spline(C,u):
 # C1 Catmull-Rom, all patches use the same fixed construction.
 P=np.vstack([2*C[0]-C[1],C,2*C[-1]-C[-2]]);f=u*(len(C)-1);ix=np.minimum(f.astype(int),len(C)-2);v=(f-ix)[:,None];P0,P1,P2,P3=P[ix],P[ix+1],P[ix+2],P[ix+3];return .5*((2*P1)+(-P0+P2)*v+(2*P0-5*P1+4*P2-P3)*v*v+(-P0+3*P1-3*P2+P3)*v*v*v)
authored=[]
for i,root in enumerate(roots):
 k=int(gd[i]);C=controls[k];Q=spline(C,u);spread=root-C[0];Q+=spread[None,:]*(1-smooth[:,None]);angle=ga[i];height=root[2];local=(angle if k==6 else abs(angle));bundle=np.floor((local+.35)*7)/7;phase=8.5*bundle+float(k)*.83
 # Spatially coherent medium bundles in the lower free volume; no per-fibre
 # random noise, root pushing or reuse of failed outer envelope.
 wave=np.sin(2*np.pi*(1.35*u)+phase)-np.sin(phase);amp=.0065*smooth*np.sin(np.pi*u*.8);normal=np.array([np.cos(angle),-np.sin(angle),0]);Q+=wave[:,None]*amp[:,None]*normal[None,:];Q[:,2]+=(height-C[0,2])*.27*smooth;Q[:,0]+=np.sin(phase)*.004*smooth;Q[0]=root;authored.append(Q)
P=np.array(authored,dtype='f4');assert np.isfinite(P).all() and np.array_equal(P[:,0],roots)
hair=previous.copy();hair.name='AFN211_ACTUAL_REGION_OWNED_WHOLE_REST_GROOM';s.collection.objects.link(hair);cu=bpy.data.hair_curves.new('AFN211_252_64_POINT_REGION_OWNED_NATIVE_GUIDES');cu.add_curves([K]*252);cu.position_data.foreach_set('vector',P.ravel());cu.surface=previous.data.surface;cu.surface_uv_map=previous.data.surface_uv_map
for at in previous.data.attributes:
 if at.name in ['position','curve_type','radius','.selection']:continue
 if at.data_type not in ['INT','FLOAT','FLOAT_VECTOR','FLOAT2','BOOLEAN']:continue
 prop='vector' if at.data_type in ['FLOAT_VECTOR','FLOAT2'] else 'value';components=3 if at.data_type=='FLOAT_VECTOR' else 2 if at.data_type=='FLOAT2' else 1;count=len(at.data);values=h.arr(at.data,prop,count,components,dtype='i4' if at.data_type in ['INT','BOOLEAN'] else 'f4')
 if at.domain=='POINT':values=np.repeat(values.reshape(252,16,components)[:,0],K,axis=0) if components>1 else np.repeat(values.reshape(252,16)[:,0],K)
 elif at.domain!='CURVE':continue
 dest=cu.attributes.new(at.name,at.data_type,at.domain);dest.data.foreach_set(prop,values.ravel())
hair.data=cu
for md in hair.modifiers:
 if md.type=='NODES':md.node_group=md.node_group.copy()
births=oldBirths.copy();births.data=oldBirths.data.copy();births.name='AFN211_CURRENT_SKIN_REGION_OWNED_BIRTHS';s.collection.objects.link(births)
for ob,domain,values in [(hair,'CURVE',gd),(births,'POINT',bd)]:
 at=ob.data.attributes.new('AFN211_PERSISTENT_ANATOMICAL_REGION','INT',domain);at.data.foreach_set('value',values)
gen=hair.modifiers['AFN198_ACTUAL_SURFACE_CHILD_GENERATOR'];count=0
for node in gen.node_group.nodes:
 if node.bl_idname=='GeometryNodeObjectInfo':node.inputs['Object'].default_value=births
 if node.bl_idname=='GeometryNodeInputNamedAttribute' and node.inputs['Name'].default_value=='AFN210_ACTUAL_ANATOMICAL_PART_SIDE':node.inputs['Name'].default_value='AFN211_PERSISTENT_ANATOMICAL_REGION';count+=1
assert count==2;gen.show_viewport=gen.show_render=True;previous.hide_render=True;hair.hide_render=False;hair.hide_set(False);hair.data.update_tag();bpy.context.view_layer.update();actual,off=m.curveworld(hair);de=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;ids=h.arr(de.attributes['AFN198_PERSISTENT_BIRTH_ID'].data,'value',len(off),dtype='i4');uv=h.arr(de.attributes['surface_uv_coordinate'].data,'vector',len(off),2);closest=h.arr(de.attributes['AFN198_ACTUAL_CLOSEST_GUIDE_ID'].data,'value',len(off),dtype='i4');assert len(off)==10191 and np.array_equal(np.diff(np.r_[off,len(actual)]),np.full(10191,K)) and np.array_equal(np.sort(ids),np.arange(10191));assert np.array_equal(uv[np.argsort(ids)],preUV[np.argsort(preIDs)]);crossAfter=int(np.sum(gd[closest]!=bd[ids]));assert crossAfter==0;rootError=float(np.linalg.norm(actual[off][np.argsort(ids)]-pre[poff][np.argsort(preIDs)],axis=1).max());assert rootError<3e-6 and protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected};canonical=actual.reshape(10191,K,3)[np.argsort(ids)];np.savez_compressed(E/'regional-whole-rest-unique-construction.npz',guideWorld=P,guideRegion=gd,birthRegion=bd,birthIDs=ids,birthUV=uv,authorPatchControls=controls,authorPatchNames=np.array(names),oldGuideRoots=roots)
save('complete-regional-rest-construction.json',{'UTC':stamp(),'actualHair':hair.name,'actualBirths':births.name,'actualSkin':skin.name,'allSevenRawMeshUVSignaturesUnchanged':protected,'actualGuideIDs':252,'guidePointsPerCurve':K,'actualCurves':10191,'actualPoints':len(actual),'anatomicalPatches':names,'guidePatchCounts':np.bincount(gd,minlength=7).tolist(),'birthPatchCounts':np.bincount(bd,minlength=7).tolist(),'actualCrossPatchGuideAffiliationsBefore':crossBefore,'actualCrossPatchGuideAffiliationsAfter':crossAfter,'rootMaximumChangeM':rootError,'canonicalDisplayedFloat32WorldSHA256':digest(canonical),'canonicalUVSHA256':digest(uv[np.argsort(ids)]),'rawGuideSHA256':digest(P),'allCurrentBirthIDsUVRetained':True,'rawGuides64PointsCompleteFreePathsRebuilt':True,'noImportedBystedtGeometryNodesOrMaterial':True,'fixedMaterialRadiusDensityLightingRetained':True,'wholeFormContactAndNaturalMotionUnaccepted':True,'secondsBeforePreview':time.time()-tick})
captures=[]
def capture(scene):
 captures.append({'UTC':stamp(),'loadedSource':bpy.data.filepath,'output':scene.render.filepath,'frame':scene.frame_current,'cameraMatrixWorld':[list(v) for v in scene.camera.matrix_world],'lens':scene.camera.data.lens,'cameraType':scene.camera.data.type,'exposure':scene.view_settings.exposure,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'samples':scene.cycles.samples,'seed':scene.cycles.seed,'newHairVisible':not hair.hide_render,'originalHairVisible':not old.hide_render,'currentGeneratorViewport':gen.show_viewport,'currentGeneratorRender':gen.show_render,'captureStateNotRenderDepsgraphProof':True});save('actual-render-pre-capture-states.json',captures)
bpy.app.handlers.render_pre.append(capture);a.b.u.v.E=F;hair.hide_render=True;old.hide_render=False
for v in ['face','body-face']:s.camera.data.type='PERSP';a.b.u.v.image('baseline-original-working-hair',v)
old.hide_render=True;hair.hide_render=False
for v in ['face','body-face','oblique','profile','back']:s.camera.data.type='PERSP';a.b.u.v.image('regional-owned-whole-rest-groom',v)
bpy.app.handlers.render_pre.remove(capture);s.camera.matrix_world=Matrix(captures[2]['cameraMatrixWorld']);s.camera.data.lens=captures[2]['lens'];s.camera.data.type='PERSP'
for f in F.glob('matched-*.png'):shutil.copyfile(f,E/f.name)
output=F/'aevrynd-female-next-r0211-region-owned-whole-rest-groom.blend';out=A/'assets-source/aevrynd-character/female-next/r0211-source'/output.name;out.parent.mkdir();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True);shutil.copyfile(output,out);save('build-summary.json',{'UTC':stamp(),'output':str(out),'userReviewSource':str(output),'sha256':sha(out),'bytes':out.stat().st_size,'actualHair':hair.name,'actualSkin':skin.name,'actualBirths':births.name,'actualCurves':10191,'actualPoints':len(actual),'oneCompleteCandidate':True,'elapsedJobSeconds':time.time()-tick,'unaccepted':True});print('R211_ACTUAL_COMPLETE_REGION_OWNED_GROOM_SAVED',flush=True)
