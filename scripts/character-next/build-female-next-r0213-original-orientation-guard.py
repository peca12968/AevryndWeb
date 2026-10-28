"""Measured semantic section cage; own complete current native guide/births.
No206 cap-disk anchors,212 grid, analytic hair-spine bank or frozen free tips.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,hashlib,importlib.util,shutil
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);E=A/'evidence/character-female-next/r0213-anatomical-section-cage';F=Path('F:/AevryndEvidence/r0213-anatomical-section-cage');t=json.loads((E/'before.json').read_text());tick=time.time();n=np.load(E/'actual-anatomical-section-cage.npz');SZ=n['sourceZ'];TZ=n['targetZ'];SR=n['sourceRings'];TR=n['targetRings'];SV=n['sourceBodyWorld'];ST=n['sourceBodyTriangles'];sourceData=np.load(E.parent/'r0212-complete-artist-volume-foundation/source-operative-complete-rest-guide-data.npz');S=sourceData['straight_hair_to_shoulder_operativeP'].astype('f8').reshape(252,16,3);spec=importlib.util.spec_from_file_location('r213base',A/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);a=m.a;h=m.h
def sha(f):return hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
def digest(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(name,q):(E/name).write_bytes((json.dumps(q,ensure_ascii=False,indent=2)+'\n').encode())
def sample(q):
 q=np.atleast_2d(q);z=q[:,2];i=np.clip(np.searchsorted(SZ,z,side='right')-1,0,len(SZ)-2);u=(z-SZ[i])/(SZ[i+1]-SZ[i]);v=np.clip(u,0,1);sb=SR[i]*(1-v[:,None])+SR[i+1]*v[:,None];tb=TR[i]*(1-v[:,None])+TR[i+1]*v[:,None];out=q.copy();out[:,2]=TZ[i]+u*(TZ[i+1]-TZ[i]);sx=np.where(q[:,0]<0,sb[:,0],sb[:,1]);tx=np.where(q[:,0]<0,tb[:,0],tb[:,1]);out[:,0]=q[:,0]*tx/sx;sc=(sb[:,2]+sb[:,3])/2;tc=(tb[:,2]+tb[:,3])/2;sy=np.where(q[:,1]<sc,sb[:,2]-sc,sb[:,3]-sc);ty=np.where(q[:,1]<sc,tb[:,2]-tc,tb[:,3]-tc);out[:,1]=tc+(q[:,1]-sc)*ty/sy;return out
assert sha(t['source'])==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);skin=bpy.data.objects[a.FIXED[0]];old=bpy.data.objects[a.FIXED[1]];previous=bpy.data.objects['AFN211_ACTUAL_REGION_OWNED_WHOLE_REST_GROOM'];oldBirths=bpy.data.objects['AFN211_CURRENT_SKIN_REGION_OWNED_BIRTHS'];protected={name:a.rawsig(bpy.data.objects[name]) for name in a.FIXED+a.MOVING};W,T=a.geometry(skin);lineage=np.load(E.parent/'r0198-native-birth-owned-scalp/native-surface-birth-lineage.npz');sf=lineage['actualCurrentScalpFaces'];sourceMask=np.load(E.parent/'r0198-native-birth-owned-scalp/source-guide-and-cap-construction.npz')['sourceCapMask'];sourceFaces=np.flatnonzero(sourceMask);sourceTree=BVHTree.FromPolygons(SV.tolist(),ST[sourceFaces].tolist(),all_triangles=True);targetTree=BVHTree.FromPolygons(W.tolist(),T[sf].tolist(),all_triangles=True)
def bary(q,tri):
 v=np.linalg.lstsq(np.column_stack([tri[1]-tri[0],tri[2]-tri[0]]),q-tri[0],rcond=None)[0];bc=np.clip(np.array([1-v.sum(),*v]),0,1);return bc/bc.sum()
sourceLogical=[];sourceNormals=[];sourceBirthGap=[]
for q in S[:,0]:
 hit,no,i,gap=sourceTree.find_nearest(Vector(q));sourceLogical.append(hit);sourceNormals.append(no);sourceBirthGap.append(gap)
sourceLogical=np.array(sourceLogical);sourceNormals=np.array(sourceNormals);assert max(sourceBirthGap)<.002;sourceWholeCorrection=sourceLogical-S[:,0];S+=sourceWholeCorrection[:,None,:];C=sample(S.reshape(-1,3)).reshape(252,16,3);eps=1e-5;sp=S.reshape(-1,3);J=np.stack([(sample(sp+np.eye(3)[j]*eps)-sample(sp-np.eye(3)[j]*eps))/(2*eps) for j in range(3)],axis=2);det=np.linalg.det(J);assert det.min()>.05
logical=[];normal=[];gf=[];gbc=[];seedGap=[];normalDot=[];Q=[]
def rotation(a,b):
 a=a/np.linalg.norm(a);b=b/np.linalg.norm(b);v=np.cross(a,b);c=float(a@b);assert c>-.99;K=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]]);return np.eye(3)+K+K@K/(1+c)
for i,q in enumerate(C[:,0]):
 hit,no,fi,gap=targetTree.find_nearest(Vector(q));f=int(sf[fi]);bc=bary(np.array(hit),W[T[f]]);base=bc@W[T[f]];no=np.cross(W[T[f,1]]-W[T[f,0]],W[T[f,2]]-W[T[f,0]]);no/=np.linalg.norm(no);transformed=np.linalg.solve(J[i*16].T,sourceNormals[i]);transformed/=np.linalg.norm(transformed);dot=float(transformed@no);normalDot.append(dot);R=rotation(transformed,no);shaft=base+no*.000102;Q.append((C[i]-C[i,0])@R.T+shaft);logical.append(base);normal.append(no);gf.append(f);gbc.append(bc);seedGap.append(gap)
logical=np.array(logical);normal=np.array(normal);gf=np.array(gf,'i4');gbc=np.array(gbc);Q=np.array(Q,'f4');premise={'UTC':stamp(),'sourceActualRootToCapMaximumM':max(sourceBirthGap),'sourceCompleteGuideTranslationBeforeCageMaximumM':float(np.linalg.norm(sourceWholeCorrection,axis=1).max()),'cageSourceTargetKnotsActualSkinSectionEvidence':str(E/'anatomical-section-measurement.json'),'old206DiskAnchorsAnd212GridUnused':True,'cageSampledCompleteGuideJacobianDeterminantRange':[float(det.min()),float(det.max())],'cageTriangularPositiveOrientationConstruction':'Strictly increasing semantic z; independently positive left/right x and front/back y scale at every interpolated section. This is a piecewise section-cage orientation statement, not contact or post-attachment global injectivity.','cageToActualCurrentScalpSeedDistanceQuantilesM':np.quantile(seedGap,[0,.5,.9,1]).tolist(),'originalSeedCoverageGuardM':.035,'transformedSourceNormalDotActualTargetNormalQuantiles':np.quantile(normalDot,[0,.5,.9,1]).tolist(),'newWholeGuideRigidSurfaceAttachmentAfterWholeCage':'Entire16point cage-deformed guide rotates/translates into measured currentSkin root frame, including all tips. No root-only correction/frozen free lengths, no failed212map snap/rescue.','wholeFreeGuideDisplacementQuantilesM':np.quantile(np.linalg.norm(Q-S,axis=2)[:,1:],[0,.5,.9,1]).tolist(),'all252GuidesRetained':True,'originalSupportDeadlineUTC':t['supportDeadlineUTC'],'withinOriginalSupportDeadline':datetime.datetime.now(datetime.timezone.utc)<=datetime.datetime.fromisoformat(t['supportDeadlineUTC'])};save('actual-section-cage-before-guards.json',premise);assert max(seedGap)<.035 and min(normalDot)>0,'Anatomical section-cage seed coverage/orientation fails'
# Independent same-count source-area births, same whole cage and actual Skin.
N=10191;rng=np.random.default_rng(213701);tri=SV[ST[sourceFaces]];centres=tri.mean(1);areas=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)/2;seedIDs=lineage['childSamplingSeedGuideIDs'];seeds=[]
for gi in seedIDs:
 eligible=np.flatnonzero(np.linalg.norm(centres-sourceLogical[gi],axis=1)<.010)
 if not len(eligible):eligible=np.array([int(sourceTree.find_nearest(Vector(sourceLogical[gi]))[2])])
 i=int(rng.choice(eligible,p=areas[eligible]/areas[eligible].sum()));x,y=rng.random(2);sq=np.sqrt(x);bc=np.array([1-sq,sq*(1-y),sq*y]);seeds.append(bc@tri[i])
mappedSeeds=sample(np.array(seeds));bf=[];bbc=[];bl=[];bn=[];birthGap=[]
for q in mappedSeeds:
 hit,no,i,gap=targetTree.find_nearest(Vector(q));f=int(sf[i]);bc=bary(np.array(hit),W[T[f]]);base=bc@W[T[f]];no=np.cross(W[T[f,1]]-W[T[f,0]],W[T[f,2]]-W[T[f,0]]);no/=np.linalg.norm(no);bf.append(f);bbc.append(bc);bl.append(base);bn.append(no);birthGap.append(gap)
assert max(birthGap)<.035;bf=np.array(bf,'i4');bbc=np.array(bbc);bl=np.array(bl);bn=np.array(bn);shaft=bl+bn*.000102;evskin=skin.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;evskin.calc_loop_triangles();loops=np.array([z.loops[:] for z in evskin.loop_triangles]);uvName='AngelicaOriginalUV';uvData=h.arr(evskin.uv_layers[uvName].data,'uv',len(evskin.uv_layers[uvName].data),2)[loops];guv=np.einsum('ni,nij->nj',gbc,uvData[gf]);buv=np.einsum('ni,nij->nj',bbc,uvData[bf]);assert len(np.unique(buv.astype('f4'),axis=0))==N
hair=previous.copy();hair.name='AFN213_ACTUAL_SECTION_CAGE_ARTIST_NATIVE_GROOM';s.collection.objects.link(hair);cu=bpy.data.hair_curves.new('AFN213_252_COMPLETE_CURRENT_ATTACHED_ARTIST_GUIDES');cu.add_curves([16]*252);cu.position_data.foreach_set('vector',Q.ravel());cu.surface=skin;cu.surface_uv_map=uvName;hair.data=cu;births=oldBirths.copy();me=bpy.data.meshes.new('AFN213_10191_CURRENT_SECTION_CAGE_BIRTHS');me.from_pydata(shaft.tolist(),[],[]);me.update();births.data=me;births.name='AFN213_CURRENT_SKIN_SECTION_CAGE_BIRTHS';s.collection.objects.link(births)
def attr(data,name,typ,domain,values,prop='value'):
 at=data.attributes.new(name,typ,domain);at.data.foreach_set(prop,np.asarray(values).ravel())
def binding(data,faces,bc,base,repeat):
 for k in range(3):attr(data,'AFN198_CAP_I'+str(k),'INT','POINT',np.repeat(T[faces,k],repeat));attr(data,'AFN198_CAP_W'+str(k),'FLOAT','POINT',np.repeat(bc[:,k],repeat))
 attr(data,'AFN198_ROOT_BIND_WORLD','FLOAT_VECTOR','POINT',np.repeat(base,repeat,axis=0),'vector')
binding(cu,gf,gbc,logical,16);binding(me,bf,bbc,bl,1);attr(cu,'AFN198_GUIDE_UP','FLOAT_VECTOR','CURVE',normal,'vector');attr(cu,'surface_uv_coordinate','FLOAT2','CURVE',guv,'vector');attr(cu,'AFN209_PERSISTENT_NATIVE_GUIDE_ID','INT','CURVE',np.arange(252,dtype='i4'));attr(cu,'AFN213_CONNECTED_STYLE_DOMAIN','INT','CURVE',np.zeros(252,'i4'));attr(me,'AFN198_PERSISTENT_BIRTH_ID','INT','POINT',np.arange(N,dtype='i4'));attr(me,'surface_uv_coordinate','FLOAT2','POINT',buv,'vector');attr(me,'AFN213_CONNECTED_STYLE_DOMAIN','INT','POINT',np.zeros(N,'i4'))
for ob in [hair,births]:
 for md in ob.modifiers:
  if md.type=='NODES':md.node_group=md.node_group.copy()
gen=hair.modifiers['AFN198_ACTUAL_SURFACE_CHILD_GENERATOR'];groups=0
for node in gen.node_group.nodes:
 if node.bl_idname=='GeometryNodeObjectInfo':node.inputs['Object'].default_value=births
 if node.bl_idname=='GeometryNodeInputNamedAttribute' and node.inputs['Name'].default_value=='AFN211_PERSISTENT_ANATOMICAL_REGION':node.inputs['Name'].default_value='AFN213_CONNECTED_STYLE_DOMAIN';groups+=1
assert groups==2
# Reuse verified effective CC0 style inputs, never node interface defaults.
with bpy.data.libraries.load(t['artistInput'],link=False) as (fr,to):to.objects=['straight_hair_to_shoulder']
donor=to.objects[0];styleInputs=[]
for src in donor.modifiers:
 if src.name not in ['Curl Hair Curves','Hair Curves Noise','Frizz Hair Curves','Roll Hair Curves','Clump Hair Curves']:continue
 md=hair.modifiers.new('AFN213_SOURCE_EFFECTIVE_'+src.name,'NODES');md.node_group=src.node_group;fields={}
 for sock in src.node_group.interface.items_tree:
  if sock.item_type!='SOCKET' or sock.in_out!='INPUT' or sock.socket_type=='NodeSocketGeometry':continue
  left=getattr(src.properties.inputs,sock.identifier);right=getattr(md.properties.inputs,sock.identifier);saved={}
  for prop in left.bl_rna.properties:
   if prop.identifier in ['name','rna_type'] or prop.is_readonly or prop.type in ['POINTER','COLLECTION']:continue
   value=getattr(left,prop.identifier);setattr(right,prop.identifier,value);saved[prop.identifier]=list(value) if getattr(prop,'is_array',False) else value
  fields[sock.identifier]={'name':sock.name,'fields':saved}
 styleInputs.append({'modifier':md.name,'original':src.name,'effectiveInputs':fields})
assert len(styleInputs)==5;gen.show_viewport=gen.show_render=True;previous.hide_render=True;hair.hide_render=False;hair.hide_set(False);hair.data.update_tag();bpy.context.view_layer.update();actual,off=m.curveworld(hair);de=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;ids=h.arr(de.attributes['AFN198_PERSISTENT_BIRTH_ID'].data,'value',len(off),dtype='i4');uv=h.arr(de.attributes['surface_uv_coordinate'].data,'vector',len(off),2);assert np.array_equal(np.sort(ids),np.arange(N)) and np.array_equal(np.diff(np.r_[off,len(actual)]),np.full(N,61));rootError=float(np.linalg.norm(actual[off]-shaft[ids],axis=1).max());assert rootError<3e-6 and np.max(abs(uv-buv[ids]))<1e-6 and protected=={name:a.rawsig(bpy.data.objects[name]) for name in protected};np.savez_compressed(E/'section-cage-current-guide-birth-lineage.npz',guideWorld=Q,sourceRebornGuideWorld=S.astype('f4'),guideSkinFaces=gf,guideSkinBC=gbc.astype('f4'),guideSkinLogicalWorld=logical.astype('f4'),guideSkinNormals=normal.astype('f4'),birthSkinFaces=bf,birthSkinBC=bbc.astype('f4'),birthIDs=ids,birthUV=uv,guideSurfaceUV=guv.astype('f4'),birthLogicalWorld=bl.astype('f4'),birthShaftWorld=shaft.astype('f4'))
save('complete-section-cage-construction.json',{'UTC':stamp(),'actualHair':hair.name,'actualSkin':skin.name,'actualBirths':births.name,'actualGuideIDs':252,'guidePointsPerCurve':16,'actualCurves':N,'actualPoints':len(actual),'displayedPointsPerCurve':61,'allSevenRawMeshUVSignaturesUnchanged':protected,'sourceArtistInput':t['artistInput'],'sourceArtistInputSHA256':t['artistInputSHA256'],'sourceGuideFullRestPreservedThroughMeasuredCageAndWholeGuideFrameOperation':True,'noOldFailedFreePathsOrDiskFieldAnchors':True,'currentGuideAndBirthSkinOwnershipNewAndExplicit':True,'oldCurrentUVSitesNotClaimedPreserved':True,'allPersistentOwnBirthIDsComplete':True,'actualRootShaftMaximumErrorM':rootError,'canonicalDisplayedFloat32WorldSHA256':digest(actual.reshape(N,61,3)[np.argsort(ids)]),'canonicalUVSHA256':digest(uv[np.argsort(ids)]),'rawGuideSHA256':digest(Q),'sourceEffectiveStyleInputs':styleInputs,'currentFinalMaterialAndRadiusUnchanged':True,'fullAppearanceOperationFiniteSelfContinuousContactMotionRuntimeUnaccepted':True,'secondsBeforeCompletePreview':time.time()-tick})
captures=[]
def capture(scene):
 captures.append({'UTC':stamp(),'source':bpy.data.filepath,'output':scene.render.filepath,'frame':scene.frame_current,'cameraMatrixWorld':[list(x) for x in scene.camera.matrix_world],'lens':scene.camera.data.lens,'cameraType':scene.camera.data.type,'exposure':scene.view_settings.exposure,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'samples':scene.cycles.samples,'seed':scene.cycles.seed,'newHairVisible':not hair.hide_render,'originalHairVisible':not old.hide_render,'currentSkin':skin.name,'captureStateNotRenderDepsgraphProof':True});save('actual-render-pre-capture-states.json',captures)
bpy.app.handlers.render_pre.append(capture);a.b.u.v.E=F;hair.hide_render=True;old.hide_render=False
for v in ['face','body-face']:s.camera.data.type='PERSP';a.b.u.v.image('baseline-original-working-hair',v)
old.hide_render=True;hair.hide_render=False
for v in ['face','body-face','oblique','profile','back']:s.camera.data.type='PERSP';a.b.u.v.image('section-cage-artist-groom',v)
bpy.app.handlers.render_pre.remove(capture);s.camera.matrix_world=Matrix(captures[2]['cameraMatrixWorld']);s.camera.data.lens=captures[2]['lens'];s.camera.data.type='PERSP'
for file in F.glob('*.png'):shutil.copyfile(file,E/file.name)
output=F/'aevrynd-female-next-r0213-section-cage-artist-groom.blend';out=A/'assets-source/aevrynd-character/female-next/r0213-source'/output.name;out.parent.mkdir();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True);shutil.copyfile(output,out);assert out.stat().st_size<t['sourceBudgetBytes'];save('build-summary.json',{'UTC':stamp(),'output':str(out),'userReviewSource':str(output),'sha256':sha(out),'bytes':out.stat().st_size,'actualHair':hair.name,'actualSkin':skin.name,'actualBirths':births.name,'actualCurves':N,'actualPoints':len(actual),'oneCompleteCandidate':True,'elapsedJobSeconds':time.time()-tick,'unaccepted':True});print('R213_COMPLETE_SECTION_CAGE_ARTIST_CURRENT_GROOM_SAVED',flush=True)
