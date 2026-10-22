"""Full artist lock families -> topological distance sections -> native volume.
No foreign groom, arbitrary source UV contours or proximity replacement masks.
Actual current-surface proximal construction replaces inconsistent source caps.
"""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time,datetime,heapq
from mathutils import Vector
from mathutils.bvhtree import BVHTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0168-source-lock-volumes';OUT=C/'assets-source/aevrynd-character/female-next/r0168-source/aevrynd-female-next-r0168-a-source-lock-volumes.blend'
sp=importlib.util.spec_from_file_location('r168base',R/'scripts/character-next/build-female-next-r0149-native-physical-groom.py');base=importlib.util.module_from_spec(sp);sp.loader.exec_module(base);a=base.a;h=base
def save(n,x):(E/n).write_bytes((json.dumps(x,indent=2)+'\n').encode())
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1e-30)
def hull2(x):
 p=sorted(set(map(tuple,np.round(x,12))))
 def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
 low=[];up=[]
 for q in p:
  while len(low)>1 and cross(low[-2],low[-1],q)<=0:low.pop()
  low.append(q)
 for q in reversed(p):
  while len(up)>1 and cross(up[-2],up[-1],q)<=0:up.pop()
  up.append(q)
 return np.array(low[:-1]+up[:-1])
def cross2(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]
def main():
 tick=time.time();timing=json.loads((E/'before.json').read_text());assert not OUT.exists() and a.a.sha(Path(timing['source']))==timing['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=timing['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[a.FIXED[0]];oldHair=bpy.data.objects[a.FIXED[1]];oldHair.material_slots[0].link='DATA';oldHair.hide_render=False;oldHair.hide_set(False);rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING if n!=oldHair.name};baseline={n:[a.a.hasharray(v) for v in a.geometry(bpy.data.objects[n])] for n in protected};W,T=a.geometry(skin);cache=np.load(R/'Evidence/character-female-next/r0150-authored-rooted-locks/actual-current-scalp.npz');assert np.array_equal(T,cache['triangles']) and np.linalg.norm(W-cache['world'],axis=1).max()<2e-6;scalp=cache['scalpFaces'];tree=BVHTree.FromPolygons(W.tolist(),T[scalp].tolist(),all_triangles=True)
 def root(p):
  hit,normal,fi,gap=tree.find_nearest(Vector(p));fi=int(scalp[fi]);tri=T[fi];B=W[tri];v=np.linalg.lstsq(np.column_stack((B[1]-B[0],B[2]-B[0])),np.array(hit)-B[0],rcond=None)[0];bc=np.array([1-v.sum(),*v]);return bc@B,tri,bc,np.array(normal),float(gap),fi
 src=np.load(E.parent/'r0165-native-hair-construction/actual-original-hair-geometry.npz');HP=src['positions'];HT=src['triangles'];component=src['components'];UV=src['uvPerVertex'];actualHP,actualHT=a.geometry(oldHair);assert np.linalg.norm(actualHP-HP,axis=1).max()<2e-6 and np.array_equal(actualHT,HT)
 families=[[48,98,160,346,394],[162,188,212,253]];selected=sum(families,[]);stations=np.linspace(0,1,65);allSections=[];familyStats=[]
 for group in families:
  sections=[[] for _ in stations];members=[]
  for ci in group:
   ids=np.where(component==ci)[0];lookup={int(v):i for i,v in enumerate(ids)};V=HP[ids];F=np.array([[lookup[int(x)] for x in t] for t in HT[component[HT[:,0]]==ci]],'i4');uv=UV[ids];rootID=np.where(uv[:,1]<uv[:,1].min()+.001)[0];tipID=np.where(uv[:,1]>uv[:,1].max()-.001)[0];edge=np.unique(np.sort(np.vstack((F[:,[0,1]],F[:,[1,2]],F[:,[2,0]])),axis=1),axis=0);adj=[[] for _ in V]
   for i,j in edge:
    length=float(np.linalg.norm(V[i]-V[j]));adj[i].append((int(j),length));adj[j].append((int(i),length))
   distance=np.full(len(V),np.inf);distance[rootID]=0.;queue=[(0.,int(i)) for i in rootID];heapq.heapify(queue)
   while queue:
    value,i=heapq.heappop(queue)
    if value>distance[i]:continue
    for j,length in adj[i]:
     new=value+length
     if new<distance[j]:distance[j]=new;heapq.heappush(queue,(new,j))
   assert np.isfinite(distance).all();tipDistance=float(np.median(distance[tipID]));field=distance/tipDistance;assert tipDistance>.15
   for k,t in enumerate(stations):
    if k==0:points=V[rootID]
    elif k==64:points=V[tipID]
    else:
     p=[]
     for i,j in edge:
      if (field[i]<=t<field[j]) or (field[j]<=t<field[i]):u=(t-field[i])/(field[j]-field[i]);p.append((1-u)*V[i]+u*V[j])
     points=np.array(p);assert len(points)>1,(ci,k)
    sections[k].extend(points)
   members.append({'component':ci,'vertices':len(V),'sourceRootIDs':ids[rootID].tolist(),'sourceTipIDs':ids[tipID].tolist(),'rootBounds':[V[rootID].min(0).tolist(),V[rootID].max(0).tolist()],'tipWorldMean':V[tipID].mean(0).tolist(),'geodesicRootToTipM':tipDistance,'field':'Actual connected source mesh edge-distance from known complete cap, normalized to original complete tip; UV used only to identify artist endpoint rows, not to create longitudinal fibre contours.'})
  allSections.append([np.array(p) for p in sections]);familyStats.append(members)
 save('direct-topological-volume-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':timing['startedUTC'],'changedPremise':'Two complete current-artist full root-to-tip families with exact component ownership, source-topology distance sections and three-dimensional convex section volumes replace local overlays/UV fragments/proximity deletion. Proximal source root caps vary by50mm in height and are rebuilt on actual current scalp before output.','sourceFamilies':familyStats,'sourceEvaluationMatchesSavedSourceGeometry':True,'oneCandidateOneStructuralMethod':True})
 rng=np.random.default_rng(1681128);paths=[];rTri=[];rBC=[];rootWorld=[];sourceRaw=[];volumeRecords=[];skin.data.calc_loop_triangles();skinuv=skin.data.uv_layers['AngelicaOriginalUV'];rootUV=[]
 for group,(sections,count) in enumerate(zip(allSections,[384,320])):
  centers=np.array([p.mean(0) for p in sections]);tangent=unit(np.gradient(centers,axis=0));director=np.array([0.,1.,0.]);frames=[]
  for j,t in enumerate(tangent):
   if j:
    v=np.cross(tangent[j-1],t);sn=np.linalg.norm(v);cs=np.clip(np.dot(tangent[j-1],t),-1,1)
    if sn>1e-12:k=v/sn;director=director*cs+np.cross(k,director)*sn+k*np.dot(k,director)*(1-cs)
   director=unit((director-t*np.dot(director,t))[None])[0];frames.append([director,np.cross(t,director)])
  frames=np.array(frames);disk=rng.random((count,2));theta=2*np.pi*disk[:,0];rho=np.sqrt(disk[:,1]);directions=np.column_stack((np.cos(theta),np.sin(theta)));raw=np.empty((count,65,3));sectionRows=[]
  for j,(center,points,frame) in enumerate(zip(centers,sections,frames)):
   plane=(points-center)@frame.T;polygon=hull2(plane);assert len(polygon)>=3;A=polygon;edge=np.roll(A,-1,axis=0)-A;denom=cross2(directions[:,None],edge[None]);safe=np.where(abs(denom)>1e-15,denom,np.nan);ray=cross2(A,edge)[None]/safe;seg=cross2(A[None],directions[:,None])/safe;valid=(ray>=0)&(seg>=0)&(seg<=1);radius=np.min(np.where(valid,ray,np.inf),axis=1);assert np.isfinite(radius).all();q=directions*(rho*radius)[:,None];raw[:,j]=center+q@frame;sectionRows.append({'station':j,'geodesicFraction':float(stations[j]),'sourceSectionPoints':len(points),'center':center.tolist(),'convexPlanePolygon':polygon.tolist(),'frame':frame.tolist()})
  # Current scalp root footprint rebuilt from measured source part extents.
  # Each fibre has a real root triangle and an explicit anatomical proximal
  # path. No late failed-strand removal or whole-groom normal push.
  rootY=(-.050,-.020) if group==0 else (-.035,-.005);rootX=.001+(.5+.5*directions[:,1]*rho)*.004;ys=rootY[0]+(.5+.5*directions[:,0]*rho)*(rootY[1]-rootY[0]);P=raw.copy();records=[]
  for i in range(count):
   rr,tri,bc,normal,gap,fi=root([rootX[i],ys[i],1.565]);rTri.append(tri);rBC.append(bc);rootWorld.append(rr);rootUV.append(bc@np.array([skinuv.data[k].uv[:] for k in skin.data.loop_triangles[fi].loops]));P[i,0]=rr
   # First24 sections are an authored scalp-following part/crown departure;
   # last8 blend into unchanged artist distal volume. This is a new proximal
   # construction domain, not a post-contact correction or tolerance change.
   for j in range(1,25):
    u=j/24.;seed=raw[i,j].copy();seed[:2]+=(rr[:2]-centers[0,:2])*(1-u)**2;pp,_,_,nn,gg,_=root(seed);height=.0035*np.sin(np.pi*.5*min(j/8,1));proximal=pp+nn*height;blend=np.clip((j-16)/8,0,1);blend=blend*blend*(3-2*blend);P[i,j]=(1-blend)*proximal+blend*raw[i,j]
   records.append({'rootTriangle':tri.tolist(),'rootBarycentric':bc.tolist(),'rootSeedToCurrentScalpM':gap})
  paths.extend(P);sourceRaw.extend(raw);volumeRecords.append({'family':group,'exactOriginalComponents':families[group],'fibres':count,'nativeStations':65,'sourceSections':sectionRows,'currentRootPatchXY':[[.001,rootY[0]],[.005,rootY[1]]],'rootOwnershipRecords':records,'proximalReconstructionStationDomain':[0,24],'distalArtistVolumeUnchangedStationDomain':[24,64],'sectionVolumeConvexHullNotFiniteContactProof':True})
 paths=np.array(paths,'f4');rTri=np.array(rTri,'i4');rBC=np.array(rBC);rootWorld=np.array(rootWorld);data=bpy.data.hair_curves.new('AFN168_EDITABLE_FULL_SOURCE_LOCK_VOLUME_DATA');data.add_curves([65]*len(paths));data.position_data.foreach_set('vector',paths.ravel());data.surface=skin;data.surface_uv_map='AngelicaOriginalUV';data.attributes.new('surface_uv_coordinate','FLOAT2','CURVE').data.foreach_set('vector',np.array(rootUV,'f4').ravel());data.attributes.new('radius','FLOAT','POINT').data.foreach_set('value',np.tile(np.linspace(.00004,.000006,65),len(paths)).astype('f4'));hair=bpy.data.objects.new('AFN168_ACTUAL_SOURCE_LOCK_VOLUME_FIBRES',data);s.collection.objects.link(hair);B=W[rTri];rootBase=(B*rBC[:,:,None]).sum(1);ax=unit(B[:,1]-B[:,0]);az=unit(np.cross(B[:,1]-B[:,0],B[:,2]-B[:,0]));ay=np.cross(az,ax);D=paths-rootBase[:,None];local=np.stack(((D*ax[:,None]).sum(2),(D*ay[:,None]).sum(2),(D*az[:,None]).sum(2)),axis=2);base.bind(hair,skin,rTri,rBC,local,paths)
 mat=bpy.data.materials.new('AFN168_NATIVE_FIBRE_SAME_REFERENCE_COLOR');mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();bs=n.new('ShaderNodeBsdfHairPrincipled');bs.parametrization='COLOR';bs.inputs['Roughness'].default_value=.35;bs.inputs['Radial Roughness'].default_value=.45;out=n.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(bs.outputs[0],out.inputs[0]);data.materials.append(mat)
 # Exact whole families removed before contacts and preview. All other source
 # polygons/positions/UV/normals retained; no selected-family opaque underlay.
 original=oldHair.data;mask=np.isin(component,selected);keep=[f for f in original.polygons if not mask[int(f.vertices[0])]];V=h.arr(original.vertices,'co',len(original.vertices),3);retained=bpy.data.meshes.new('AFN168_RETAINED_HAIR_OUTSIDE_EXACT_SOURCE_FAMILIES');retained.from_pydata(V.tolist(),[],[list(f.vertices) for f in keep]);retained.update()
 for ma in original.materials:retained.materials.append(ma)
 loops=np.array([li for f in keep for li in range(f.loop_start,f.loop_start+f.loop_total)],'i4')
 for i,f in enumerate(retained.polygons):f.material_index=keep[i].material_index;f.use_smooth=keep[i].use_smooth
 for uv in original.uv_layers:
  dst=retained.uv_layers.new(name=uv.name);dst.data.foreach_set('uv',h.arr(uv.data,'uv',len(uv.data),2)[loops].ravel());dst.active_render=uv.active_render;dst.active_clone=uv.active_clone
 retained.uv_layers.active_index=original.uv_layers.active_index;retained.normals_split_custom_set(h.arr(original.corner_normals,'vector',len(original.loops),3)[loops].tolist());oldHair.data=retained;oldHair.material_slots[0].link='DATA';bpy.context.view_layer.update();actual=a.q.hair(hair);error=float(np.linalg.norm(actual-paths.reshape(-1,3),axis=1).max());assert error<3e-6 and protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected} and baseline=={n:[a.a.hasharray(v) for v in a.geometry(bpy.data.objects[n])] for n in baseline}
 save('actual-source-lock-volume-construction.json',{'sourceFamilies':families,'actualNativeCurves':len(paths),'actualNativePoints':len(actual),'nativeSourceAndEvaluatedPointErrorM':error,'sourcePolygonsRemovedByExactFamilyIdentity':len(original.polygons)-len(keep),'noSelectedFamilyOpaqueUnderlayRetained':True,'otherCoarseHairMayStillOverlapNotWholeGroomAcceptance':True,'volumeRecords':volumeRecords,'anatomicalRootReconstructionNotCalibratedNaturalMotion':True,'finiteContactsAppearanceRuntimeUnaccepted':True});np.savez_compressed(E/'actual-source-lock-volume-lineage.npz',guideWorld=paths,sourceRawVolumeWorld=np.array(sourceRaw,'f4'),rootTriangles=rTri,rootBarycentric=rBC,rootWorld=rootWorld,retainedOriginalHairPolygons=np.array([f.index for f in keep],'i4'),replacedSourceComponents=np.array(selected,'i4'))
 bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=True);save('a-build-summary.json',{'source':timing['source'],'output':str(OUT),'engineAlias':str(R/'engine/assets/characters/female-next/source/r0168-source'/OUT.name),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualSkin':skin.name,'actualRig':rig.name,'actualHair':hair.name,'retainedSourceHair':oldHair.name,'nativeStrands':len(paths),'points':len(actual),'originalGazeAction':rig.animation_data.action.name,'rejectedOrAdoptedNotYetJudged':True,'secondsBeforePreview':time.time()-tick});assert OUT.stat().st_size<timing['sourceBudgetBytes'];a.b.u.v.E=E;views=[]
 for view in ['face','body-face','profile','back','oblique']:
  ctl=a.b.u.v.image('a-source-lock-volumes',view);ctl.update(frame=1,actualHair=hair.name,hairTypeAtActualCapture=s.render.hair_type,actualSamplesAtCapture=s.cycles.samples,actualResolutionAtCapture=[s.render.resolution_x,s.render.resolution_y]);views.append(ctl);save('actual-source-lock-preview-controls.json',views)
 print('R168_COMPLETE_TOPOLOGICAL_SOURCE_VOLUME_HEAD_BODY_PROFILE_BACK_OBLIQUE_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
