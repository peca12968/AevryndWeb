"""Continuous current-Skin intrinsic streamlines and complete swept crop.
New full rest paths and connected anatomical posterior domain, no bank pooling,
foreign affine/free-path transplant, former sagittal split or failed-root rescue.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,time,hashlib,importlib.util,shutil
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);E=A/'evidence/character-female-next/r0204-anatomical-groom-regions';F=Path('F:/AevryndEvidence/r0204-anatomical-groom-regions');t=json.loads((E/'before.json').read_text('utf-8'));tick=time.time()
def sha(f):return hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,d):(E/n).write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
def attr(d,n,typ,values,prop='value',domain='POINT'):
 a=d.attributes.get(n) or d.attributes.new(n,typ,domain);a.data.foreach_set(prop,np.asarray(values).ravel());return a
assert sha(t['source'])==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);sp=importlib.util.spec_from_file_location('r204base',A/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h;skin=bpy.data.objects[a.FIXED[0]];old=bpy.data.objects[a.FIXED[1]];previous=bpy.data.objects['AFN198_ACTUAL_SURFACE_BORN_NATIVE_GROOM'];oldBirths=bpy.data.objects['AFN198_ACTUAL_EDITABLE_SURFACE_BIRTHS'];protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};rootData=np.load(E.parent/'r0198-native-birth-owned-scalp/native-surface-birth-lineage.npz');W,T=a.geometry(skin);sf=rootData['actualCurrentScalpFaces'];tree=BVHTree.FromPolygons(W.tolist(),T[sf].tolist(),all_triangles=True)
roots=h.arr(previous.data.position_data,'vector',4032,3).reshape(252,16,3)[:,0];normals=h.arr(previous.data.attributes['AFN198_GUIDE_UP'].data,'vector',252,3);before=h.arr(previous.data.position_data,'vector',4032,3).reshape(252,16,3)
def region(roots,normals):
 result=np.full(len(roots),3,'i4');lateral=(np.abs(normals[:,0])>.55)&(roots[:,1]<.025);result[lateral&(roots[:,0]<0)]=1;result[lateral&(roots[:,0]>=0)]=2;result[(roots[:,2]>1.53)&(roots[:,1]<.015)]=0;result[(roots[:,2]<1.465)&(roots[:,1]>0)]=4;return result
regions=region(roots,normals);cuts=np.choose(regions,[.045,.028,.028,.034,.023]);heights=np.choose(regions,[.009,.005,.005,.006,.004]);paths=[];surfacePaths=[];released=[];logical=rootData['guideLogicalBirthWorld']
for gid,(root,n0,L,H) in enumerate(zip(roots,normals,cuts,heights)):
 q=np.array(logical[gid],dtype='f8');normal=np.array(n0,dtype='f8');normal/=np.linalg.norm(normal);trace=[q.copy()];out=[root.copy()];free=False;releaseAt=None;direction=None
 for j in range(1,16):
  previousS=(j-1)*L/15;endS=j*L/15
  for step in range(4):
   ds=L/60;flow=np.array([0,1,-.22],dtype='f8');d=flow-normal*np.dot(flow,normal)
   if np.linalg.norm(d)<1e-6:d=np.array([0,0,-1.])-normal*np.dot(np.array([0,0,-1.]),normal)
   d/=np.linalg.norm(d);candidate=q+ds*d
   if not free:
    hit,no,fi,distance=tree.find_nearest(Vector(candidate));newQ=np.array(hit);newN=np.array(no)
    if np.dot(newN,normal)<0:newN=-newN
    newN/=np.linalg.norm(newN)
    if np.linalg.norm(newQ-q)<.15*ds or distance>.75*ds:free=True;releaseAt=(j-1)*4+step
    else:q=newQ;normal=newN
   if free:q+=ds*d+np.array([0,0,-1])*ds*.20*(endS/L)**2
  u=j/15;height=.000102+H*np.sin(.75*np.pi*u);point=q+normal*height;trace.append(q.copy());out.append(point)
 paths.append(out);surfacePaths.append(trace);released.append(-1 if releaseAt is None else releaseAt)
P=np.array(paths,dtype='f4');assert np.isfinite(P).all() and float(np.linalg.norm(P[:,0]-roots,axis=1).max())==0
# Preserve whole203 failed groom/22-path construction as hidden rollback;
# new native guides and independent birth object own every new displayed ID.
hair=previous.copy();hair.data=previous.data.copy();hair.name='AFN204_ACTUAL_CURRENT_SKIN_CONNECTED_CROP';s.collection.objects.link(hair);births=oldBirths.copy();births.data=oldBirths.data.copy();births.name='AFN204_CURRENT_SKIN_CONNECTED_BIRTHS';s.collection.objects.link(births);births.hide_render=True;births.hide_set(True)
for mod in hair.modifiers:
 if mod.type=='NODES' and mod.node_group:mod.node_group=mod.node_group.copy()
for mod in births.modifiers:
 if mod.type=='NODES' and mod.node_group:mod.node_group=mod.node_group.copy()
generator=hair.modifiers['AFN198_ACTUAL_SURFACE_CHILD_GENERATOR']
for node in generator.node_group.nodes:
 if node.bl_idname=='GeometryNodeObjectInfo' and node.inputs['Object'].default_value==oldBirths:node.inputs['Object'].default_value=births
 if node.bl_idname=='GeometryNodeInputNamedAttribute' and node.inputs['Name'].default_value=='AFN198_PART_BRANCH':node.inputs['Name'].default_value='AFN204_CONNECTED_GROOM_DOMAIN'
attr(hair.data,'AFN204_CONNECTED_GROOM_DOMAIN','INT',np.zeros(252,'i4'),domain='CURVE');attr(hair.data,'AFN204_ANATOMICAL_REGION','INT',regions,domain='CURVE');attr(hair.data,'AFN204_PERSISTENT_GUIDE_ID','INT',np.arange(252,dtype='i4'),domain='CURVE');hair.data.position_data.foreach_set('vector',P.ravel());hair.data.update_tag();B=np.array([v.co[:] for v in births.data.vertices]);bn=h.arr(births.data.attributes['AFN198_POINT_UP'].data,'vector',len(B),3);birthRegions=region(B,bn);attr(births.data,'AFN204_CONNECTED_GROOM_DOMAIN','INT',np.zeros(len(B),'i4'));attr(births.data,'AFN204_ANATOMICAL_REGION','INT',birthRegions);births.data.update();hair.hide_set(False);hair.hide_render=False;previous.hide_render=True;previous.hide_set(True);bpy.context.view_layer.update()
actual,off=m.curveworld(hair);d=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;ids=h.arr(d.attributes['AFN198_PERSISTENT_BIRTH_ID'].data,'value',len(off),dtype='i4');uv=h.arr(d.attributes['surface_uv_coordinate'].data,'vector',len(off),2);assert len(off)==10191 and np.array_equal(np.sort(ids),np.arange(10191));rootError=float(np.linalg.norm(actual[off]-rootData['shaftStartWorld'][ids],axis=1).max());assert rootError<3e-6;assert protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected};assert np.max(np.abs(uv-rootData['actualSkinUV'][ids]))<1e-6
np.savez_compressed(E/'connected-current-skin-streamline-lineage.npz',currentGuideRoots=roots,guideCurrentSkinNormals=normals,actualSkinScalpFaces=sf,newAuthoredGuidePaths=P,old203GuidePaths=before,guideAnatomicalRegions=regions,guideCutLengthsM=cuts,guideShaftArchM=heights,currentSurfaceStreamlines=np.array(surfacePaths),surfaceBoundaryReleaseSteps=np.array(released),birthAnatomicalRegions=birthRegions,displayBirthIDs=ids,displayBirthUV=uv,actualDisplayedPositions=actual,actualDisplayedOffsets=off)
save('authoring-decision.json',{'UTC':stamp(),'actualSingleChosenMethod':'Actual currentSkin intrinsic surface streamlines, connected posterior field and full short swept crop rest geometry. All source/artist foreign-retarget methods remain unqualified.','actualNewEvidence':'Actual globalx split applies to127 rear guides and5169 posterior births; effective artist raw-source roots also differ from native surface-deformed roots by14.9955mm, but current anatomical correspondence still missing. No retry of202 box/root mapping.','artistShortReference':'Inspected source-only Klecer CC0 complete short-groom front/profile; effective source guide median length30.0169mm. Used only style/scale reference, no foreign paths/UV copied.','newStyleWhy':'Short swept crop independently authors complete root-to-tip scalp-following rest flow and anatomical posterior continuity; avoids pooled22-bank lobes. A new hairstyle, not a shortened action, removed failures or collision pass. All10191 births preserved; old long failures remain rollback and all old contact conclusions invalid for this new style.','ownCutLengthsByRegionM':{'crownFront':.045,'leftSide':.028,'rightSide':.028,'occiput':.034,'nape':.023},'isNotPhysicalHairSimulationOrFiniteContactProof':True,'fixedMaterialRadiusDensityLightAndExposureUnchanged':True})
save('anatomical-connected-construction.json',{'UTC':stamp(),'actualHair':hair.name,'actualSkin':skin.name,'actualBirths':births.name,'sourceGuideCount':252,'actualCurves':len(off),'actualPoints':len(actual),'allPersistentBirthIDsAndUVRetained':True,'rawRootMaximumChangeM':0,'completeFreePathMaximumChangeM':float(np.linalg.norm(P-before,axis=2).max()),'actualBirthRootMaximumErrorM':rootError,'allSevenRawMeshUVSignaturesUnchanged':protected,'actualConnectedGeneratorGroupAttribute':'AFN204_CONNECTED_GROOM_DOMAIN','allConnectedDomainValue':0,'regionAttributeIsEditableMaskNotArtificialBoundary':'AFN204_ANATOMICAL_REGION crown-front0,leftside1,rightside2,occiput3,nape4','guideRegionCounts':{str(i):int((regions==i).sum()) for i in np.unique(regions)},'birthRegionCounts':{str(i):int((birthRegions==i).sum()) for i in np.unique(birthRegions)},'allOriginalFailedGroomAndBuildTimeBezierObjectsRetainedHiddenRollback':True,'noNewSkinShellOrForeignSourceCopied':True,'actualIntrinsicFlowUsesCurrentScalpTrianglesNotAWorldHeightStationTable':True,'referenceSourceRawEvaluatedContradictionRetainedNoInventedCause':True,'constructionSecondsBeforePreview':time.time()-tick,'contactNaturalMotionOperationAndRuntimeUnaccepted':True})
captures=[]
def capture(scene):
 captures.append({'UTC':stamp(),'loadedSource':bpy.data.filepath,'output':scene.render.filepath,'frame':scene.frame_current,'cameraMatrixWorld':[list(v) for v in scene.camera.matrix_world],'lens':scene.camera.data.lens,'cameraType':scene.camera.data.type,'exposure':scene.view_settings.exposure,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'cyclesSamples':scene.cycles.samples,'seed':scene.cycles.seed,'originalHairVisible':not old.hide_render,'newConnectedGroomVisible':not hair.hide_render,'previous203GroomVisible':not previous.hide_render,'captureStateNotRenderGeometryDepsgraphProof':True});save('actual-render-pre-capture-states.json',captures)
bpy.app.handlers.render_pre.append(capture);a.b.u.v.E=F;hair.hide_render=True;old.hide_render=False
for v in ['face','body-face']:s.camera.data.type='PERSP';a.b.u.v.image('baseline-original-working-hair',v)
old.hide_render=True;hair.hide_render=False
for v in ['face','body-face','oblique','profile','back']:s.camera.data.type='PERSP';a.b.u.v.image('a-connected-current-skin-crop',v)
bpy.app.handlers.render_pre.remove(capture);s.camera.matrix_world=Matrix(captures[2]['cameraMatrixWorld']);s.camera.data.lens=captures[2]['lens'];s.camera.data.type='PERSP'
for f in F.glob('matched-*.png'):shutil.copyfile(f,E/f.name)
output=F/'aevrynd-female-next-r0204-connected-current-skin-crop.blend';out=A/'assets-source/aevrynd-character/female-next/r0204-source'/output.name;out.parent.mkdir();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True);shutil.copyfile(output,out);assert sha(output)==sha(out);save('a-build-summary.json',{'UTC':stamp(),'output':str(out),'userReviewSource':str(output),'sha256':sha(out),'bytes':out.stat().st_size,'actualHair':hair.name,'actualSkin':skin.name,'actualBirths':births.name,'actualCurves':len(off),'actualPoints':len(actual),'oneCompleteCandidate':True,'elapsedJobSeconds':time.time()-tick,'unaccepted':True});print('R204_COMPLETE_CONNECTED_CURRENT_SKIN_CROP_SAVED',json.dumps({'source':str(output),'curves':len(off),'points':len(actual),'rootErrorM':rootError}),flush=True)