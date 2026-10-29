from pathlib import Path
import bpy,numpy as np,json,datetime,hashlib,importlib.util,traceback
from mathutils import Matrix,Vector
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);E=A/'evidence/character-female-next/r0220-native-direct-lock-sculpt';T=Path(p['temporaryWorkspace']);EDIT=T/'r220-native-session/aevrynd-female-next-r0220-native-editing.blend';COMMAND=T/'r220-native-control.json';t=json.loads((E/'before.json').read_text('utf-8'));b=json.loads((E.parent/'r0219-static-elastic-rod-rest/build-summary.json').read_text('utf-8'));sp=importlib.util.spec_from_file_location('r220base',A/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h;K=40;groups=[];events=[];lastCommand=None;activeName=None
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,q):(E/n).write_bytes((json.dumps(q,separators=(',',':'))+'\n').encode())
def sha(f):return hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
def digest(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
assert sha(t['source'])==t['sourceSha256'] and not EDIT.exists() and not COMMAND.exists();bpy.ops.wm.open_mainfile(filepath=t['source'])
def attr(data,name,typ,domain,value,prop='value'):
 at=data.attributes.new(name,typ,domain);at.data.foreach_set(prop,np.asarray(value).ravel());return at
def activate(name):
 global activeName
 win=bpy.context.window_manager.windows[0];area=next(x for x in win.screen.areas if x.type=='VIEW_3D');region=next(x for x in area.regions if x.type=='WINDOW')
 with bpy.context.temp_override(window=win,area=area,region=region):
  if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
  for ob in bpy.context.view_layer.objects:ob.select_set(False)
  ob=next(x['ob'] for x in groups if x['name']==name);ob.hide_set(False);ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.mode_set(mode='SCULPT_CURVES');bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',relative_asset_identifier='brushes/essentials_brushes-curve_sculpt.blend/Brush/'+brushName);s.tool_settings.curves_sculpt.brush.size=300;s.tool_settings.curves_sculpt.brush.strength=.75;activeName=name
def initialize():
 global s,skin,old,scalp,hidden,protected,initialSave,brushName
 try:
  s=bpy.context.scene;s.frame_set(1);skin=bpy.data.objects[b['actualSkin']];scalp=bpy.data.objects[b['actualScalp']];old=bpy.data.objects[a.FIXED[1]];prior=bpy.data.objects[b['actualHair']];V,off=m.curveworld(prior);P=V.reshape(10191,K,3).astype('f4');cu=prior.data;W,ST=a.geometry(skin);faces=h.arr(cu.attributes['AFN219_ACTUAL_SKIN_TRIANGLE_ID'].data,'value',10191,dtype='i4');bc=h.arr(cu.attributes['AFN219_ACTUAL_SKIN_BARYCENTRIC'].data,'vector',10191,3);local=h.arr(cu.attributes['AFN219_LOCAL_SCALP_TRIANGLE_ID'].data,'value',10191,dtype='i4');uv=h.arr(cu.attributes['surface_uv_coordinate'].data,'vector',10191,2);ids=h.arr(cu.attributes['AFN219_PERSISTENT_ROD_ID'].data,'value',10191,dtype='i4');rad=h.arr(cu.attributes['radius'].data,'value',10191*K).reshape(10191,K);roots=np.einsum('na,nac->nc',bc,W[ST[faces]]);assert np.array_equal(ids,np.arange(10191)) and np.linalg.norm(P[:,0]-roots,axis=1).max()<3e-6;surfaceMap=cu.surface_uv_map;material=prior.material_slots[0].material;assert surfaceMap in scalp.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.uv_layers;protected={name:a.rawsig(bpy.data.objects[name]) for name in a.FIXED+a.MOVING};zone=np.where(roots[:,1]<-.04,0,np.where(abs(roots[:,0])>.045,1,2));domain=zone*2+(roots[:,0]>=0);names=['L_FRONTAL','R_FRONTAL','L_TEMPORAL','R_TEMPORAL','L_OCCIPITAL','R_OCCIPITAL'];top=bpy.data.collections.new('AFN220_DIRECT_ROOT_OWNED_NATIVE_HAIR_DOMAINS');s.collection.children.link(top)
  for d,name in enumerate(names):
   indices=np.flatnonzero(domain==d);assert len(indices)>0;data=bpy.data.hair_curves.new('AFN220_DIRECT_FULL_PATHS_'+name);data.add_curves([K]*len(indices));initial=P[indices].copy();data.position_data.foreach_set('vector',initial.ravel());data.surface=scalp;data.surface_uv_map=surfaceMap;data.materials.append(material);ob=bpy.data.objects.new('AFN220_ACTUAL_DIRECT_HAIR_'+name,data);top.objects.link(ob);ob.hide_render=False;ob.hide_set(False)
   for an,typ,adomain,values,prop in [('AFN220_GLOBAL_CURVE_ID','INT','CURVE',ids[indices],'value'),('AFN220_ACTUAL_SKIN_TRIANGLE_ID','INT','CURVE',faces[indices],'value'),('AFN220_ACTUAL_SKIN_BARYCENTRIC','FLOAT_VECTOR','CURVE',bc[indices],'vector'),('AFN220_LOCAL_SCALP_TRIANGLE_ID','INT','CURVE',local[indices],'value'),('surface_uv_coordinate','FLOAT2','CURVE',uv[indices],'vector'),('radius','FLOAT','POINT',rad[indices],'value')]:attr(data,an,typ,adomain,values,prop)
   groups.append({'name':name,'ob':ob,'ids':indices,'initial':initial,'roots':initial[:,0].copy(),'uv':uv[indices].copy(),'last':digest(initial)})
  bpy.data.objects.remove(prior,do_unlink=True);hidden=[]
  for ob in bpy.context.view_layer.objects:
   ob.select_set(False)
   if ob.type in ['ARMATURE','CAMERA','LIGHT'] or (ob.hide_render and not ob.name.startswith('AFN220_')):
    if not ob.hide_get():hidden.append(ob.name);ob.hide_set(True)
  for ob in s.objects:
   if ob.type=='CURVES' and not ob.name.startswith('AFN220_'):ob.hide_render=True;ob.hide_set(True)
  old.hide_render=True;old.hide_set(True);scalp.hide_render=True;scalp.hide_set(True)
  with bpy.data.libraries.load('D:/SteamLibrary/steamapps/common/Blender/5.2/datafiles/assets/brushes/essentials_brushes-curve_sculpt.blend') as (fr,to):available=list(fr.brushes)
  brushName='Snake Hook' if 'Snake Hook' in available else 'Comb';save('native-tool-capability.json',{'UTC':stamp(),'actualAvailableNativeBrushes':available,'selectedBrush':brushName,'oneCapabilityCheckOnly':True,'fallback':'KnownnativeComb onlyifSnakeHook absent, sharesoriginalsupportbudget','notRadialNormalBlanks':True,'noGuideOnlyProxyOrChildGenerator':True,'actualDirectCurves':10191,'allActualPoints':10191*K})
  win=bpy.context.window_manager.windows[0];area=next(x for x in win.screen.areas if x.type=='VIEW_3D');rv=area.spaces.active.region_3d;recorded=json.loads((E.parent/'r0214-native-display-hair-modal-motion/actual-render-pre-capture-states.json').read_text('utf-8'));state=next(x for x in recorded if x['output'].endswith('-face.png'));rv.view_rotation=Matrix(state['cameraMatrixWorld']).to_quaternion();rv.view_location=Vector((0,-.025,1.43));rv.view_distance=.72;rv.view_perspective='ORTHO';area.spaces.active.shading.type='SOLID';area.spaces.active.shading.color_type='SINGLE';area.spaces.active.shading.single_color=(.25,.25,.25);area.spaces.active.overlay.show_floor=False;area.spaces.active.overlay.show_extras=False;activate(groups[0]['name']);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(EDIT),compress=True);initialSave=EDIT.stat().st_size;save('native-editor-start.json',{'UTC':stamp(),'editingSource':str(EDIT),'initialMutableBytes':initialSave,'actualSkin':skin.name,'actualScalp':scalp.name,'surfaceMap':surfaceMap,'domains':[{'name':g['name'],'object':g['ob'].name,'globalCurveIDs':g['ids'].tolist(),'curves':len(g['ids']),'initialRawSHA256':g['last']} for g in groups],'pointsPerCurve':K,'completeCurves':10191,'completePoints':10191*K,'allSevenProtectedRawSignatures':protected,'actualRenderEngine':s.render.engine,'actualHairPrimitive':s.render.hair_type,'nativeBrush':brushName,'editorOnlyHiddenObjects':hidden,'editorSolidSingleGrayNotAppearanceEvidence':True,'allDirectDomainGeometryVisibleNoOtherDomainHidden':True,'source219FailedPhysicsCalibrationAndLookNotAdopted':True,'fullFreePathsEditableNotProtected':True});bpy.app.timers.register(observe,first_interval=.75);print('R220_DIRECT_NATIVE_LOCK_SCULPT_READY',flush=True)
 except Exception as e:save('native-editor-initialization-failure.json',{'UTC':stamp(),'error':repr(e),'traceback':traceback.format_exc()});traceback.print_exc();bpy.ops.wm.quit_blender()
 return None
def observe():
 global lastCommand,brushName
 try:
  for g in groups:
   ob=g['ob'];N=len(g['ids']);raw=h.arr(ob.data.position_data,'vector',N*K,3).reshape(N,K,3);sig=digest(raw)
   if sig!=g['last']:
    bpy.context.view_layer.update();actual,off=m.curveworld(ob);delta=np.linalg.norm(raw-g['initial'],axis=2);ids=h.arr(ob.data.attributes['AFN220_GLOBAL_CURVE_ID'].data,'value',N,dtype='i4');uv=h.arr(ob.data.attributes['surface_uv_coordinate'].data,'vector',N,2);event={'UTC':stamp(),'domain':g['name'],'actualBrush':s.tool_settings.curves_sculpt.brush.name,'rawSHA256':sig,'completeCurves':N,'completePoints':N*K,'curvesWithChangedFreePaths':int((delta[:,1:].max(1)>1e-7).sum()),'curvesWithChangedTips':int((delta[:,-1]>1e-7).sum()),'changedPoints':int((delta>1e-7).sum()),'maximumRootChangeM':float(delta[:,0].max()),'actualDisplayedRootMaximumChangeM':float(np.linalg.norm(actual[off]-g['roots'],axis=1).max()),'actualGlobalIDsExact':bool(np.array_equal(ids,g['ids'])),'actualUVExact':bool(np.array_equal(uv,g['uv'])),'actualDisplayedWorldFloat32SHA256':digest(actual.astype('f4'))};events.append(event);save('native-editor-actual-edit-events.json',events);g['last']=sig
  if COMMAND.exists():
   command=COMMAND.read_text('utf-8')
   if command!=lastCommand:
    cmd=json.loads(command)
    if cmd.get('region') and cmd['region']!=activeName:activate(cmd['region'])
    if cmd.get('brush'):brushName=cmd['brush'];activate(activeName)
    lastCommand=command
    if cmd.get('finish'):
     if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
     for g in groups:g['ob'].hide_set(False);g['ob'].hide_render=False
     for name in hidden:bpy.data.objects[name].hide_set(False)
     old.hide_set(True);old.hide_render=True;scalp.hide_set(True);scalp.hide_render=True;bpy.context.view_layer.update();assert protected=={name:a.rawsig(bpy.data.objects[name]) for name in protected};bpy.ops.wm.save_as_mainfile(filepath=str(EDIT),compress=True);save('native-editor-frozen.json',{'UTC':stamp(),'editingSource':str(EDIT),'sha256':sha(EDIT),'bytes':EDIT.stat().st_size,'initialMutableBytes':initialSave,'nativeEditEvents':len(events),'domainSHA256s':{g['name']:g['last'] for g in groups},'fullCurves':10191,'pointsPerCurve':K,'allActualDomainGeometryVisible':True,'oneCandidate':True});print('R220_DIRECT_NATIVE_LOCK_SOURCE_FROZEN',flush=True);bpy.ops.wm.quit_blender();return None
  save('native-editor-current-state.json',{'UTC':stamp(),'actualFile':bpy.data.filepath,'activeDomain':activeName,'brush':brushName,'events':len(events),'allDomainCurves':{g['name']:len(g['ids']) for g in groups}})
 except Exception as e:save('native-editor-observer-failure.json',{'UTC':stamp(),'error':repr(e),'traceback':traceback.format_exc()});traceback.print_exc()
 return .75
bpy.app.timers.register(initialize,first_interval=1)
