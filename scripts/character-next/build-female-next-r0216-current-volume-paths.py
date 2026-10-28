"""Complete actual-scalp curves routed in an inspected artist-volume scaffold.
The volume is a shape reference, never inferred follicle or card-UV flow.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,hashlib,importlib.util,heapq,time,shutil
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);E=A/'evidence/character-female-next/r0216-current-scalp-volume-paths';F=Path('F:/AevryndEvidence/r0216-current-scalp-volume-paths');t=json.loads((E/'before.json').read_text('utf-8'));tick=time.time()
def sha(f):return hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
def digest(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def save(name,q):(E/name).write_bytes((json.dumps(q,separators=(',',':'))+'\n').encode())
assert sha(t['source'])==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);spec=importlib.util.spec_from_file_location('r216base',A/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);a=m.a;h=m.h;old=bpy.data.objects[a.FIXED[1]];skin=bpy.data.objects[a.FIXED[0]];V,HT=a.geometry(old);W,ST=a.geometry(skin);protected={name:a.rawsig(bpy.data.objects[name]) for name in a.FIXED+a.MOVING};birth=np.load(E.parent/'r0198-native-birth-owned-scalp/native-surface-birth-lineage.npz');faces=birth['childBirthActualSkinFaces'];bary=birth['childBirthBC'];tri=ST[faces];assert np.array_equal(tri,birth['childBirthActualSkinTriangles']);roots=np.einsum('ni,nij->nj',bary,W[tri]);normals=np.cross(W[tri[:,1]]-W[tri[:,0]],W[tri[:,2]]-W[tri[:,0]]);normals/=np.linalg.norm(normals,axis=1)[:,None];N=len(roots);assert N==10191 and len(np.unique(roots.astype('f4'),axis=0))==N
# Construct a local3D rest-volume occupancy from real artist surface points
# and triangle interiors. No panel direction, UV direction or roots borrowed.
spacing=.0035;origin=V.min(0)-spacing*3;shape=np.ceil((V.max(0)-origin+spacing*3)/spacing).astype(int)+1;mask=np.zeros(tuple(shape),bool);samples=np.vstack([V,V[HT].mean(1)]);ij=np.rint((samples-origin)/spacing).astype(int);mask[tuple(ij.T)]=True
for k in range(2):
 expanded=mask.copy()
 for axis in range(3):expanded|=np.roll(mask,1,axis)|np.roll(mask,-1,axis)
 mask=expanded
mask[[0,-1],:,:]=False;mask[:,[0,-1],:]=False;mask[:,:,[0,-1]]=False;sf=birth['actualCurrentScalpFaces'];tree=BVHTree.FromPolygons(W.tolist(),ST[sf].tolist(),all_triangles=True);active=np.argwhere(mask);points=origin+active*spacing;signed=[]
for point in points:
 q,n,face,d=tree.find_nearest(Vector(point));signed.append(float((Vector(point)-q).dot(n)))
signed=np.array(signed);insideHypothesis=signed<-.0005;mask[tuple(active[insideHypothesis].T)]=False
# This local nearest-normal domain exclusion is NOT a global inside/contact
# test. It shapes new paths only; full evaluated contact remains separate.
active=np.argwhere(mask);z=origin[2]+np.arange(shape[2])*spacing;below=np.roll(mask,1,axis=2);terminal=mask&~below&(z[None,None,:]<1.395);assert terminal.sum()>20;D=np.full(tuple(shape),np.inf,'f4');parent=np.full(tuple(shape),-1,'i4');queue=[];strides=np.array([shape[1]*shape[2],shape[2],1]);flat=D.ravel();flatMask=mask.ravel();flatParent=parent.ravel();endIDs=np.flatnonzero(terminal)
for x in endIDs:flat[x]=0;heapq.heappush(queue,(0.,int(x)))
neighbor=[int(x) for x in np.r_[strides,-strides]]
while queue:
 d,i=heapq.heappop(queue)
 if d>float(flat[i])+1e-7:continue
 for off in neighbor:
  j=i+off
  if 0<=j<len(flat) and flatMask[j] and d+spacing<float(flat[j])-1e-7:
   flat[j]=d+spacing;flatParent[j]=i;heapq.heappush(queue,(float(flat[j]),j))
reachable=mask&np.isfinite(D);assert reachable.sum()>1000;distance=D.copy();distance[~reachable]=0
for k in range(16):
 total=distance.copy();count=np.ones(tuple(shape),'f4')
 for axis in range(3):
  for shift in [-1,1]:
   ok=reachable&np.roll(reachable,shift,axis);total+=np.where(ok,np.roll(distance,shift,axis),0);count+=ok
 distance=np.where(reachable,.5*distance+.5*total/count,0);distance[terminal]=0
gradient=[]
for axis in range(3):
 lo=np.where(np.roll(reachable,1,axis),np.roll(distance,1,axis),distance);hi=np.where(np.roll(reachable,-1,axis),np.roll(distance,-1,axis),distance);gradient.append((hi-lo)/(2*spacing))
gradient=np.stack(gradient,axis=-1);cells=np.argwhere(reachable);voxelWorld=origin+cells*spacing;kd=KDTree(len(cells))
for i,v in enumerate(voxelWorld):kd.insert(Vector(v),i)
kd.balance();startWorld=roots+normals*.0045;near=[kd.find(Vector(v)) for v in startWorld];seedDistance=np.array([x[2] for x in near]);seedCell=cells[[x[1] for x in near]];save('volume-construction-before-curves.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'spacingM':spacing,'gridShape':shape.tolist(),'reachableVoxels':int(reachable.sum()),'terminalVoxels':int(terminal.sum()),'actualSkinBirths':N,'allRootFaceTrianglesAndBarycentricPositionsVerified':True,'uniqueActualRootPositions':len(np.unique(roots.astype('f4'),axis=0)),'maximumNormalStartToReachableVolumeDistanceM':float(seedDistance.max()),'sourceArtistVolumeBounds':[V.min(0).tolist(),V.max(0).tolist()],'rootFlowNotInferredFromCardsOrUV':True,'newConstruction':'Current-space voxel geodesic potential and continuous descent, current Skin roots. Not radial envelope loft, borrowed whole-guide transfer or spine bank.','localNearestScalpNormalMaskIsHypothesisNotContactProof':True,'supportOriginalDeadline':t['supportDeadlineUTC'],'elapsedSinceJobSeconds':time.time()-tick})
np.savez_compressed(E/'current-space-volume-path-construction.npz',origin=origin,spacing=np.array(spacing),reachableMask=reachable,potential=distance.astype('f4'),rootSkinFaces=faces,rootBarycentric=bary,terminalMask=terminal)
def interpolate(field,P):
 g=(P-origin)/spacing;lo=np.floor(g).astype(int);lo=np.clip(lo,0,shape-2);frac=np.clip(g-lo,0,1);out=np.zeros((len(P),)+field.shape[3:],'f8')
 for dx in [0,1]:
  for dy in [0,1]:
   for dz in [0,1]:
    w=np.prod(np.where(np.array([dx,dy,dz]),frac,1-frac),axis=1);v=field[lo[:,0]+dx,lo[:,1]+dy,lo[:,2]+dz];out+=v*w.reshape((len(P),)+(1,)*(field.ndim-3))
 return out
P=startWorld.copy();paths=[roots.copy(),P.copy()];finished=np.zeros(N,bool);finishSteps=np.zeros(N,'i4');travel=np.linalg.norm(P-roots,axis=1);fallbacks=np.zeros(N,'i4')
for step in range(160):
 grad=interpolate(gradient,P);mag=np.linalg.norm(grad,axis=1);direction=-grad/np.maximum(mag[:,None],1e-20);blend=np.exp(-travel/.008);direction=direction*(1-blend[:,None])+normals*blend[:,None];direction/=np.maximum(np.linalg.norm(direction,axis=1)[:,None],1e-20);candidate=P+direction*.0025;ix=np.rint((candidate-origin)/spacing).astype(int);ix=np.clip(ix,0,shape-1);valid=reachable[tuple(ix.T)]&(mag>1e-8)
 for i in np.flatnonzero(~valid&~finished):
  point,cellID,delta=kd.find(Vector(P[i]));cell=cells[cellID];ni=flatParent[np.ravel_multi_index(tuple(cell),tuple(shape))]
  if ni>=0:target=origin+np.array(np.unravel_index(ni,tuple(shape)))*spacing;dv=target-P[i];candidate[i]=P[i]+dv/max(np.linalg.norm(dv),1e-20)*.0025
  else:candidate[i]=P[i]
  fallbacks[i]+=1
 value=interpolate(distance,P);done=(value<spacing*.65)&(P[:,2]<1.40);new=done&~finished;finishSteps[new]=step+1;finished|=done;candidate[finished]=P[finished];travel+=np.linalg.norm(candidate-P,axis=1);P=candidate;paths.append(P.copy())
paths=np.stack(paths,axis=1);K=80;result=np.empty((N,K,3),'f4');lengths=[]
for i,path in enumerate(paths):
 length=np.r_[0,np.cumsum(np.linalg.norm(np.diff(path,axis=0),axis=1))];keep=np.r_[True,np.diff(length)>1e-9];length=length[keep];path=path[keep];lengths.append(length[-1]);u=np.linspace(0,length[-1],K)
 for axis in range(3):result[i,:,axis]=np.interp(u,length,path[:,axis])
result[:,0]=roots.astype('f4');assert np.isfinite(result).all();save('complete-path-domain-observations.json',{'allCurvesRetained':N,'finishedAtRecordedTerminal':int(finished.sum()),'unfinishedIDs':np.flatnonzero(~finished).tolist(),'maximumVolumeSeedDistanceM':float(seedDistance.max()),'seedDistanceOver15mmIDs':np.flatnonzero(seedDistance>.015).tolist(),'curveLengthQuantilesM':np.quantile(lengths,[0,.1,.5,.9,1]).tolist(),'fallbackStepsMaximum':int(fallbacks.max()),'fallbackCurves':int(np.count_nonzero(fallbacks)),'knownUnfinishedOrLongSeedCasesNotHiddenOrWaived':True})
# A unique polygon atlas on the current Skin gives actual face/bary births
# unique persistent UVs without changing any original artist UV layer.
ed=skin.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;ed.calc_loop_triangles();triLoops=np.array([x.loops[:] for x in ed.loop_triangles]);polyIDs=np.array([x.polygon_index for x in ed.loop_triangles]);scalpPolys=np.unique(polyIDs[sf]);side=int(np.ceil(np.sqrt(len(scalpPolys))));chart=skin.data.uv_layers.new(name='AFN216_PERSISTENT_SCALP_POLYGON_CHART');allUV=np.zeros((len(skin.data.loops),2),'f4')
for j,pi in enumerate(scalpPolys):
 polygon=skin.data.polygons[int(pi)];loops=list(polygon.loop_indices);n=len(loops);corners=np.array([[0,0],[1,0],[1,1],[0,1]],'f4') if n==4 else np.array([[0,0],[1,0],[0,1]],'f4') if n==3 else np.column_stack([.5+.5*np.cos(np.arange(n)*2*np.pi/n),.5+.5*np.sin(np.arange(n)*2*np.pi/n)]);allUV[loops]=(np.array([j%side,j//side])+.05+.9*corners)/side
chart.data.foreach_set('uv',allUV.ravel());rootUV=np.einsum('ni,nij->nj',bary,allUV[triLoops[faces]]).astype('f4');assert len(np.unique(rootUV,axis=0))==N
cu=bpy.data.hair_curves.new('AFN216_EXPLICIT_COMPLETE_CURRENT_SCALP_ROOT_TIP_CURVES');cu.add_curves([K]*N);cu.position_data.foreach_set('vector',result.ravel());cu.surface=skin;cu.surface_uv_map=chart.name;hair=bpy.data.objects.new('AFN216_ACTUAL_CURRENT_VOLUME_PATH_GROOM',cu);s.collection.objects.link(hair)
for name,typ,domain,values,prop in [('AFN216_PERSISTENT_CURVE_ID','INT','CURVE',np.arange(N,dtype='i4'),'value'),('AFN216_ACTUAL_SCALP_TRIANGLE_ID','INT','CURVE',faces.astype('i4'),'value'),('AFN216_ACTUAL_SCALP_BARYCENTRIC','FLOAT_VECTOR','CURVE',bary.astype('f4'),'vector'),('surface_uv_coordinate','FLOAT2','CURVE',rootUV,'vector')]:at=cu.attributes.new(name,typ,domain);at.data.foreach_set(prop,values.ravel())
at=cu.attributes.get('radius') or cu.attributes.new('radius','FLOAT','POINT');radii=np.tile(np.linspace(.000055,.000015,K,dtype='f4'),N);at.data.foreach_set('value',radii);mat=bpy.data.materials.new('AFN216_FIXED_BROWN_PHYSICAL_FIBRE');mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear();shader=nodes.new('ShaderNodeBsdfHairPrincipled');shader.parametrization='COLOR';shader.inputs['Color'].default_value=(.055,.020,.009,1);shader.inputs['Roughness'].default_value=.35;shader.inputs['Radial Roughness'].default_value=.45;output=nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(shader.outputs[0],output.inputs['Surface']);cu.materials.append(mat)
hair.hide_render=False;hair.hide_set(False);old.hide_render=True
for ob in s.objects:
 if ob.type=='CURVES' and ob!=hair:ob.hide_render=True
cu.update_tag();bpy.context.view_layer.update();actual,offset=m.curveworld(hair);assert len(actual)==N*K and len(offset)==N;assert np.linalg.norm(actual[offset]-roots,axis=1).max()<3e-6;nowRaw={name:a.rawsig(bpy.data.objects[name]) for name in protected}
for name,signature in protected.items():
 assert signature['vertices']==nowRaw[name]['vertices'] and signature['triangles']==nowRaw[name]['triangles']
 for layer,hashValue in signature['uv'].items():assert nowRaw[name]['uv'][layer]==hashValue
save('complete-current-space-rooted-construction.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actualHair':hair.name,'actualSkin':skin.name,'actualCurves':N,'actualPoints':len(actual),'pointsPerCurve':K,'nativeCurveIDsComplete':True,'uniqueRootUVs':N,'newActualSkinChart':chart.name,'allOriginalRawGeometryAndUVLayersUnchanged':True,'protectedOriginalRawSignatures':protected,'allCurveRootPositionsMatchActualScalpBarycentricM':float(np.linalg.norm(actual[offset]-roots,axis=1).max()),'actualCurveWorldFloat32SHA256':digest(actual.astype('f4')),'rawCurvePointSHA256':digest(result),'actualSurfaceUVSHA256':digest(rootUV),'rootAncestrySource':'r0198 actual currentSkin triangle/bary sampling only; foreign guide paths/styles/frames not used.','styleReference':'Original artist Hair vertices/triangle centres used only as current-space rest volume scaffold.','fixedRadiusMetres':[.000055,.000015],'fixedMaterial':'PrincipledHair COLOR[.055,.020,.009],roughness.35,radial.45; no appearance parameter sweeps.','naturalAppearanceContactsMotionRuntimeUnaccepted':True,'secondsBeforeFullPreview':time.time()-tick})
captures=[];recorded=json.loads((E.parent/'r0214-native-display-hair-modal-motion/actual-render-pre-capture-states.json').read_text('utf-8'))
def image(tag,view):
 state=next(x for x in recorded if x['output'].endswith('-'+view+'.png'));s.camera.matrix_world=Matrix(state['cameraMatrixWorld']);s.camera.data.type='PERSP';s.camera.data.lens=state['lens'];s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG';s.render.filepath=str(F/f'matched-{tag}-{view}.png');captures.append({'frame':s.frame_current,'file':s.render.filepath,'actualHair':hair.name,'newVisible':not hair.hide_render,'oldVisible':not old.hide_render,'cameraMatrixWorld':state['cameraMatrixWorld'],'lens':state['lens'],'samples':s.cycles.samples,'seed':s.cycles.seed,'exposure':s.view_settings.exposure,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'captureStateNotRenderDepsgraphProof':True});save('actual-pre-capture-states.json',captures);bpy.ops.render.render(write_still=True)
hair.hide_render=True;old.hide_render=False
for v in ['face','body-face']:image('baseline-original-working-hair',v)
hair.hide_render=False;old.hide_render=True
for v in ['face','body-face','profile','back']:image('current-space-rooted-path-groom',v)
outdir=A/'assets-source/aevrynd-character/female-next/r0216-source';outdir.mkdir();out=outdir/'aevrynd-female-next-r0216-current-space-rooted-path-groom.blend';review=F/out.name;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(review),compress=True);shutil.copyfile(review,out);assert out.stat().st_size<t['sourceBudgetBytes']
for file in F.glob('matched-*.png'):shutil.copyfile(file,E/file.name)
save('build-summary.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'output':str(out),'userReviewSource':str(review),'sha256':sha(out),'bytes':out.stat().st_size,'actualHair':hair.name,'actualSkin':skin.name,'actualCurves':N,'actualPoints':N*K,'pointsPerCurve':K,'allActualRootIDsUVsComplete':True,'oneCompleteCandidate':True,'elapsedJobSeconds':time.time()-tick,'unaccepted':True});print('R216_COMPLETE_ACTUAL_SCALP_VOLUME_PATH_GROOM_AND_VIEWS_SAVED',flush=True)
