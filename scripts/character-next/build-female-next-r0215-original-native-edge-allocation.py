"""One native displayed-surface shell candidate; all artist panels retained.
Surface seams represent layer coupling, never follicles or strand physics.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,hashlib,importlib.util,shutil,time
from mathutils import Matrix,Vector
from mathutils.kdtree import KDTree
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);E=A/'evidence/character-female-next/r0215-native-surface-cloth-hair';F=Path('F:/AevryndEvidence/r0215-native-surface-cloth-hair');t=json.loads((E/'before.json').read_text('utf-8'));inspect=json.loads((E/'actual-panels-scalp-and-witness-correspondence.json').read_text('utf-8'));corr=np.load(E/'actual-panel-scalp-correspondence.npz');tick=time.time()
def sha(f):return hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
def save(name,q):(E/name).write_bytes((json.dumps(q,separators=(',',':'))+'\n').encode())
def digest(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
assert sha(t['source'])==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);spec=importlib.util.spec_from_file_location('r215base',A/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);a=m.a;h=m.h;old=bpy.data.objects[a.FIXED[1]];skin=bpy.data.objects[a.FIXED[0]];V,T=a.geometry(old);protected={name:a.rawsig(bpy.data.objects[name]) for name in a.FIXED+a.MOVING};panel=corr['panelIDs'];dist=corr['nearestScalpDistanceM'];N=int(panel.max()+1);assert N==470
# Inspect actual nearest vertex pairs between separate authored surface panels.
# These are explicit shell couplings; the scalp ancestry is stored separately.
kd=KDTree(len(V))
for i,v in enumerate(V):kd.insert(Vector(v),i)
kd.balance();pairs={}
for i,v in enumerate(V):
 for _,j,d in kd.find_n(Vector(v),32):
  pi,pj=int(panel[i]),int(panel[j])
  if pi==pj:continue
  key=tuple(sorted((pi,pj)))
  if key not in pairs or d<pairs[key][0]:pairs[key]=(float(d),i,j)
parent=np.arange(N+1)
def find(x):
 while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
 return x
pin=np.zeros(len(V),'f4');anchored=[]
for row in inspect['panels']:
 j=row['panelID']
 if row['minimumScalpDistanceM']<=.0075:
  ids=np.flatnonzero((panel==j)&(dist<=row['minimumScalpDistanceM']+.001));pin[ids]=1;parent[find(j)]=find(N);anchored.append(j)
seams=[]
for d,i,j in sorted(pairs.values()):
 pi,pj=find(int(panel[i])),find(int(panel[j]))
 if pi==pj:continue
 parent[pj]=pi;seams.append((int(i),int(j),float(d)))
unsupported=[j for j in range(N) if find(j)!=find(N)];save('actual-layer-shell-couplings.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'completeSurfacePanels':N,'directScalpOwnedPanels':len(anchored),'directScalpOwnedPanelIDs':anchored,'nativePinVertices':int(np.count_nonzero(pin)),'persistentScalpCorrespondence':str(E/'actual-panel-scalp-correspondence.npz'),'unrootedPanelsAfterExplicitLayerCoupling':unsupported,'seams':seams,'maximumSeamRestDistanceM':max(x[2] for x in seams),'representation':'470 artist surface panels connected by explicit closest-vertex minimum spanning layer seams to verified scalp-near panels. Couplings are thin-shell structural constraints, not real follicles/strand paths/friction. No panel deletion, no root projection or global displacement.','allPanelsKept':True,'sourceRestUnchanged':True});assert not unsupported,'Actual shell graph lacks scalp-owned path; do not invent attachment'
hair=old.copy();hair.data=old.data.copy();hair.name='AFN215_ACTUAL_LAYERED_SURFACE_CLOTH_HAIR';s.collection.objects.link(hair);hair.hide_render=False;hair.hide_set(False);hair.data.vertices.foreach_set('co',V.astype('f4').ravel());hair.matrix_world=Matrix.Identity(4);start=len(hair.data.edges);hair.data.edges.add(len(seams))
for k,(i,j,d) in enumerate(seams):hair.data.edges[start+k].vertices=(i,j)
hair.data.update();vg=hair.vertex_groups.new(name='AFN215_SCALP_OWNED_SURFACE_PINS');ids=np.flatnonzero(pin).tolist();vg.add(ids,1,'REPLACE')
for name,typ,values in [('AFN215_PERSISTENT_ARTIST_VERTEX_ID','INT',np.arange(len(V),dtype='i4')),('AFN215_ARTIST_SURFACE_PANEL_ID','INT',panel.astype('i4')),('AFN215_SCALP_SUPPORT_TRIANGLE_ID','INT',corr['nearestSkinTriangleIDs'].astype('i4')),('AFN215_SURFACE_PIN_WEIGHT','FLOAT',pin)]:at=hair.data.attributes.new(name,typ,'POINT');at.data.foreach_set('value',values)
cloth=hair.modifiers.new('AFN215_ACTUAL_LAYERED_SHELL_BENDING_AND_CONTACT','CLOTH');cs=cloth.settings;cs.quality=8;cs.mass=.000001;cs.air_damping=1;cs.tension_stiffness=80;cs.compression_stiffness=40;cs.shear_stiffness=30;cs.bending_stiffness=.6;cs.bending_model='ANGULAR';cs.vertex_group_mass=vg.name;cs.pin_stiffness=1;cs.tension_damping=8;cs.compression_damping=8;cs.shear_damping=8;cs.bending_damping=2;cc=cloth.collision_settings;cc.use_collision=True;cc.distance_min=.001;cc.collision_quality=4;cc.use_self_collision=True;cc.self_distance_min=.0005;cc.self_friction=5;cloth.point_cache.frame_start=1;cloth.point_cache.frame_end=73;cloth.point_cache.use_disk_cache=False
coll=bpy.data.collections.new('AFN215_ONLY_CURRENT_SKIN_COLLISION_DOMAIN');s.collection.children.link(coll);coll.objects.link(skin);cc.collection=coll
if not any(x.type=='COLLISION' for x in skin.modifiers):skin.modifiers.new('AFN215_ACTUAL_SKIN_CONTACT','COLLISION')
skin.collision.thickness_outer=.001;skin.collision.thickness_inner=.001;skin.collision.cloth_friction=5
# Field input is native Blender wind strength, not an asserted calibrated m/s.
bpy.ops.object.effector_add(type='WIND',location=(0,0,1.4));wind=bpy.context.object;wind.name='AFN215_NATIVE_WIND_FIELD';direction=Vector((3,.75,0));wind.rotation_euler=direction.to_track_quat('Z','Y').to_euler();wind.field.noise=0;wind.field.flow=1
for frame,strength in [(1,0),(8,0),(13,3),(20,3),(25,0),(73,0)]:wind.field.strength=strength;wind.field.keyframe_insert(data_path='strength',frame=frame)
for slot in wind.animation_data.action.slots:
 for layer in wind.animation_data.action.layers:
  for strip in layer.strips:
   bag=strip.channelbag(slot)
   if bag:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
s.render.fps=24;s.frame_start=1;s.frame_end=73;s.render.threads_mode='FIXED';s.render.threads=4;s.gravity=(0,0,-9.81)
for ob in s.objects:
 if ob.type=='CURVES' or ob.name=='AFN214_ACTUAL_DISPLAY_HAIR_MODAL_MESH':ob.hide_render=True
old.hide_render=True;states=[];captures=[];recorded=json.loads((E.parent/'r0214-native-display-hair-modal-motion/actual-render-pre-capture-states.json').read_text('utf-8'));peak=21
def image(tag,view):
 state=next(x for x in recorded if x['output'].endswith('-'+view+'.png'));s.camera.matrix_world=Matrix(state['cameraMatrixWorld']);s.camera.data.type='PERSP';s.camera.data.lens=state['lens'];s.render.image_settings.media_type='IMAGE';s.render.image_settings.file_format='PNG';s.render.filepath=str(F/f'matched-{tag}-{view}.png');captures.append({'frame':s.frame_current,'path':s.render.filepath,'cameraMatrixWorld':state['cameraMatrixWorld'],'lens':state['lens'],'exposure':s.view_settings.exposure,'samples':s.cycles.samples,'seed':s.cycles.seed,'actualWindFieldStrength':float(wind.field.strength),'actualHair':hair.name,'captureStateNotRenderDepsgraphProof':True});save('actual-pre-capture-states.json',captures);bpy.ops.render.render(write_still=True)
s.frame_set(1);bpy.context.view_layer.update();neutral,nt=a.geometry(hair);assert np.linalg.norm(neutral-V,axis=1).max()<3e-6 and len(nt)==81789
for view in ['face','body-face']:image('native-layered-shell-neutral',view)
outdir=A/'assets-source/aevrynd-character/female-next/r0215-source';outdir.mkdir();output=F/'aevrynd-female-next-r0215-native-layered-surface-hair.blend';out=outdir/output.name;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(output),compress=True);shutil.copyfile(output,out);assert out.stat().st_size<t['sourceBudgetBytes'];save('build-summary.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'output':str(out),'userReviewSource':str(output),'sha256':sha(out),'bytes':out.stat().st_size,'actualHair':hair.name,'actualSkin':skin.name,'actualWind':wind.name,'actualVertices':len(V),'actualTriangles':81789,'surfacePanels':470,'physicalLayerSeams':len(seams),'nativePinVertices':len(ids),'actualModifier':cloth.name,'motionFrames':73,'peakFrame':21,'settledFrame':73,'unbakedReplayRequired':True,'savedAtFrame':1,'oneCompleteCandidate':True,'unaccepted':True});print('R215_COMPLETE_NATIVE_LAYERED_SURFACE_SOURCE_NEUTRAL_SAVED',flush=True)
for frame in range(1,74):
 s.frame_set(frame);bpy.context.view_layer.update();ev,tri=a.geometry(hair);move=np.linalg.norm(ev-V,axis=1);pinmove=float(move[ids].max());finite=bool(np.isfinite(ev).all());row={'frame':frame,'actualNativeWindFieldStrength':float(wind.field.strength),'maximumNativeVertexMovementM':float(move.max()),'fixedSurfacePinMaximumMovementM':pinmove,'nativeWorldFloat32SHA256':digest(ev.astype('f4')),'allVerticesFinite':finite,'actualVertexCount':len(ev),'actualTriangleCount':len(tri)};states.append(row);save('actual-native-shell-simulation-progress.json',states);assert finite and len(ev)==57424 and len(tri)==81789 and pinmove<3e-6
 if frame==peak:
  for view in ['face','body-face','profile','back']:image('native-layered-shell-wind',view)
 if frame==73:
  for view in ['face','body-face']:image('native-layered-shell-settled',view)
print('R215_COMPLETE_NATIVE_SHELL_73FRAMES_AND_HEAD_BODY_PREVIEWS',flush=True)
for file in F.glob('matched-*.png'):shutil.copyfile(file,E/file.name)
save('complete-native-shell-operation.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceSHA256':sha(out),'sourceUnchanged':sha(out)==sha(output),'frames':states,'effectiveClothSettings':{k:getattr(cs,k) for k in ['quality','mass','air_damping','tension_stiffness','compression_stiffness','shear_stiffness','bending_stiffness','bending_model','vertex_group_mass']},'effectiveCollisionSettings':{k:getattr(cc,k) for k in ['distance_min','collision_quality','use_self_collision','self_distance_min','self_friction']},'nativeWindNotCalibratedMetresPerSecond':True,'fullNaturalStrandFiniteSelfContinuousRuntimeAcceptanceUnproved':True,'protectedRaw7Unchanged':protected=={name:a.rawsig(bpy.data.objects[name]) for name in protected},'elapsedSeconds':time.time()-tick})
