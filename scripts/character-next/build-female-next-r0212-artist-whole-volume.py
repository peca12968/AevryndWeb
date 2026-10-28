"""Complete CC0 operative rest through a regularized volumetric grid.
Current guide/birth identity comes from explicit anatomical cap charts.
No old failed free path, analytic spine, TPS or foreign scalp graft.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,hashlib,importlib.util,shutil
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);E=A/'evidence/character-female-next/r0212-complete-artist-volume-foundation';F=Path('F:/AevryndEvidence/r0212-complete-artist-volume-foundation');t=json.loads((E/'before.json').read_text('utf-8'));tick=time.time()
def sha(f):return hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
def digest(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,d):(E/n).write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
spec=importlib.util.spec_from_file_location('r212base',A/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);a=m.a;h=m.h;source=np.load(E/'source-operative-complete-rest-guide-data.npz');S=source['straight_hair_to_shoulder_operativeP'].astype('f8').reshape(252,16,3);assert np.array_equal(source['straight_hair_to_shoulder_operativeOffsets'],np.arange(252)*16);cap=np.load(E.parent/'r0206-operative-guide-anatomical-map/failed-operative-guide-cap-map-lineage.npz');sv=cap['sourceCapWorld'];st=cap['sourceCapTriangles'];suv=cap['sourceCapUV'];tv=cap['targetCapWorld'];tt=cap['targetCapTriangles'];tuv=cap['targetCapUV'];sb=cap['sourceBoundary'];tb=cap['targetBoundary'];sa=cap['sourceBoundaryAngles'];ta=cap['targetBoundaryAngles'];mapped=cap['volumeAnchorTargets'];assert sha(t['source'])==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);skin=bpy.data.objects[a.FIXED[0]];old=bpy.data.objects[a.FIXED[1]];previous=bpy.data.objects['AFN211_ACTUAL_REGION_OWNED_WHOLE_REST_GROOM'];oldBirths=bpy.data.objects['AFN211_CURRENT_SKIN_REGION_OWNED_BIRTHS'];protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};W,T=a.geometry(skin);lineage=np.load(E.parent/'r0198-native-birth-owned-scalp/native-surface-birth-lineage.npz');sf=lineage['actualCurrentScalpFaces'];assert np.max(abs(W[T[sf]]-tv[tt]))<3e-6
def uvhit(q,uvfaces):
 aa=uvfaces[:,0];v=uvfaces[:,1]-aa;w=uvfaces[:,2]-aa;r=q-aa;det=v[:,0]*w[:,1]-v[:,1]*w[:,0];valid=abs(det)>1e-15;b=np.full(len(det),-np.inf);c=b.copy();b[valid]=(r[valid,0]*w[valid,1]-r[valid,1]*w[valid,0])/det[valid];c[valid]=(v[valid,0]*r[valid,1]-v[valid,1]*r[valid,0])/det[valid];bc=np.column_stack([1-b-c,b,c]);ids=np.flatnonzero((bc.min(1)>=-1e-7)&valid);assert len(ids)>0,('UV outside anatomical cap',q.tolist());i=int(ids[0]);z=np.clip(bc[i],0,1);return i,z/z.sum()
def radial(q,angles,Buv):
 theta=np.arctan2(q[:,1],q[:,0]);theta=np.where(theta<-np.pi/2,theta+2*np.pi,theta);i=np.clip(np.searchsorted(angles,theta,side='right')-1,0,len(angles)-1);v=Buv[i];w=Buv[(i+1)%len(Buv)];d=np.column_stack([np.cos(theta),np.sin(theta)]);cross=lambda x,y:x[:,0]*y[:,1]-x[:,1]*y[:,0];return cross(v,w)/cross(d,w-v)
def target(q):
 q=np.atleast_2d(q);z=q*(radial(q,ta,tuv[tb])/radial(q,sa,suv[sb]))[:,None];fi=[];bc=[]
 for point in z:
  i,w=uvhit(point,tuv[tt]);fi.append(int(sf[i]));bc.append(w)
 fi=np.array(fi,'i4');bc=np.array(bc);return np.einsum('ni,nij->nj',bc,W[T[fi]]),fi,bc
tree=BVHTree.FromPolygons(sv.tolist(),st.tolist(),all_triangles=True);guideParam=[];sourceGaps=[];projectedSourceRoots=[]
for q in S[:,0]:
 hit,no,i,gap=tree.find_nearest(Vector(q));tri=sv[st[i]];uv=np.linalg.lstsq(np.column_stack([tri[1]-tri[0],tri[2]-tri[0]]),np.array(hit)-tri[0],rcond=None)[0];bc=np.array([1-uv.sum(),*uv]);guideParam.append(bc@suv[st[i]]);sourceGaps.append(gap);projectedSourceRoots.append(np.array(hit))
diagnosis=json.loads((E/'source-guide-ownership-single-diagnosis.json').read_text());assert max(sourceGaps)<.002;sourceWholePathBirthCorrection=np.array(projectedSourceRoots)-S[:,0];S+=sourceWholePathBirthCorrection[:,None,:];save('explicit-source-native-guide-rebirth.json',{'UTC':stamp(),'originalFailedSourcePointVsUVPremiseRetained':diagnosis,'originalGuideUVIsAffiliationNotPhysicalBirth':True,'newSourceBirthDefinition':'Own source guide births explicitly projected onto actual source cap before whole-volume transport. Full source guide translated by same measured <=1.201mm vector, not only root edited. Then every complete guide point undergoes current-head volumetric deformation.','maximumFullSourceGuideTranslationM':float(np.linalg.norm(sourceWholePathBirthCorrection,axis=1).max()),'original2mmSourceCapCoverageGuardNotRelaxed':True,'all252GuidesRetained':True,'appearanceAndContactsUnaccepted':True});guideLogical,gf,gbc=target(np.array(guideParam));gn=np.cross(W[T[gf,1]]-W[T[gf,0]],W[T[gf,2]]-W[T[gf,0]]);gn/=np.linalg.norm(gn,axis=1)[:,None];guideShaft=guideLogical+gn*.000102
# Regularized trilinear finite-volume displacement, matrix-free CG.
# One fixed grid/energy/guard configuration, no parameter search.
shape=np.array([24,24,40]);lo=np.minimum(S.reshape(-1,3).min(0),sv.min(0))-.025;hi=np.maximum(S.reshape(-1,3).max(0),sv.max(0))+.025;step=(hi-lo)/(shape-1);total=int(np.prod(shape));stride=np.array([shape[1]*shape[2],shape[2],1]);corners=np.array([[x,y,z] for x in [0,1] for y in [0,1] for z in [0,1]],'i4')
def stencil(q):
 f=(np.asarray(q)-lo)/step;i=np.clip(np.floor(f).astype('i4'),0,shape-2);u=f-i;idx=((i[:,None,:]+corners[None,:,:])*stride).sum(2);weights=np.prod(np.where(corners[None,:,:],u[:,None,:],1-u[:,None,:]),axis=2);assert weights.min()>-1e-9;return idx,weights
idx,weights=stencil(sv);displacement=mapped-sv;mean=displacement.mean(0);lam=.002;mu=.00001
def sample(x,ii=idx,ww=weights):return np.sum(x[ii]*ww[:,:,None],axis=1)
def transpose(y):
 out=np.zeros((total,3));np.add.at(out,idx.reshape(-1),(weights[:,:,None]*y[:,None,:]).reshape(-1,3));return out
def lap(x):
 g=x.reshape(*shape,3);out=np.zeros_like(g)
 for axis in range(3):
  aa=[slice(None)]*4;bb=aa.copy();aa[axis]=slice(1,None);bb[axis]=slice(None,-1);v=g[tuple(aa)]-g[tuple(bb)];out[tuple(aa)]+=v;out[tuple(bb)]-=v
 return out.reshape(total,3)
def mul(x):return transpose(sample(x))+lam*lap(x)+mu*x
rhs=transpose(displacement)+mu*mean;field=np.repeat(mean[None,:],total,axis=0);r=rhs-mul(field);direction=r.copy();rr=np.sum(r*r,axis=0);initial=np.sqrt(rr)
for iteration in range(700):
 ap=mul(direction);alpha=rr/np.maximum(np.sum(direction*ap,axis=0),1e-30);field+=direction*alpha;r-=ap*alpha;new=np.sum(r*r,axis=0)
 if np.sqrt(new).max()<1e-7:break
 direction=r+direction*(new/np.maximum(rr,1e-30));rr=new
def warp(q):
 ii,ww=stencil(q);return np.asarray(q)+sample(field,ii,ww)
anchorResidual=np.linalg.norm(warp(sv)-mapped,axis=1);Q=warp(S.reshape(-1,3)).reshape(252,16,3);rootResidual=guideLogical-Q[:,0];rootError=np.linalg.norm(rootResidual,axis=1);eps=1e-5;test=S.reshape(-1,3);J=np.stack([(warp(test+np.eye(3)[j]*eps)-warp(test-np.eye(3)[j]*eps))/(2*eps) for j in range(3)],axis=2);det=np.linalg.det(J);premise={'UTC':stamp(),'sourceStyle':'straight_hair_to_shoulder','actualCompleteSourceViewsInspected':['front','profile','back'],'originalSourceGuideFirstPointToCapMaximumM':max(sourceGaps),'newOwnSourceGuideBirthsOnActualCapNotOriginalUVIdentity':True,'gridShape':shape.tolist(),'gridUnknowns':total,'regularizerLaplacian':lam,'screen':mu,'CGIterations':iteration+1,'CGResidualMaximum':float(np.sqrt(new).max()),'capAnchorResidualQuantilesM':np.quantile(anchorResidual,[0,.5,.9,1]).tolist(),'operativeGuideRootResidualQuantilesM':np.quantile(rootError,[0,.5,.9,1]).tolist(),'sampledGuideJacobianDeterminantRange':[float(det.min()),float(det.max())],'fixedRootResidualGuardM':.003,'fixedSampledJacobianGuard':.05,'sampledJacobianNotFullInjectivityOrContactProof':True,'newVolumetricGridNotTPSRadialAffineOrRootOnlyGraft':True,'fullFreeGuidePointDisplacementQuantilesM':np.quantile(np.linalg.norm(Q-S,axis=2)[:,1:],[0,.5,.9,1]).tolist(),'allPriorFailedShapesUnused':True,'originalSupportDeadlineUTC':t['supportDeadlineUTC'],'withinOriginalSupportDeadline':datetime.datetime.now(datetime.timezone.utc)<=datetime.datetime.fromisoformat(t['supportDeadlineUTC'])};save('whole-volume-field-before-guard.json',premise);np.savez_compressed(E/'unique-whole-volume-grid.npz',field=field.astype('f4'),gridShape=shape,gridMinimum=lo,gridStep=step,sourceGuideWorld=S.astype('f4'),warpedGuideWorldBeforeAttachment=Q.astype('f4'),sourceGuideRootParam=np.array(guideParam),guideLogicalWorld=guideLogical.astype('f4'),guideSkinFaces=gf,guideSkinBC=gbc.astype('f4'));assert rootError.max()<.003 and det.min()>.05,'Fixed complete volume map cheap falsifier failed'
# Residual correction extends through each complete path after all points
# have undergone the volume deformation; this is not frozen free-length graft.
u=np.linspace(0,1,16);Q+=rootResidual[:,None,:]*(1-u[None,:,None]);Q+=gn[:,None,:]*.000102;Q[:,0]=guideShaft;Q=Q.astype('f4')
# Own source-cap area births transported through the same qualified cap map.
N=10191;seedIDs=lineage['childSamplingSeedGuideIDs'];rng=np.random.default_rng(212701);centres=sv[st].mean(1);areas=np.linalg.norm(np.cross(sv[st[:,1]]-sv[st[:,0]],sv[st[:,2]]-sv[st[:,0]]),axis=1)/2;birthParam=[]
for gi in seedIDs:
 eligible=np.flatnonzero(np.linalg.norm(centres-S[gi,0],axis=1)<.010)
 if not len(eligible):eligible=np.array([int(tree.find_nearest(Vector(S[gi,0]))[2])])
 f=int(rng.choice(eligible,p=areas[eligible]/areas[eligible].sum()));x,y=rng.random(2);sq=np.sqrt(x);bc=np.array([1-sq,sq*(1-y),sq*y]);birthParam.append(bc@suv[st[f]])
logical,bf,bbc=target(np.array(birthParam));bn=np.cross(W[T[bf,1]]-W[T[bf,0]],W[T[bf,2]]-W[T[bf,0]]);bn/=np.linalg.norm(bn,axis=1)[:,None];shaft=logical+bn*.000102;evskin=skin.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;evskin.calc_loop_triangles();loops=np.array([z.loops[:] for z in evskin.loop_triangles]);uvName='AngelicaOriginalUV';uvData=h.arr(evskin.uv_layers[uvName].data,'uv',len(evskin.uv_layers[uvName].data),2)[loops];guv=np.einsum('ni,nij->nj',gbc,uvData[gf]);buv=np.einsum('ni,nij->nj',bbc,uvData[bf]);assert len(np.unique(buv.astype('f4'),axis=0))==N
hair=previous.copy();hair.name='AFN212_ACTUAL_ARTIST_WHOLE_VOLUME_NATIVE_GROOM';s.collection.objects.link(hair);cu=bpy.data.hair_curves.new('AFN212_252_CURRENT_BOUND_FULL_ARTIST_GUIDES');cu.add_curves([16]*252);cu.position_data.foreach_set('vector',Q.ravel());cu.surface=skin;cu.surface_uv_map=uvName;hair.data=cu
births=oldBirths.copy();me=bpy.data.meshes.new('AFN212_10191_CURRENT_CHART_MAPPED_BIRTHS');me.from_pydata(shaft.tolist(),[],[]);me.update();births.data=me;births.name='AFN212_CURRENT_SKIN_CHART_OWNED_BIRTHS';s.collection.objects.link(births)
def attr(data,name,typ,domain,values,prop='value'):
 at=data.attributes.new(name,typ,domain);at.data.foreach_set(prop,np.asarray(values).ravel())
def binding(data,faces,bc,base,repeat):
 for k in range(3):attr(data,'AFN198_CAP_I'+str(k),'INT','POINT',np.repeat(T[faces,k],repeat));attr(data,'AFN198_CAP_W'+str(k),'FLOAT','POINT',np.repeat(bc[:,k],repeat))
 attr(data,'AFN198_ROOT_BIND_WORLD','FLOAT_VECTOR','POINT',np.repeat(base,repeat,axis=0),'vector')
binding(cu,gf,gbc,guideLogical,16);binding(me,bf,bbc,logical,1);attr(cu,'AFN198_GUIDE_UP','FLOAT_VECTOR','CURVE',gn,'vector');attr(cu,'surface_uv_coordinate','FLOAT2','CURVE',guv,'vector');attr(cu,'AFN209_PERSISTENT_NATIVE_GUIDE_ID','INT','CURVE',np.arange(252,dtype='i4'));attr(cu,'AFN212_CONNECTED_STYLE_DOMAIN','INT','CURVE',np.zeros(252,'i4'));attr(me,'AFN198_PERSISTENT_BIRTH_ID','INT','POINT',np.arange(N,dtype='i4'));attr(me,'surface_uv_coordinate','FLOAT2','POINT',buv,'vector');attr(me,'AFN212_CONNECTED_STYLE_DOMAIN','INT','POINT',np.zeros(N,'i4'))
for ob in [hair,births]:
 for md in ob.modifiers:
  if md.type=='NODES':md.node_group=md.node_group.copy()
gen=hair.modifiers['AFN198_ACTUAL_SURFACE_CHILD_GENERATOR'];groups=0
for node in gen.node_group.nodes:
 if node.bl_idname=='GeometryNodeObjectInfo':node.inputs['Object'].default_value=births
 if node.bl_idname=='GeometryNodeInputNamedAttribute' and node.inputs['Name'].default_value=='AFN211_PERSISTENT_ANATOMICAL_REGION':node.inputs['Name'].default_value='AFN212_CONNECTED_STYLE_DOMAIN';groups+=1
assert groups==2;gen.show_viewport=gen.show_render=True;previous.hide_render=True;hair.hide_render=False;hair.hide_set(False);hair.data.update_tag();bpy.context.view_layer.update();actual,off=m.curveworld(hair);de=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;ids=h.arr(de.attributes['AFN198_PERSISTENT_BIRTH_ID'].data,'value',len(off),dtype='i4');uv=h.arr(de.attributes['surface_uv_coordinate'].data,'vector',len(off),2);assert np.array_equal(np.sort(ids),np.arange(N)) and np.array_equal(np.diff(np.r_[off,len(actual)]),np.full(N,16));rootActualError=float(np.linalg.norm(actual[off]-shaft[ids],axis=1).max());assert rootActualError<3e-6 and np.max(abs(uv-buv[ids]))<1e-6 and protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected};np.savez_compressed(E/'current-whole-volume-groom-lineage.npz',guideWorld=Q,guideSkinFaces=gf,guideSkinBC=gbc.astype('f4'),birthSkinFaces=bf,birthSkinBC=bbc.astype('f4'),birthIDs=ids,birthUV=uv,guideSurfaceUV=guv.astype('f4'),birthLogicalWorld=logical.astype('f4'),birthShaftWorld=shaft.astype('f4'))
save('complete-artist-volume-construction.json',{'UTC':stamp(),'actualHair':hair.name,'actualSkin':skin.name,'actualBirths':births.name,'actualGuideIDs':252,'guidePointsPerCurve':16,'actualCurves':N,'actualPoints':len(actual),'allSevenRawMeshUVSignaturesUnchanged':protected,'sourceRestStyle':'CC0 Tomas Klecer straight_hair_to_shoulder operative16point guides','sourceInputSnapshot':json.loads((E/'source-input-snapshot.json').read_text()),'wholeVolumeFieldEvidence':str(E/'whole-volume-field-before-guard.json'),'allFreePathsVolumetricallyDeformedNotFrozen':True,'postFieldResidualCorrectionMaximumM':float(rootError.max()),'currentBirthsNewAnatomicalSourceToCurrentChartConstructionNotOld198Sites':True,'oldCurrentUVLocationsNotClaimedPreserved':True,'persistentOwnBirthIDsComplete':True,'actualRootShaftMaximumErrorM':rootActualError,'canonicalDisplayedFloat32WorldSHA256':digest(actual.reshape(N,16,3)[np.argsort(ids)]),'canonicalUVSHA256':digest(uv[np.argsort(ids)]),'rawGuideSHA256':digest(Q),'fixedCurrentFinalMaterialAndRadiusDensityCountRetained':True,'sourcePostStyleModifiersNotClaimedReproduced':True,'wholeAppearanceFunctionFiniteSelfContinuousContactsNaturalMotionRuntimeUnaccepted':True,'secondsBeforePreview':time.time()-tick})
captures=[]
def capture(scene):
 captures.append({'UTC':stamp(),'source':bpy.data.filepath,'output':scene.render.filepath,'frame':scene.frame_current,'cameraMatrixWorld':[list(x) for x in scene.camera.matrix_world],'lens':scene.camera.data.lens,'cameraType':scene.camera.data.type,'exposure':scene.view_settings.exposure,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'samples':scene.cycles.samples,'seed':scene.cycles.seed,'newHairVisible':not hair.hide_render,'originalHairVisible':not old.hide_render,'captureStateNotRenderDepsgraphProof':True});save('actual-render-pre-capture-states.json',captures)
bpy.app.handlers.render_pre.append(capture);a.b.u.v.E=F;hair.hide_render=True;old.hide_render=False
for v in ['face','body-face']:s.camera.data.type='PERSP';a.b.u.v.image('baseline-original-working-hair',v)
old.hide_render=True;hair.hide_render=False
for v in ['face','body-face','oblique','profile','back']:s.camera.data.type='PERSP';a.b.u.v.image('artist-whole-volume-groom',v)
bpy.app.handlers.render_pre.remove(capture);s.camera.matrix_world=Matrix(captures[2]['cameraMatrixWorld']);s.camera.data.lens=captures[2]['lens'];s.camera.data.type='PERSP'
for f in F.glob('*.png'):shutil.copyfile(f,E/f.name)
outDir=A/'assets-source/aevrynd-character/female-next/r0212-source';outDir.mkdir();inputInfo=json.loads((E/'source-input-snapshot.json').read_text());inputCopy=outDir/Path(inputInfo['file']).name;shutil.copyfile(inputInfo['file'],inputCopy);assert sha(inputCopy)==inputInfo['sha256'];inputInfo['archiveFile']=str(inputCopy);output=F/'aevrynd-female-next-r0212-artist-whole-volume-groom.blend';out=outDir/output.name;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True);shutil.copyfile(output,out);assert out.stat().st_size+inputCopy.stat().st_size<t['sourceBudgetBytes'];save('build-summary.json',{'UTC':stamp(),'output':str(out),'userReviewSource':str(output),'sha256':sha(out),'bytes':out.stat().st_size,'sourceInputSnapshot':inputInfo,'actualHair':hair.name,'actualSkin':skin.name,'actualBirths':births.name,'actualCurves':N,'actualPoints':len(actual),'oneCompleteCandidate':True,'elapsedJobSeconds':time.time()-tick,'unaccepted':True});print('R212_ACTUAL_WHOLE_ARTIST_VOLUME_CURRENT_GROOM_SAVED',flush=True)
