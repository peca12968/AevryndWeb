"""Different CC0 complete short groom, measured whole-volume retarget.
No inherited failed198 guide paths, local brush variants or source scalp graft.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,hashlib,importlib.util,time
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0202-independent-complete-groom';OUT=C/'assets-source/aevrynd-character/female-next/r0202-source/aevrynd-female-next-r0202-independent-short-groom.blend';ART=Path('C:/Users/USER/AppData/Local/Temp/Aevrynd-hair-editor-reference/hair.blend')
sp=importlib.util.spec_from_file_location('r202base',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,x):(E/n).write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def sha(p):return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
def attr(d,n,typ,v,prop='value',domain='POINT'):
 at=d.attributes.new(n,typ,domain);at.data.foreach_set(prop,np.asarray(v).ravel());return at
def basis(v):
 x,y,z=np.asarray(v).T;return np.column_stack([np.ones(len(x)),x,y,z,x*x,x*y,x*z,y*y,y*z,z*z])
tick=time.time();t=json.loads((E/'before.json').read_text('utf-8'));assert not OUT.exists() and sha(ART)=='93aedaef061dc14618a0fcfad33c3df816fa755e8093381cbdfd0fd4c34527f5'
assert (E/'original-short-style-reproduction.json').exists()
bpy.ops.wm.open_mainfile(filepath=str(ART));src=bpy.data.objects['basic_short_hair'];src.hide_set(False);bpy.context.view_layer.update();sourceP,off=m.curveworld(src);lengths=np.diff(np.r_[off,len(sourceP)]).astype('i4');de=src.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;sourceRadius=h.arr(de.attributes['radius'].data,'value',len(sourceP));sourceRaw=h.arr(src.data.position_data,'vector',len(src.data.position_data),3);guideRoots=np.array([src.matrix_world@c.points[0].position for c in src.data.curves],dtype='f8')
assert len(off)==25324 and len(sourceP)==772252 and len(guideRoots)==418
sourceRoots=sourceP[off].copy();sourceRootRadius=sourceRadius[off].copy();sourceBounds=np.stack([guideRoots.min(0),guideRoots.max(0)])
assert sha(t['source'])==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);skin=bpy.data.objects[a.FIXED[0]];old=bpy.data.objects[a.FIXED[1]];previous=bpy.data.objects['AFN198_ACTUAL_SURFACE_BORN_NATIVE_GROOM'];protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING}
W,T=a.geometry(skin);sf=np.load(E.parent/'r0198-native-birth-owned-scalp/native-surface-birth-lineage.npz')['actualCurrentScalpFaces'];cap=W[np.unique(T[sf])];targetBounds=np.stack([cap.min(0),cap.max(0)]);scale=(targetBounds[1]-targetBounds[0])/(sourceBounds[1]-sourceBounds[0]);sourceCentre=sourceBounds.mean(0);targetCentre=targetBounds.mean(0)
tree=BVHTree.FromPolygons(W.tolist(),T[sf].tolist(),all_triangles=True)
def project(points):
 xyz=[];faces=[];bary=[];gap=[];normals=[]
 for p in points:
  hit,no,fi,d=tree.find_nearest(Vector(p));fid=int(sf[fi]);tri=W[T[fid]];v=np.linalg.lstsq(np.column_stack([tri[1]-tri[0],tri[2]-tri[0]]),np.array(hit)-tri[0],rcond=None)[0];bc=np.clip(np.array([1-v.sum(),*v]),0,1);bc/=bc.sum();xyz.append(bc@tri);faces.append(fid);bary.append(bc);gap.append(float(d));normals.append(no)
 return np.array(xyz),np.array(faces,'i4'),np.array(bary),np.array(gap),np.array(normals)
guideSeeds=(guideRoots-sourceCentre)*scale+targetCentre;guideTargets,gf,gb,gg,gn=project(guideSeeds)
# Fit a single smooth three-dimensional displacement of the complete source
# volume to all418 measured source/current scalp correspondences. This does
# not synthesize a hairstyle from shared height stations or freeze free paths.
normalizer=.1;u=(guideRoots-sourceCentre)/normalizer;B=basis(u);correction=guideTargets-guideSeeds;coef=np.linalg.lstsq(np.vstack([B,np.diag([0,0,0,0,.1,.1,.1,.1,.1,.1])]),np.vstack([correction,np.zeros((10,3))]),rcond=None)[0]
def deform(points):
 return (points-sourceCentre)*scale+targetCentre+basis((points-sourceCentre)/normalizer)@coef
epsilon=1e-5;J=np.stack([(deform(guideRoots+np.eye(3)[k]*epsilon)-deform(guideRoots-np.eye(3)[k]*epsilon))/(2*epsilon) for k in range(3)],axis=2);det=np.linalg.det(J);fitError=np.linalg.norm(deform(guideRoots)-guideTargets,axis=1)
correspondence={'UTC':stamp(),'sourceStyle':'basic_short_hair','sourceGuides':418,'sourceRootBounds':sourceBounds.tolist(),'targetActualScalpBounds':targetBounds.tolist(),'sourceCentre':sourceCentre.tolist(),'targetCentre':targetCentre.tolist(),'initialAxisScale':scale.tolist(),'seedToCurrentScalpDistanceQuantilesM':np.quantile(gg,[0,.5,.9,1]).tolist(),'guideFitResidualQuantilesM':np.quantile(fitError,[0,.5,.9,1]).tolist(),'completeVolumeJacobianDeterminantRange':[float(det.min()),float(det.max())],'fixedCheapFalsifiers':{'seedMaximumM':.035,'positiveGuideJacobianMinimum':.05},'initialBoxFitNotAnatomicalCorrespondenceProof':True,'actualCurrentScalpTrianglesExplicitlyUsed':True,'allGuideCorrespondencesRetained':True,'newNonlinearWholeVolumeWarpNotPriorAffineOrRootOnlyTranslation':True,'noCurrentHeadOrScalpGeometryChanged':True}
save('actual-source-current-volume-correspondence.json',correspondence)
assert gg.max()<.035 and det.min()>.05,('Reject source/current correspondence before candidate emission',gg.max(),det.min())
P=deform(sourceP);warpedRoots=P[off].copy();logical,faces,bc,gaps,normals=project(warpedRoots);rootRadius=sourceRootRadius*float(np.cbrt(np.prod(scale)));rootLift=rootRadius+.000002;shaft=logical+normals*rootLift[:,None];rootDelta=shaft-warpedRoots
# Final exact actual Skin ownership for every complete source curve. The
# remaining root residual moves its whole already-warped curve coherently.
P+=np.repeat(rootDelta,lengths,axis=0);assert np.isfinite(P).all()
tri=T[faces];baseRoot=np.einsum('ni,nij->nj',bc,W[tri]);ids=np.arange(len(off),dtype='i4');cu=bpy.data.hair_curves.new('AFN202_COMPLETE_CC0_SHORT_GROOM_CURRENT_SPACE');cu.add_curves(lengths.tolist());cu.position_data.foreach_set('vector',P.astype('f4').ravel());cu.surface=skin;cu.surface_uv_map='AngelicaOriginalUV';hair=bpy.data.objects.new('AFN202_CURRENT_SKIN_OWNED_ARTIST_SHORT_GROOM',cu);s.collection.objects.link(hair)
attr(cu,'AFN202_PERSISTENT_SOURCE_CURVE_ID','INT',ids,domain='CURVE');attr(cu,'AFN202_ACTUAL_SKIN_FACE','INT',faces,domain='CURVE');attr(cu,'AFN202_ROOT_BC','FLOAT_VECTOR',bc.astype('f4'),'vector','CURVE');attr(cu,'radius','FLOAT',(sourceRadius*float(np.cbrt(np.prod(scale)))).astype('f4'))
skinEval=skin.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;skinEval.calc_loop_triangles();loops=np.array([x.loops[:] for x in skinEval.loop_triangles]);uvdata=h.arr(skinEval.uv_layers['AngelicaOriginalUV'].data,'uv',len(skinEval.uv_layers['AngelicaOriginalUV'].data),2)[loops];uv=np.einsum('ni,nij->nj',bc,uvdata[faces]);attr(cu,'surface_uv_coordinate','FLOAT2',uv.astype('f4'),'vector','CURVE')
for k in range(3):attr(cu,'AFN198_CAP_I'+str(k),'INT',np.repeat(tri[:,k],lengths));attr(cu,'AFN198_CAP_W'+str(k),'FLOAT',np.repeat(bc[:,k],lengths).astype('f4'))
attr(cu,'AFN198_ROOT_BIND_WORLD','FLOAT_VECTOR',np.repeat(baseRoot,lengths,axis=0).astype('f4'),'vector')
hair.modifiers.new('AFN202_ACTUAL_CURRENT_SKIN_COMPLETE_CURVE_BINDING','NODES').node_group=previous.modifiers['AFN198_ACTUAL_GUIDE_CAP_BINDING'].node_group.copy()
cu.materials.append(bpy.data.materials['AFN198_OWN_NATIVE_HAIR_FIXED_MELANIN']);hair.hide_render=False;hair.hide_set(False);previous.hide_render=True;old.hide_render=True;bpy.context.view_layer.update();actual,actualOff=m.curveworld(hair);ev=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;actualIDs=h.arr(ev.attributes['AFN202_PERSISTENT_SOURCE_CURVE_ID'].data,'value',len(off),dtype='i4')
assert np.array_equal(actualIDs,ids) and np.array_equal(actualOff,off);error=float(np.linalg.norm(actual-P,axis=1).max());assert error<3e-6;assert protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected}
np.savez_compressed(E/'current-short-groom-root-lineage.npz',sourceGuideRoots=guideRoots.astype('f4'),targetGuideRoots=guideTargets.astype('f4'),sourceCentre=sourceCentre,targetCentre=targetCentre,axisScale=scale,quadraticCoefficient=coef,sourceCompleteRoots=sourceRoots.astype('f4'),warpedCompleteRoots=warpedRoots.astype('f4'),currentLogicalRoots=logical.astype('f4'),currentShaftRoots=shaft.astype('f4'),currentFaces=faces,currentTriangles=tri,currentBC=bc.astype('f4'),currentUV=uv.astype('f4'),sourceCurveOffsets=off,sourceCurveLengths=lengths,sourceCurveIDs=ids,currentRootRadius=rootRadius.astype('f4'),rootResidualTranslation=rootDelta.astype('f4'))
save('independent-short-construction-summary.json',{'UTC':stamp(),'actualHair':hair.name,'actualSkin':skin.name,'actualCurves':len(off),'actualPoints':len(P),'sourceNativeStyle':'basic_short_hair','sourceRawGuides':418,'sourceNativeCompleteCurves':len(off),'allSourceCurvesAndPointsPreserved':True,'persistentSourceCurveIDsPreserved':True,'allSevenRawMeshUVSignaturesUnchanged':protected,'actualDisplayedRootMaximumErrorM':float(np.linalg.norm(actual[off]-shaft,axis=1).max()),'actualDisplayedPointMaximumErrorM':error,'rootResidualTranslationQuantilesM':np.quantile(gaps,[0,.5,.9,1]).tolist(),'material':'AFN198_OWN_NATIVE_HAIR_FIXED_MELANIN','sourceRootRadiusScaledByPhysicalHeadSizeOnly':True,'currentSkinNeverGraftedOrChanged':True,'oldFailedGuidesNotUsedInNewRestShape':True,'newFullVolumeWarpNotFrozenForeignFreePaths':True,'exactSkinAttachmentNotAnatomicalOrContactAcceptance':True,'independentFunctionNaturalMotionContactAndRuntimeUnaccepted':True,'secondsBeforeCompletePreview':time.time()-tick})
captures=[]
def capture(scene):
 captures.append({'UTC':stamp(),'loadedSource':bpy.data.filepath,'plannedCandidate':str(OUT),'output':scene.render.filepath,'frame':scene.frame_current,'cameraMatrixWorld':[list(x) for x in scene.camera.matrix_world],'lens':scene.camera.data.lens,'cameraType':scene.camera.data.type,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'cyclesSamples':scene.cycles.samples,'seed':scene.cycles.seed,'hairType':scene.render.hair_type,'newGroomVisible':not hair.hide_render,'originalHairVisible':not old.hide_render,'previousFailedGroomVisible':not previous.hide_render,'captureStateNotRenderGeometryDepsgraphProof':True});save('actual-render-pre-capture-states.json',captures)
bpy.app.handlers.render_pre.append(capture);a.b.u.v.E=E;hair.hide_render=True;old.hide_render=False
for v in ['face','body-face']:s.camera.data.type='PERSP';a.b.u.v.image('baseline-original-working-hair',v)
old.hide_render=True;hair.hide_render=False
for v in ['face','body-face','oblique','profile','back']:s.camera.data.type='PERSP';a.b.u.v.image('a-independent-short-groom',v)
bpy.app.handlers.render_pre.remove(capture);s.camera.matrix_world=Matrix(captures[2]['cameraMatrixWorld']);s.camera.data.lens=captures[2]['lens'];s.camera.data.type='PERSP';OUT.parent.mkdir(parents=True,exist_ok=True);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
save('a-build-summary.json',{'UTC':stamp(),'output':str(OUT),'sha256':sha(OUT),'bytes':OUT.stat().st_size,'actualHair':hair.name,'actualSkin':skin.name,'oneCandidate':True,'elapsedJobSeconds':time.time()-tick,'actualCurves':len(off),'actualPoints':len(P),'unaccepted':True});print('R202_COMPLETE_DIFFERENT_CC0_SHORT_GROOM_SAVED',flush=True)
