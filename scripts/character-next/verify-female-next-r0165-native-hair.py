"""Independent minimum source, actual geometry/edit/root and failure readback.
No appearance rescue, natural motion or finite render occupancy claim.
"""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0165-native-hair-construction'
sp=importlib.util.spec_from_file_location('r165verify',C/'scripts/character-next/build-female-next-r0165-intrinsic-native-groom.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;tick=time.time();before=json.loads((E/'before.json').read_text());A=json.loads((E/'a-build-summary.json').read_text());B=json.loads((E/'b-build-summary.json').read_text());records=[];baseline=None
def save(n,x):(E/n).write_bytes((json.dumps(x,indent=2)+'\n').encode())
for tag,p,digest in [('input152',before['source'],before['sourceSha256']),('A',A['engineAlias'],A['sha256']),('B',B['engineAlias'],B['sha256'])]:
 assert a.a.sha(Path(p))==digest;bpy.ops.wm.open_mainfile(filepath=p);s=bpy.context.scene;rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];s.frame_set(1);bpy.context.view_layer.update();raw={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};poses=[]
 for frame in range(1,50):
  s.frame_set(frame);bpy.context.view_layer.update();poses.append({'frame':frame,'allSevenWorldHashes':{n:[a.a.hasharray(x) for x in a.geometry(bpy.data.objects[n])] for n in a.FIXED+a.MOVING}})
 current={'raw':raw,'poses':poses,'action':rig.animation_data.action.name}
 if baseline is None:baseline=current
 else:assert current==baseline,'Protected actual original49-gaze/current meshes differ'
 s.frame_set(1);bpy.context.view_layer.update();record={'state':tag,'source':p,'sha256':digest,'allSevenRawMeshesUVAnd49EvaluatedGazePosesEqual':True,'action':rig.animation_data.action.name,'rawSignatures':raw,'explicitFrame1Restored':True}
 if tag=='A':
  hair=bpy.data.objects[A['actualHair']];slot=hair.material_slots[0];node=next(n for n in slot.material.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled');record['effectiveObjectSlot']={'link':slot.link,'material':slot.material.name,'IOR':float(node.inputs['IOR'].default_value),'originalLibraryMaterialIOR':float(next(n for n in hair.data.materials[0].node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled').inputs['IOR'].default_value)};assert abs(record['effectiveObjectSlot']['IOR']-1.55)<1e-6 and record['effectiveObjectSlot']['originalLibraryMaterialIOR']==1000.
 if tag=='B':
  hair=bpy.data.objects[B['actualHair']];skin=bpy.data.objects[B['actualSkin']];old=bpy.data.objects[B['sourceOriginalHair']];assert not hair.hide_render and old.hide_render;rest=a.q.hair(hair);count=B['nativeStrands'];assert len(rest)==B['points'] and np.isfinite(rest).all();data=hair.data;radius=a.q.arr(data.attributes['radius'].data,'value',len(rest));ev=hair.evaluated_get(bpy.context.evaluated_depsgraph_get());actualRadius=a.q.arr(ev.data.attributes['radius'].data,'value',len(rest));assert np.isfinite(actualRadius).all();shader=next(n for n in data.materials[0].node_tree.nodes if n.bl_idname=='ShaderNodeBsdfHairPrincipled');record['nativeRepresentation']={'object':hair.name,'nativeCurves':len(data.curves),'nativePoints':len(data.points),'evaluatedControlPoints':len(rest),'actualEvaluatedRadiusRangeM':[float(actualRadius.min()),float(actualRadius.max())],'rawRadiusRangeM':[float(radius.min()),float(radius.max())],'allFinite':True,'material':data.materials[0].name,'shader':shader.bl_idname,'model':getattr(shader,'model',None),'parametrization':shader.parametrization,'effectiveInputs':{key:float(shader.inputs[key].default_value) for key in ['Melanin','Melanin Redness','Roughness','Radial Roughness','IOR'] if key in shader.inputs},'savedSceneHairType':s.render.hair_type,'savedSceneSamples':s.cycles.samples,'savedSceneResolution':[s.render.resolution_x,s.render.resolution_y],'actualCaptureControlsSeparate':str(E/'actual-intrinsic-native-groom-preview-controls.json'),'sourceFieldsNotRenderDepsgraphOrCauseProof':True,'originalCoarseHairHiddenNoUnderlay':old.hide_render}
  co=data.position_data[24].vector.copy();data.position_data[24].vector=co+Vector((.001,0,0));data.update_tag();hair.update_tag();bpy.context.view_layer.update();changed=a.q.hair(hair);distance=np.linalg.norm(changed-rest,axis=1);move=float(distance.max());rootsMove=float(distance.reshape(count,49)[:,0].max());data.position_data[24].vector=co;data.update_tag();hair.update_tag();bpy.context.view_layer.update();restore=float(np.linalg.norm(a.q.hair(hair)-rest,axis=1).max());assert move>.0009 and rootsMove<3e-6 and restore<3e-6
  link=skin.data;assert link.library is not None;skin.data=link.copy();ids=a.q.arr(data.attributes['AFN149_SkinVertex0'].data,'value',len(rest),dtype='i4');probe=int(ids[0]);co=skin.data.vertices[probe].co.copy();skin.data.vertices[probe].co=co+Vector((0,0,.001));skin.data.update();skin.update_tag(refresh={'DATA'});bpy.context.view_layer.update();skinMoved=a.q.hair(hair);skinMove=float(np.linalg.norm(skinMoved-rest,axis=1).max());assert skinMove>1e-5;skin.data=link;bpy.context.view_layer.update();skinRestore=float(np.linalg.norm(a.q.hair(hair)-rest,axis=1).max());assert skinRestore<3e-6;record['actualNativeEditAndSourceBinding']={'point1mmEditMaximumMovementM':move,'allRootsMovementFromInteriorPointEditM':rootsMove,'pointEditRestoreMaximumM':restore,'actualSkinVertexProbe':probe,'actualSkinEditMaximumGroomMovementM':skinMove,'actualSkinEditRestoreMaximumM':skinRestore,'editingLinkedSkinRequiredSingleUserCopy':True,'originalLibraryMeshPointerRestored':True,'notCompleteHeadMotionOrNaturalDynamics':True}
  # Cheap proper control-polygon crossing witness on the actual body mesh.
  # Centreline chords are not exact rendered Catmull/finite spline occupancy.
  W,T=a.geometry(skin);tree=BVHTree.FromPolygons([Vector(x) for x in W],T.tolist(),all_triangles=True);paths=rest.reshape(count,49,3);gaps=np.load(E/'actual-intrinsic-groom-root-lineage.npz')['sourceEndpointGaps'];order=np.argsort(gaps)[::-1];witness=[];inspected=0;hitCount=0
  for ci in order[:128]:
   inspected+=1
   for j in range(48):
    x,y=paths[ci,j:j+2];vec=y-x;length=float(np.linalg.norm(vec))
    if length<1e-12:continue
    point,normal,fi,dist=tree.ray_cast(Vector(x),Vector(vec/length),length)
    if point is not None:
     hitCount+=1
     if dist>1e-5 and dist<length-1e-5:witness.append({'curve':int(ci),'controlSegment':j,'bodyTriangle':int(fi),'worldPoint':list(point),'distanceAlongControlSegmentM':float(dist),'segmentLengthM':length,'sourceEndpointToScalpGapM':float(gaps[ci])})
    if len(witness)>=8:break
   if len(witness)>=8:break
  save('minimum-native-groom-body-witnesses.json',{'sourceSha256':B['sha256'],'allNativeCurves':count,'inspectionPriority':'Largest source endpoint gaps first, all segments of inspected curves including roots; stop after8 well-separated chord intersections or128 complete curves.','curvesInspected':inspected,'allRayHitsObservedInInspectedSegments':hitCount,'strongControlPolygonBodyIntersections':witness,'strongClassification':'Interior along control chord at least10micrometres from endpoints; not a relaxed pass tolerance. No global pass is claimed.','actualBodyTriangles':len(T),'sourceControlPolygonNotExactRenderedSplineOccupancy':True,'finiteRadiusSelfContinuousAndGlobalSignedMinimumUnaccepted':True})
  deps=[]
  for lib in bpy.data.libraries:
   p=Path(bpy.path.abspath(lib.filepath)).resolve();assert p.is_file();deps.append({'kind':'library','file':str(p),'sha256':a.a.sha(p)})
  for im in bpy.data.images:
   if im.source=='FILE' and not im.packed_file and im.filepath:
    p=Path(bpy.path.abspath(im.filepath,library=im.library)).resolve();assert p.is_file();deps.append({'kind':'texture','file':str(p),'sha256':a.a.sha(p)})
  hashes={d['sha256'] for d in deps};expected=json.loads((E.parent/'r0158-shared-native-skin/workspace-storage-provenance.json').read_text())['dependencyFiles'];assert all(x['sha256'] in hashes for x in expected);record['dependencies']=deps;record['uniqueDependencyFileHashCount']=len(hashes);record['geometryAndMaterialReadbackNotCompleteAppearanceFunctionContactRuntimeAcceptance']=True
 assert a.a.sha(Path(p if isinstance(p,str) else {'input152':before['source'],'A':A['output'],'B':B['output']}[tag]))==digest if tag!='B' else a.a.sha(Path(B['output']))==digest
 records.append(record);save('independent-native-hair-source-readback.json',{'records':records,'original49GazePoseHashReference':baseline['poses'],'allProtected49GazeAndCurrentMeshGeometryEqual':True,'originalSourceFilesUnchanged':True,'fullHairAppearanceNaturalMotionFiniteSelfContinuousRuntimeUnaccepted':True,'seconds':time.time()-tick})
print('R165_INDEPENDENT_A_B_SOURCE_49GAZE_NATIVE_EDIT_ROOT_RESTORE_AND_MINIMUM_BODY_READBACK_DONE',time.time()-tick,flush=True)
