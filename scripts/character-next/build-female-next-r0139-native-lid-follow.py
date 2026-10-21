"""Author actual current skin/lash/wet-line native lid follow, not closing caps.
Source-native semantic margin chains establish geodesic weights and fixed corners.
The actual r138 eye bones drive new lid bones; no external handler or Rigify code.
"""
from pathlib import Path
import bpy,numpy as np,json,math,time,datetime,heapq,importlib.util
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0139-native-lid-follow';S=R/'engine/assets/characters/female-next/source';SRC=S/'r0138-source/aevrynd-female-next-r0138-b-native-socket-walls.blend';OUT=S/'r0139-source/aevrynd-female-next-r0139-a-native-lid-follow.blend'
sp=importlib.util.spec_from_file_location('r139base',Path(__file__).with_name('build-female-next-r0138-native-current-gaze.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);a.b.u.v.E=E
UPPER=[4760,5920,6065,6002,5993,5933,5982,5971,5960,6495];LOWER=[6106,10251,6182,6312,6319,6330,6338,6349,6361,6497]
SKIN=a.FIXED[0];ATTACH=[a.FIXED[2],a.FIXED[3]];STATIC=[a.FIXED[1],a.FIXED[4]]
REST='AFN139_STATIC_REST';BONES={(s,k):'AFN139_'+s+'_'+k+'_LID' for s in ['L','R'] for k in ['UPPER','LOWER']}
def save(n,x):
 (E/n).write_text(json.dumps(x,indent=2,default=lambda v:v.tolist() if isinstance(v,np.ndarray) else v.item() if isinstance(v,np.generic) else str(v))+'\n',encoding='utf-8')
def kdtree(P):
 t=KDTree(len(P))
 for i,p in enumerate(P):t.insert(Vector(p),i)
 t.balance();return t
def graph(P,edges):
 g=[[] for _ in P]
 for i,j in edges:
  w=float(np.linalg.norm(P[i]-P[j]));g[int(i)].append((int(j),w));g[int(j)].append((int(i),w))
 return g
def path(g,start,end):
 d={start:0.};prev={};heap=[(0.,start)]
 while heap:
  x,i=heapq.heappop(heap)
  if x!=d[i]:continue
  if i==end:break
  for j,w in g[i]:
   nd=x+w
   if nd<d.get(j,np.inf):d[j]=nd;prev[j]=i;heapq.heappush(heap,(nd,j))
 assert end in d;out=[end]
 while out[-1]!=start:out.append(prev[out[-1]])
 return out[::-1]
def chain(g,landmarks):
 out=[landmarks[0]]
 for j in landmarks[1:]:out+=path(g,out[-1],j)[1:]
 return np.array(out,dtype='i4')
def geodesic(g,seeds,support):
 dist=np.full(len(g),np.inf);owner=np.full(len(g),-1,dtype='i4');heap=[]
 for i,j in enumerate(seeds):dist[j]=0;owner[j]=i;heapq.heappush(heap,(0.,int(j)))
 while heap:
  d,i=heapq.heappop(heap)
  if d!=dist[i] or d>support:continue
  for j,w in g[i]:
   nd=d+w
   if nd<dist[j] and nd<=support:dist[j]=nd;owner[j]=owner[i];heapq.heappush(heap,(nd,j))
 return dist,owner
def components(ob):
 g=[[] for _ in ob.data.vertices]
 for e in ob.data.edges:i,j=e.vertices;g[i].append(j);g[j].append(i)
 seen=set();rows=[]
 for seed in range(len(g)):
  if seed in seen:continue
  seen.add(seed);ids=[seed];stack=[seed]
  while stack:
   for j in g[stack.pop()]:
    if j not in seen:seen.add(j);ids.append(j);stack.append(j)
  rows.append(np.array(ids,dtype='i4'))
 return rows
def bary(P,A,B,C):
 v0=B-A;v1=C-A;v2=P-A;d00=v0@v0;d01=v0@v1;d11=v1@v1;d20=v2@v0;d21=v2@v1;den=d00*d11-d01*d01;assert den>1e-25;v=(d11*d20-d01*d21)/den;w=(d00*d21-d01*d20)/den;return np.array([1-v-w,v,w])
def actual_triangle_anchor(P,tri):
 A,B,C=tri;v,res,rank,s=np.linalg.lstsq(np.column_stack([B-A,C-A]),P-A,rcond=None);bc=np.array([1-v.sum(),v[0],v[1]])
 if rank==2 and bc.min()>=0:return bc@tri,bc
 choices=[]
 for i,j in [(0,1),(1,2),(2,0)]:
  d=tri[j]-tri[i];dd=d@d;t=float(np.clip(((P-tri[i])@d)/dd,0,1)) if dd>0 else 0.;w=np.zeros(3);w[i]=1-t;w[j]=t;Q=w@tri;choices.append((float(np.sum((Q-P)**2)),Q,w))
 _,Q,w=min(choices,key=lambda row:row[0]);return Q,w
def bind(ob,weights,rig):
 assert not ob.modifiers and all(n not in ob.vertex_groups for n in [REST,*BONES.values()])
 assert np.isfinite(weights).all() and weights.min()>=0 and np.max(abs(weights.sum(1)-1))<1e-12
 names=[REST]+list(BONES.values())
 for col,n in enumerate(names):
  group=ob.vertex_groups.new(name=n)
  for i in np.flatnonzero(weights[:,col]>0):group.add([int(i)],float(weights[i,col]),'REPLACE')
 md=ob.modifiers.new('AFN139_ACTUAL_CURRENT_LID_FOLLOW','ARMATURE');md.object=rig;md.use_bone_envelopes=False;md.use_vertex_groups=True;md.use_deform_preserve_volume=False
def main():
 tick=time.time();assert not OUT.exists()
 if not (E/'direct-native-lid-authoring-start.json').exists():save('direct-native-lid-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalStartedUTC':'2026-10-21T22:26:00+00:00','action':'Direct native lid deform bones, semantic source margin/geodesic skin weights, actual lash island/wet-line skin triangle attachment weights. No generated cap/closure surface or old hidden-head control.'})
 else:save('minimal-anchor-repair-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalRoundAndAuthoringClockUnchanged':True,'priorTerminalHandle':57363,'noCandidateOrModelRoundRestart':True})
 bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[SKIN];assert not skin.modifiers and not skin.data.shape_keys;rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];protected=a.a.protected();raw={n:a.rawsig(bpy.data.objects[n]) for n in [SKIN]+ATTACH+a.MOVING+STATIC};neutral={n:a.geometry(bpy.data.objects[n]) for n in raw};W,T=neutral[SKIN];K=kdtree(W)
 source=np.load(R/'Evidence/character-female-next/r0127-native-lid-closure/native-head-topology.npz');P=source['world'];nativeGraph=graph(P,source['edges']);nativeChains={'UPPER':chain(nativeGraph,UPPER),'LOWER':chain(nativeGraph,LOWER)};edges=np.unique(np.sort(np.concatenate([T[:,[0,1]],T[:,[1,2]],T[:,[2,0]]]),axis=1),axis=0);g=graph(W,edges);weights=np.zeros((len(W),5));domains={};columns={key:i+1 for i,key in enumerate(BONES)}
 for side,sign in [('L',1),('R',-1)]:
  for kind,support in [('UPPER',.012),('LOWER',.008)]:
   reference=P[nativeChains[kind]].copy();reference[:,0]*=sign;mapped=[K.find(Vector(p)) for p in reference];ids=np.array([x[1] for x in mapped],dtype='i4');errors=np.array([x[2] for x in mapped]);assert errors.max()<.002,('Rebuilt anatomy diverged from semantic source chain',side,kind,errors.max());unique,indices=np.unique(ids,return_index=True);indices=np.sort(indices);ids=ids[indices];ref=reference[indices];arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(ref,axis=0),axis=1))];corner=np.sin(np.pi*arc/arc[-1])**2;dist,owner=geodesic(g,ids,support);valid=np.flatnonzero(np.isfinite(dist));t=np.clip(1-dist[valid]/support,0,1);fade=t*t*(3-2*t);weights[valid,columns[(side,kind)]]=fade*corner[owner[valid]]
   domains[side+'_'+kind]={'originalSourceMarginIds':nativeChains[kind],'sourceMarginWorld':reference,'actualSkinSeedIds':ids,'sourceToCurrentSeedDistanceMaxM':float(errors.max()),'sourceToCurrentSeedDistancesM':errors,'geodesicSupportM':support,'affectedActualSkinVertices':len(valid),'cornerAnchoring':'sin(pi*s)^2 along original three-dimensional native margin arc; both canthi zero influence.','noSourceCapOrOldClosedPoseUsed':True}
 total=weights[:,1:].sum(1);over=total>1;weights[over,1:]/=total[over,None];weights[:,0]=1-weights[:,1:].sum(1);weights=np.maximum(weights,0);weights/=weights.sum(1)[:,None]
 # Reconstruct native armature on the same original optical centres.
 bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');root=rig.data.edit_bones['AFN138_EYES_FRAME'];rest=rig.data.edit_bones.new(REST);rest.head=(0,0,0);rest.tail=(0,.02,0)
 for (side,kind),name in BONES.items():
  original=rig.data.edit_bones[a.bone_names()[side]];bone=rig.data.edit_bones.new(name);bone.head=original.head;bone.tail=original.tail;bone.roll=original.roll;bone.parent=root;bone.use_connect=False
 bpy.ops.object.mode_set(mode='OBJECT')
 for (side,kind),name in BONES.items():
  pb=rig.pose.bones[name];pb.rotation_mode='XYZ';fc=pb.driver_add('rotation_euler',0);driver=fc.driver;driver.type='SCRIPTED';v=driver.variables.new();v.name='eye_pitch';v.type='SINGLE_PROP';v.targets[0].id=rig;v.targets[0].data_path='pose.bones["'+a.bone_names()[side]+'"].rotation_euler[0]';driver.expression='eye_pitch * '+str(.75 if kind=='UPPER' else .35)
 bind(skin,weights,rig)
 # Bind each lash island at its actual closest source root/skin triangle;
 # the wet strip receives per-vertex triangle-barycentric skin influence.
 BVH=BVHTree.FromPolygons([Vector(p) for p in W],T.tolist(),all_triangles=True);attachments={};npz={'skinWeights':weights,'skinWorld':W,'skinTriangles':T}
 for n in ATTACH:
  ob=bpy.data.objects[n];V,F=neutral[n];aw=np.zeros((len(V),5));anchors=[];groups=components(ob) if n==ATTACH[0] else [np.array([i],dtype='i4') for i in range(len(V))]
  for ids in groups:
   nearest=[BVH.find_nearest(Vector(V[i])) for i in ids];j=int(np.argmin([r[3] for r in nearest]));point,normal,fi,distance=nearest[j];fi=int(fi);tri=T[fi];point,bc=actual_triangle_anchor(V[ids[j]],W[tri]);assert bc.min()>-1e-4 and bc.max()<1.0001;bc=np.clip(bc,0,1);bc/=bc.sum();distance=np.linalg.norm(point-V[ids[j]]);ww=bc@weights[tri];ww=np.maximum(ww,0);ww/=ww.sum();aw[ids]=ww;anchors.append({'vertices':ids,'rootVertex':int(ids[j]),'skinTriangle':fi,'skinTriangleVertices':tri,'barycentric':bc,'restSkinDistanceM':float(distance),'rootWorld':V[ids[j]],'restSkinAnchorWorld':np.array(point),'nativeBoneWeights':ww,'bindingScope':'BVH float candidate face, exact float64 closest triangle interior/edge anchor. Binding, not global minimum/contact evidence.'})
  bind(ob,aw,rig);attachments[n]={'nativeComponents':len(groups),'rigidComponentInfluence':n==ATTACH[0],'restAttachmentDistanceMaxM':max(x['restSkinDistanceM'] for x in anchors),'anchors':anchors};npz[n+'Weights']=aw
 scene.frame_set(1);bpy.context.view_layer.update();neutralErrors={n:float(np.linalg.norm(a.geometry(bpy.data.objects[n])[0]-neutral[n][0],axis=1).max()) for n in [SKIN]+ATTACH};assert max(neutralErrors.values())<8e-7
 for n in raw:assert a.rawsig(bpy.data.objects[n])==raw[n]
 for n in STATIC+a.MOVING:assert all(np.array_equal(x,y) for x,y in zip(a.geometry(bpy.data.objects[n]),neutral[n]))
 assert a.a.protected()==protected;rig['AFN139_operation']='Actual current skin/lash/wet-line native lid following from existing eye pitch; upper0.75/lower0.35 fixed initial engineering authoring factors, not physiological calibration. Native original gaze range retained; not blink or eye tracking. Need actual visual/contact judgment.';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False)
 np.savez_compressed(E/'native-current-lid-skinning.npz',**npz);save('native-lid-follow-construction.json',{'source':str(SRC),'actualSkin':SKIN,'rig':rig.name,'nativeLidBones':{s+'_'+k:v for (s,k),v in BONES.items()},'restBone':REST,'upperPitchFactor':.75,'lowerPitchFactor':.35,'factorsFixedBeforePreviewNotAParameterSweep':True,'actualSourceNativeDomains':domains,'actualAttachments':attachments,'neutralEvaluatedMaxErrorsM':neutralErrors,'allRawGeometryTopologyUVAndOriginalMaterialsRetained':True,'allOldR138ContactClaimsInvalidForMovedSkinLashWetLine':True,'reference':'Original actual artist lid margin topology and native Blender bone/weights; official Rigify face.skin_eye docs search reference for coupled upper/lower chains and adjustable follow, not code import or installed dependency.','referenceURL':'https://docs.blender.org/manual/en/5.2/addons/rigify/rig_types/face.html','referenceAccess':'Official search excerpts available; full page fetch402/staging403, not claimed read. No source code imported. Original source geometry is the actual authoring basis.','scope':'Actual native deform/control construction only; no appearance/operation/contact/runtime acceptance.'})
 save('a-build-summary.json',{'source':str(SRC),'output':str(OUT),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'actualSkin':SKIN,'actualRig':rig.name,'standardAction':rig.animation_data.action.name,'actualLidBones':list(BONES.values()),'actualAttachedObjects':ATTACH,'originalEyeGeometryAndNativeRangeUnchanged':True,'rawMeshTopologyUVExact':True,'neutralEvaluatedMaxErrorsM':neutralErrors,'secondsBeforePreview':time.time()-tick,'completeAppearanceOperationContactRuntimeUnaccepted':True});views=[]
 for v in ['face','body-face','profile','oblique','back']:
  views.append(a.b.u.v.image('a-native-lid-follow',v));save('a-view-controls.json',views)
 neutralControl=a.b.u.v.image('motion-neutral','face');motion=[]
 for f in [1,5,9,13,17,21,25,29,33,37,41,45,49]:
  scene.frame_set(f);bpy.context.view_layer.update();file=E/('actual-lid-gaze-face-frame-%03d.png'%f);scene.render.filepath=str(file);bpy.ops.render.render(write_still=True);motion.append({'frame':f,'file':str(file),'actualEyeEulerDegrees':a.angles(rig),'actualLidEulerDegrees':{n:[math.degrees(v) for v in rig.pose.bones[n].rotation_euler] for n in BONES.values()},'cameraLightExposure':neutralControl});save('actual-lid-gaze-motion-controls.json',motion)
 # Actual combined pose that falsified r138, unchanged eye angles.
 action=rig.animation_data.action;slot=rig.animation_data.action_slot;rig.animation_data.action=None
 for yaw,pitch in [(-20,10),(20,-10)]:
  for n in a.bone_names().values():rig.pose.bones[n].rotation_euler=(math.radians(-pitch),0,math.radians(yaw))
  bpy.context.view_layer.update();scene.render.filepath=str(E/('actual-lid-diagonal-yaw%+d-pitch%+d-face.png'%(yaw,pitch)));bpy.ops.render.render(write_still=True)
 for n in a.bone_names().values():rig.pose.bones[n].rotation_euler=(0,0,0)
 rig.animation_data.action=action;rig.animation_data.action_slot=slot;scene.frame_set(1);bpy.context.view_layer.update();assert a.a.protected()==protected;print('R139_ACTUAL_NATIVE_LID_FOLLOW_COMPLETE_HEAD_BODY_MOTION_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
