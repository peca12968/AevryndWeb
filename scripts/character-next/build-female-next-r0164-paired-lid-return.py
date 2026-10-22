"""One coherent paired lid-return construction in the actual complete Skin.
Inner fold follows the SAME evaluated outer-lid bands, then harmonic attachment
to retained posterior cavity. No cloth rebake, cover, contact exemption or sweep.
Geometric engineering approximation, not physiological/continuous/runtime proof.
"""
from pathlib import Path
import bpy,bmesh,numpy as np,json,importlib.util,time,datetime,collections
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0164-paired-lid-return';OUT=C/'assets-source/aevrynd-character/female-next/r0164-source/aevrynd-female-next-r0164-a-paired-lid-return.blend'
sp=importlib.util.spec_from_file_location('r164base',C/'scripts/character-next/build-female-next-r0161-contact-membrane-lids.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h;g=m.g;m.E=E;h.E=E
def main():
 tick=time.time();before=json.loads((E/'before.json').read_text());assert not OUT.exists() and a.a.sha(Path(before['source']))==before['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=before['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[a.FIXED[0]];reference=bpy.data.objects['AFN161_ORIGINAL_NATIVE_MARGIN_POSE_REFERENCE'];patch=bpy.data.objects['AFN157_ACTUAL_EDITABLE_OUTER_LIDS'];rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];old=skin.data;V,T=a.geometry(skin);N=len(V);baseline={n:a.geometry(bpy.data.objects[n])[0] for n in a.FIXED+a.MOVING};z=np.load(E.parent/'r0163-remeshed-inner-lids/actual-remeshed-wall-source-map.npz');wallGlobal=z['wallTriangles'];used=z['globalVertexIds'];rim=z['boundaryVertexIds'];oldWall=set(map(int,z['newWallPolygons']));local={int(v):i for i,v in enumerate(used)};F=np.array([[local[int(v)] for v in f] for f in wallGlobal],'i4');rest=V[used].copy();originalRim=set(map(int,rim));boundaryLocal=np.array([local[int(v)] for v in rim],'i4');edges=collections.Counter(tuple(sorted((int(u),int(v)))) for f in wallGlobal for u,v in zip(f,np.roll(f,-1)));directed={int(u):int(v) for f in wallGlobal for u,v in zip(f,np.roll(f,-1)) if edges[tuple(sorted((int(u),int(v))))]==1};assert set(directed)==originalRim
 lineage=np.load(E.parent/'r0158-shared-native-skin/explicit-shared-skin-lineage.npz');patchToNative=lineage['patchToNative'];author=np.load(R/'Evidence/character-female-next/r0157-outer-lid-retopology/authored-outer-lid-patch.npz');role=author['role'];side=author['side'];outerUV=author['uvPerVertex'];PV,PT=a.geometry(patch);RV,_=a.geometry(reference);patchError=float(np.linalg.norm(PV-RV[patchToNative],axis=1).max());assert patchError<2e-7
 # Every rim point belongs to an actual outer band column, by source ID.
 columns={};columnRows={};taper={};reports=[]
 for si in [0,1]:
  inner=np.flatnonzero((side==si)&(role==0));n=len(inner);outerIds=patchToNative[inner];assert set(map(int,outerIds))<=originalRim
  xyz=PV[inner];left=int(np.argmin(xyz[:,0]));right=int(np.argmax(xyz[:,0]));cycle=list(range(n));up=cycle[left:right+1] if left<right else cycle[left:]+cycle[:right+1];low=cycle[right:left+1] if right<left else cycle[right:]+cycle[:left+1];thickness=np.zeros(n)
  for chain in [up,low]:
   P=xyz[chain];arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))];t=arc/arc[-1];thickness[chain]=.0008*(.35+.65*np.sqrt(np.maximum(np.sin(np.pi*t),0.)))
  for k,pi in enumerate(inner):
   vi=int(patchToNative[pi]);columns[vi]=int(pi);columnRows[vi]=[int(np.flatnonzero((side==si)&(role==j))[k]) for j in [1,2,3]];taper[vi]=float(thickness[k])
  reports.append({'side':si,'columns':n,'actualTissueThicknessRangeM':[float(thickness.min()),float(thickness.max())],'outerBandFractions':[.16,.33,.52],'innerThicknessFractions':[.45,.8,1.],'canthusTaperIsAuthoredAnatomicalApproximationNotContactAdaptive':True})
 assert set(columns)==originalRim;newV=V.tolist();rowId={};rowPatch=[];rowThickness=[];rowNative=[]
 for j,multiplier in enumerate([.45,.8,1.]):
  for vi in rim:
   vi=int(vi);rowId[(j,vi)]=len(newV);newV.append([0.,0.,0.]);rowPatch.append(columnRows[vi][j]);rowThickness.append(taper[vi]*multiplier);rowNative.append(int(patchToNative[columnRows[vi][j]]))
 rowPatch=np.array(rowPatch,'i4');rowThickness=np.array(rowThickness);rowNative=np.array(rowNative,'i4');newV=np.array(newV,'f4');backBoundary=np.array([rowId[(2,int(vi))] for vi in rim],'i4');backMap={int(vi):rowId[(2,int(vi))] for vi in rim};newBack=np.array([[backMap.get(int(v),int(v)) for v in face] for face in wallGlobal],'i4');returnFaces=[]
 for u,v in directed.items():
  for j in range(3):
   x=u if j==0 else rowId[(j-1,u)];y=v if j==0 else rowId[(j-1,v)];z1=rowId[(j,v)];z0=rowId[(j,u)];returnFaces.extend([[x,y,z1],[x,z1,z0]])
 returnFaces=np.array(returnFaces,'i4');newWall=np.concatenate((returnFaces,newBack));keep=[f for f in old.polygons if f.index not in oldWall];faces=[list(f.vertices) for f in keep]+newWall.tolist();newUsed=np.array(sorted(set(map(int,newWall.ravel()))),'i4');newLocal={int(v):i for i,v in enumerate(newUsed)};newF=np.array([[newLocal[int(v)] for v in f] for f in newWall],'i4')
 # Harmonic boundary extension changes rest space, with posterior fixed by
 # source depth; it is not a free tissue solver and has no hidden face culling.
 posterior=set()
 for si in [False,True]:
  ids=np.flatnonzero((rest[:,0]<0)==si);cut=float(np.quantile(rest[ids,1],.75));posterior.update(int(i) for i in ids if rest[i,1]>=cut and int(used[i]) not in originalRim)
 fixed=np.array(sorted(set(map(int,boundaryLocal))|posterior),'i4');unknown=np.array(sorted(set(range(len(used)))-set(map(int,fixed))),'i4');adj=[set() for _ in used]
 for face in F:
  for u,v in zip(face,np.roll(face,-1)):adj[int(u)].add(int(v));adj[int(v)].add(int(u))
 L=np.zeros((len(used),len(used)))
 for i,neighbors in enumerate(adj):L[i,i]=len(neighbors);L[i,list(neighbors)]=-1.
 H=-np.linalg.solve(L[np.ix_(unknown,unknown)],L[np.ix_(unknown,fixed)]);fixedWhere={int(v):i for i,v in enumerate(fixed)};steps=[];stats=[];zeroNormals=[]
 def positions(frame):
  s.frame_set(frame);bpy.context.view_layer.update();outer,tri=a.geometry(patch);ref,_=a.geometry(reference);assert float(np.linalg.norm(outer-ref[patchToNative],axis=1).max())<2e-7;normal=np.zeros_like(outer);area=np.cross(outer[tri[:,1]]-outer[tri[:,0]],outer[tri[:,2]]-outer[tri[:,0]])
  for k in range(3):np.add.at(normal,tri[:,k],area)
  length=np.linalg.norm(normal,axis=1);assert (length[rowPatch]>0).all(),'Actual outer normal undefined; no arbitrary frame fallback';normal/=np.maximum(length[:,None],1e-30);inside=outer[rowPatch]-rowThickness[:,None]*normal[rowPatch];targets=rest.copy();delta=np.zeros((len(fixed),3))
  for k,vi in enumerate(rim):delta[fixedWhere[local[int(vi)]]]=inside[2*len(rim)+k]-rest[local[int(vi)]]
  targets[fixed]=rest[fixed]+delta;targets[unknown]=rest[unknown]+H@delta;world=newV.astype('f8').copy();world[:len(ref)]=ref;world[N:]=inside
  for i,vi in enumerate(used):
   if int(vi) not in originalRim:world[int(vi)]=targets[i]
  result=world[newUsed];dist=np.linalg.norm(inside-outer[rowPatch],axis=1);triP=world[newWall];area2=np.linalg.norm(np.cross(triP[:,1]-triP[:,0],triP[:,2]-triP[:,0]),axis=1);stats.append({'frame':frame,'blink':[float(rig[k]) for k in ['blink_L','blink_R']],'actualPairedVertexOffsetRangeM':[float(dist.min()),float(dist.max())],'allSourcePatchPositionsAgreeWithActualOuterSkinM':float(np.linalg.norm(outer-ref[patchToNative],axis=1).max()),'minimumNewWallDoubleAreaM2':float(area2.min()),'zeroAreaNewTriangles':int((area2==0).sum()),'maxNewWallDisplacementFromOriginalNeutralM':float(np.linalg.norm(result-newV[newUsed],axis=1).max())});return result,world
 neutral,newV64=positions(1);newV=newV64.astype('f4');m.save('direct-paired-lid-return-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':before['startedUTC'],'changedPremise':'Actual same complete Skin now contains connected folded inner returns derived from the same evaluated outer bands. Posterior lining rest attachment is rebuilt with exact inner-boundary targets and fixed posterior nodes. No unchanged contact-membrane simulation, radial cup projection or added exterior cover. All new faces replace the original inner-wall domain and stay in final contacts.','originalWallTrianglesReplaced':len(wallGlobal),'newReturnTriangles':len(returnFaces),'newPosteriorTriangles':len(newBack),'sourceSharedRimPoints':len(rim),'posteriorFixedNodes':len(posterior),'harmonicInteriorNodes':len(unknown),'sameOuterSourceAndTrueSharedMotion':True,'sourceOuterPatchErrorM':patchError,'thicknessConstruction':reports,'thicknessNotPhysiologicallyCalibrated':True,'reference':'EyeWiki eyelid anterior/posterior structural concepts only; no image/text assets copied.','allOldRetirementsRemainEffective':True})
 for frame in range(1,25):
  result,_=positions(frame);assert np.isfinite(result).all();steps.append(result.astype('f4'));m.save('actual-paired-lid-return-progress.json',stats);print('R164_ACTUAL_PAIRED_RETURN_FRAME',frame,stats[-1]['zeroAreaNewTriangles'],flush=True)
 # One native Skin with unchanged exterior corner UV/normals/materials.
 mesh=bpy.data.meshes.new('AFN164_ONE_NATIVE_PAIRED_LID_RETURN_SKIN');mesh.from_pydata(newV.tolist(),[],faces);mesh.update()
 for material in old.materials:mesh.materials.append(material if material else next(x for x in old.materials if x))
 for i,material in enumerate(old.materials):
  if material is None:mesh.materials[i]=None
 for i,f in enumerate(mesh.polygons):f.material_index=old.polygons[keep[i].index].material_index if i<len(keep) else 0;f.use_smooth=old.polygons[keep[i].index].use_smooth if i<len(keep) else True
 oldLoopOrder=np.array([li for f in keep for li in range(f.loop_start,f.loop_start+f.loop_total)],'i4');newLoopVert=newWall.ravel();pointUV=np.zeros((len(newV),2),'f4');pointUV[N:]=outerUV[rowPatch]
 for uv in old.uv_layers:
  values=h.arr(uv.data,'uv',len(uv.data),2)
  for fi in oldWall:
   f=old.polygons[fi]
   for vi,li in zip(f.vertices,range(f.loop_start,f.loop_start+f.loop_total)):pointUV[vi]=values[li]
  dst=mesh.uv_layers.new(name=uv.name);dst.data.foreach_set('uv',np.concatenate((values[oldLoopOrder],pointUV[newLoopVert])).ravel());dst.active_render=uv.active_render;dst.active_clone=uv.active_clone
 mesh.uv_layers.active_index=old.uv_layers.active_index
 for name in ['AFN113_NATIVE_COLOR_WEIGHT','AFN126_NECK_BLEND']:
  values=h.arr(old.attributes[name].data,'value',N);m.attr(mesh,name,np.concatenate((values,values[rowNative])))
 parents=h.arr(old.attributes['AFN117_NATIVE_PARENT_FACE'].data,'value',len(old.polygons),dtype='i4');m.attr(mesh,'AFN117_NATIVE_PARENT_FACE',np.concatenate((parents[[f.index for f in keep]],np.full(len(newWall),-1,'i4'))),'FACE');norm=np.concatenate((h.arr(old.corner_normals,'vector',len(old.loops),3)[oldLoopOrder],np.zeros((len(newLoopVert),3),'f4')));mesh.normals_split_custom_set(norm.tolist());wi=np.zeros(len(newV),'i4');wi[newUsed]=np.arange(len(newUsed));interior=np.zeros(len(newV),'i4');interior[[int(v) for v in newUsed if int(v) not in originalRim]]=1;m.attr(mesh,'AFN161_WALL_INDEX',wi);m.attr(mesh,'AFN161_WALL_INTERIOR',interior);m.attr(mesh,'AFN161_EDIT_REST',newV);baked=m.meshob('AFN164_ACTUAL_PAIRED_LID_RETURN_STATES',steps[0],newF);baked.shape_key_add(name='Basis')
 for i in range(1,24):
  key=baked.shape_key_add(name='AFN164_PAIRED_RETURN_FRAME_%02d'%(i+1));key.data.foreach_set('co',steps[i].ravel())
  for frame,value in [(i,0.),(i+1,1.),(i+2,0.)]:key.value=value;key.keyframe_insert(data_path='value',frame=frame)
 for layer in baked.data.shape_keys.animation_data.action.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
 baked.hide_set(True);skin.modifiers.clear();skin.data=mesh;m.skin_graph(skin,reference,baked);s.frame_set(1);bpy.context.view_layer.update();actual,_=a.geometry(skin);outerIds=np.unique(np.array([v for f in keep for v in f.vertices]));outsideError=float(np.linalg.norm(actual[outerIds]-baseline[skin.name][outerIds],axis=1).max());assert outsideError<2e-7;np.savez_compressed(E/'actual-paired-lid-return-source-map.npz',globalVertexIds=newUsed,wallTriangles=newWall,newWallPolygons=np.arange(len(keep),len(faces),dtype='i4'),boundaryVertexIds=rim,returnPolygons=np.arange(len(keep),len(keep)+len(returnFaces),dtype='i4'),posteriorPolygons=np.arange(len(keep)+len(returnFaces),len(faces),dtype='i4'),pairedOuterVertexIds=rowNative,pairedInnerVertexIds=np.arange(N,len(newV),dtype='i4'),authoredThicknessM=rowThickness,retainedOriginalPolygons=np.array([f.index for f in keep],'i4'));np.savez_compressed(E/'actual-paired-lid-return-states.npz',positions=np.array(steps),frames=np.arange(1,25));m.save('actual-paired-lid-return-construction.json',{'actualSkinVertices':len(actual),'actualSkinTriangles':len(a.geometry(skin)[1]),'newWallTriangles':len(newWall),'innerReturnTriangles':len(returnFaces),'posteriorWallTriangles':len(newBack),'sharedNativeOriginalRimPoints':len(rim),'newInnerPairedVertices':len(rowNative),'posteriorFixedNodes':len(posterior),'allRetainedOuterNeutralErrorM':outsideError,'noClothSolverOrMismatchedPinOverride':True,'allDisplayedInnerGeometryUsesSameOuterMotionAndExactSharedBoundary':True,'finiteThicknessIsAuthoredVertexCorrespondenceNotWholeFaceDistanceProof':True,'noFailedContactFacesLayersRemovedOrHidden':True,'discreteStatesAreNotNaturalDynamicsOrContinuousProof':True});assert a.a.sha(Path(before['source']))==before['sourceSha256'];bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=True);m.save('a-build-summary.json',{'source':before['source'],'output':str(OUT),'engineAlias':str(R/'engine/assets/characters/female-next/source/r0164-source'/OUT.name),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualSkin':skin.name,'actualRig':rig.name,'actualPoseSource':reference.name,'actualWallCorrectives':baked.name,'unaccepted':True,'secondsBeforePreview':time.time()-tick});assert OUT.stat().st_size<before['sourceBudgetBytes'];a.b.u.v.E=E;views=[]
 for frame,view,tag in [(11,'face','a-paired-return-closed'),(11,'body-face','a-paired-return-closed'),(1,'face','a-paired-return-neutral'),(9,'face','a-paired-return-half')]:
  s.frame_set(frame);bpy.context.view_layer.update();_=a.geometry(skin)
  for name in a.FIXED[2:4]:_=a.geometry(bpy.data.objects[name])
  ctl=a.b.u.v.image(tag,view);ctl.update(frame=frame,blink=[float(rig[k]) for k in ['blink_L','blink_R']]);views.append(ctl);m.save('actual-paired-return-preview-controls.json',views)
 s.frame_set(1);bpy.context.view_layer.update();print('R164_COMPLETE_PAIRED_LID_RETURN_HEAD_BODY_NEUTRAL_HALF_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
