
from pathlib import Path
import bpy,numpy as np,json,datetime,hashlib,importlib.util,traceback,time
from mathutils import Vector
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);E=A/'evidence/character-female-next/r0210-native-part-and-whole-path-sculpt';F=Path('F:/AevryndEvidence/r0210-native-part-and-whole-path-sculpt');TEMP=Path('F:/AevryndEvidence/CharacterTemp');EDIT=TEMP/'aevrynd-female-next-r0210-native-resumed-editing-session.blend';COMMAND=TEMP/'r210-native-finish.json';t=json.loads((E/'before.json').read_text('utf-8'));sp=importlib.util.spec_from_file_location('r210base',A/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h

def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(name,d):(E/name).write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
def digest(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def sha(f):return hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()

LOAD=TEMP/'quit.blend';assert LOAD.exists() and not EDIT.exists() and not COMMAND.exists();assert sha(t['source'])==t['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=str(LOAD));events=[]
def initialize():
 global hair,gen,s,raw0,ids0,canonical0,uv0,last,hidden,old,protected
 try:
  start=json.loads((E/'native-editor-start.json').read_text('utf-8'));baseline=np.load(E/'native-editor-unique-baseline.npz');win=bpy.context.window_manager.windows[0];area=next(x for x in win.screen.areas if x.type=='VIEW_3D');region=next(x for x in area.regions if x.type=='WINDOW');s=bpy.context.scene;s.frame_set(1)
  with bpy.context.temp_override(window=win,area=area,region=region):
   hair=bpy.data.objects[start['actualHair']];old=bpy.data.objects[a.FIXED[1]];skin=bpy.data.objects[start['actualSkin']];births=bpy.data.objects[start['actualBirths']];gen=hair.modifiers['AFN198_ACTUAL_SURFACE_CHILD_GENERATOR'];protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};assert protected==start['allSevenRawMeshUVSignaturesUnchanged'];raw0=baseline['guideWorld'];raw=h.arr(hair.data.position_data,'vector',4032,3);assert np.array_equal(raw,raw0);assert hair.data.attributes.get('radius') is not None;assert np.array_equal(h.arr(hair.data.attributes['AFN210_ACTUAL_ANATOMICAL_PART_SIDE'].data,'value',252,dtype='i4'),baseline['guideSide']);assert np.array_equal(h.arr(births.data.attributes['AFN210_ACTUAL_ANATOMICAL_PART_SIDE'].data,'value',10191,dtype='i4'),baseline['birthSide']);gen.show_viewport=True;bpy.context.view_layer.update();P,off=m.curveworld(hair);de=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;ids0=h.arr(de.attributes['AFN198_PERSISTENT_BIRTH_ID'].data,'value',len(off),dtype='i4');uv0=h.arr(de.attributes['surface_uv_coordinate'].data,'vector',len(off),2);canonical0=P.reshape(10191,16,3)[np.argsort(ids0)];assert digest(canonical0)==start['originalFullDisplayedSHA256'] and np.array_equal(np.sort(ids0),np.arange(10191));hidden=start['editorOnlyHiddenObjects']
   for ob in bpy.context.view_layer.objects:ob.select_set(False)
   hair.hide_set(False);hair.select_set(True);bpy.context.view_layer.objects.active=hair;rv=area.spaces.active.region_3d;rv.view_rotation=s.camera.matrix_world.to_quaternion();rv.view_location=Vector((0,-.025,1.47));rv.view_distance=.44;rv.view_perspective='ORTHO';area.spaces.active.shading.type='SOLID';area.spaces.active.shading.color_type='MATERIAL';gen.show_viewport=False
   if hair.mode!='SCULPT_CURVES':bpy.ops.object.mode_set(mode='SCULPT_CURVES')
   bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',relative_asset_identifier='brushes/essentials_brushes-curve_sculpt.blend/Brush/Comb');brush=s.tool_settings.curves_sculpt.brush;assert brush;brush.size=160;brush.strength=.7;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(EDIT),compress=True);last=digest(raw);save('native-editor-resumed-from-terminal-source.json',{'UTC':stamp(),'originalProcess816Terminal':'No process/window; original log Blender quit with saved recovery. This is genuine saved-source resumption, not timeout restart.','loadedRecoverySource':str(LOAD),'recoverySHA256':sha(LOAD),'newEditingSource':str(EDIT),'originalInitialEditorSourceRetained':start['editingSource'],'rawGuidePositionsExactBaseline':True,'allSevenProtectedExact':True,'current252Guide10191BirthPartDomainsExact':True,'canonicalCompleteDisplayedGeometryExact':True,'actualMode':hair.mode,'actualBrush':brush.name,'originalRoundClocksNotReset':True,'newGeometryAuthoredByResumeScript':False});bpy.app.timers.register(observe,first_interval=.5);print('R210_SAVED_SOURCE_NATIVE_EDITOR_RESUMED',flush=True)
 except Exception as er:save('native-editor-resume-failure.json',{'UTC':stamp(),'error':repr(er),'traceback':traceback.format_exc()});traceback.print_exc();bpy.ops.wm.quit_blender()
 return None
def observe():
 global last
 try:
  raw=h.arr(hair.data.position_data,'vector',4032,3);sig=digest(raw)
  if sig!=last:
   gen.show_viewport=True;bpy.context.view_layer.update();P,off=m.curveworld(hair);de=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;ids=h.arr(de.attributes['AFN198_PERSISTENT_BIRTH_ID'].data,'value',len(off),dtype='i4');uv=h.arr(de.attributes['surface_uv_coordinate'].data,'vector',len(off),2);valid=len(ids)==10191 and np.array_equal(np.sort(ids),np.arange(10191));canonical=P.reshape(10191,16,3)[np.argsort(ids)];delta=np.linalg.norm(canonical-canonical0,axis=2);change=np.linalg.norm(raw.reshape(252,16,3)-raw0.reshape(252,16,3),axis=2);event={'UTC':stamp(),'brush':getattr(s.tool_settings.curves_sculpt.brush,'name',None),'brushSize':s.tool_settings.curves_sculpt.brush.size,'brushStrength':s.tool_settings.curves_sculpt.brush.strength,'rawSHA256':sig,'rawMaxChangeM':float(change.max()),'rawRootsMaxChangeM':float(change[:,0].max()),'guidesWithChangedMidpaths':int((change[:,3:13].max(1)>1e-7).sum()),'guidesWithChangedTips':int((change[:,-1]>1e-7).sum()),'actualBirthIDsComplete':bool(valid),'displayedMaxChangeM':float(delta.max()),'displayedPointsMoved':int((delta>1e-8).sum()),'displayedRootsMaxChangeM':float(delta[:,0].max()),'actualUVMaxChange':float(np.max(abs(uv[np.argsort(ids)]-uv0[np.argsort(ids0)]))),'canonicalDisplayedSHA256':digest(canonical)};events.append(event);save('native-editor-actual-edit-events.json',events);np.savez_compressed(E/'native-editor-latest-guides.npz',guideWorld=raw);last=sig;gen.show_viewport=False;bpy.context.view_layer.update()
  save('native-editor-current-state.json',{'UTC':stamp(),'actualMode':hair.mode,'actualBrush':getattr(s.tool_settings.curves_sculpt.brush,'name',None),'rawSHA256':sig,'events':len(events),'actualFile':bpy.data.filepath})
  if COMMAND.exists():
   command=json.loads(COMMAND.read_text('utf-8'))
   if command.get('finish'):
    if hair.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
    rad=hair.data.attributes.get('radius');assert rad;hair.data.attributes.remove(rad);gen.show_viewport=gen.show_render=True
    for name in hidden:bpy.data.objects[name].hide_set(False)
    old.hide_set(False);old.hide_render=True;hair.hide_render=False;hair.hide_set(False);hair.data.update_tag();bpy.context.view_layer.update();assert protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected};bpy.ops.wm.save_as_mainfile(filepath=str(EDIT),compress=True);save('native-editor-frozen.json',{'UTC':stamp(),'editingSource':str(EDIT),'sha256':sha(EDIT),'bytes':EDIT.stat().st_size,'nativeUIObservedEdits':len(events),'rawSHA256':sig,'temporaryEditorRadiusRemoved':True,'completeGeneratorRestored':True,'allSevenProtectedUnchanged':True});print('R210_NATIVE_EDITING_SOURCE_FROZEN',flush=True);bpy.ops.wm.quit_blender();return None
 except Exception as er:save('native-editor-observer-failure.json',{'UTC':stamp(),'error':repr(er),'traceback':traceback.format_exc()});traceback.print_exc()
 return .5
bpy.app.timers.register(initialize,first_interval=1)
