
from pathlib import Path
import bpy,numpy as np,json,datetime,hashlib,importlib.util,traceback,time
from mathutils import Vector
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);E=A/'evidence/character-female-next/r0210-native-part-and-whole-path-sculpt';F=Path('F:/AevryndEvidence/r0210-native-part-and-whole-path-sculpt');TEMP=Path('F:/AevryndEvidence/CharacterTemp');EDIT=TEMP/'aevrynd-female-next-r0210-native-editing-session.blend';COMMAND=TEMP/'r210-native-finish.json';t=json.loads((E/'before.json').read_text('utf-8'));sp=importlib.util.spec_from_file_location('r210base',A/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h

def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(name,d):(E/name).write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
def digest(x):return hashlib.sha256(np.ascontiguousarray(x).tobytes()).hexdigest()
def sha(f):return hashlib.file_digest(Path(f).open('rb'),'sha256').hexdigest()
assert sha(t['source'])==t['sourceSha256'] and not EDIT.exists() and not COMMAND.exists();bpy.ops.wm.open_mainfile(filepath=t['source']);events=[]
def initialize():
 global hair,gen,s,raw0,ids0,canonical0,uv0,last,hidden,old,protected
 try:
  win=bpy.context.window_manager.windows[0];area=next(x for x in win.screen.areas if x.type=='VIEW_3D');region=next(x for x in area.regions if x.type=='WINDOW');s=bpy.context.scene;s.frame_set(1)
  with bpy.context.temp_override(window=win,area=area,region=region):
   previous=bpy.data.objects['AFN209_ACTUAL_MEASURED_WORKING_HAIR_REST_GROOM'];previous.hide_render=True;previous.hide_set(True);hair=previous.copy();hair.data=previous.data.copy();hair.name='AFN210_ACTUAL_NATIVE_WHOLE_PATH_PART_GROOM';s.collection.objects.link(hair);hair.hide_render=False;hair.hide_set(False);old=bpy.data.objects[a.FIXED[1]];skin=bpy.data.objects[a.FIXED[0]];oldBirths=bpy.data.objects['AFN209_CURRENT_SKIN_OWNED_BIRTHS'];births=oldBirths.copy();births.data=oldBirths.data.copy();births.name='AFN210_CURRENT_SKIN_OWNED_PART_BIRTHS';s.collection.objects.link(births);births.hide_render=True;births.hide_set(True)
   for md in births.modifiers:
    if md.type=='NODES':md.node_group=md.node_group.copy()
   for md in hair.modifiers:
    if md.type=='NODES':md.node_group=md.node_group.copy()
   gen=hair.modifiers['AFN198_ACTUAL_SURFACE_CHILD_GENERATOR']
   for node in gen.node_group.nodes:
    if node.bl_idname=='GeometryNodeObjectInfo' and node.inputs['Object'].default_value==oldBirths:node.inputs['Object'].default_value=births
   protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING};raw0=h.arr(hair.data.position_data,'vector',4032,3).copy();gSide=(raw0.reshape(252,16,3)[:,0,0]>=0).astype('i4');bp=h.arr(births.data.vertices,'co',len(births.data.vertices),3);bSide=(bp[:,0]>=0).astype('i4')
   for d,domain,values in [(hair.data,'CURVE',gSide),(births.data,'POINT',bSide)]:
    at=d.attributes.new('AFN210_ACTUAL_ANATOMICAL_PART_SIDE','INT',domain);at.data.foreach_set('value',values)
   changed=[]
   for node in gen.node_group.nodes:
    if node.bl_idname=='GeometryNodeInputNamedAttribute' and node.inputs['Name'].default_value=='AFN204_CONNECTED_GROOM_DOMAIN':node.inputs['Name'].default_value='AFN210_ACTUAL_ANATOMICAL_PART_SIDE';changed.append(node.name)
   assert len(changed)>0
   bpy.context.view_layer.update();P,off=m.curveworld(hair);de=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;ids0=h.arr(de.attributes['AFN198_PERSISTENT_BIRTH_ID'].data,'value',len(off),dtype='i4');uv0=h.arr(de.attributes['surface_uv_coordinate'].data,'vector',len(off),2);assert len(off)==10191 and np.array_equal(np.sort(ids0),np.arange(10191));canonical0=P.reshape(10191,16,3)[np.argsort(ids0)];np.savez_compressed(E/'native-editor-unique-baseline.npz',guideWorld=raw0,guideSide=gSide,birthSide=bSide,birthIDs=ids0,birthUV=uv0)
   hidden=[]
   for ob in bpy.context.view_layer.objects:
    ob.select_set(False)
    if (ob.hide_render or ob.type in {'ARMATURE','LIGHT','CAMERA'}) and not ob.hide_get():hidden.append(ob.name);ob.hide_set(True)
   hair.hide_set(False);hair.select_set(True);bpy.context.view_layer.objects.active=hair;old.hide_set(True);old.hide_render=True;rv=area.spaces.active.region_3d;rv.view_rotation=s.camera.matrix_world.to_quaternion();rv.view_location=Vector((0,-.025,1.47));rv.view_distance=.44;rv.view_perspective='ORTHO';area.spaces.active.shading.type='SOLID';area.spaces.active.shading.color_type='MATERIAL';area.spaces.active.overlay.show_floor=False;gen.show_viewport=False
   if hair.data.attributes.get('radius'):raise AssertionError('Unexpected authored radius before editor')
   at=hair.data.attributes.new('radius','FLOAT','POINT');at.data.foreach_set('value',np.full(4032,.0001,'f4'));hair.data.update_tag();bpy.ops.object.mode_set(mode='SCULPT_CURVES');activation=bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',relative_asset_identifier='brushes/essentials_brushes-curve_sculpt.blend/Brush/Comb');brush=s.tool_settings.curves_sculpt.brush;assert brush;brush.size=160;brush.strength=.7;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(EDIT),compress=True);last=digest(raw0);save('native-editor-start.json',{'UTC':stamp(),'actualHair':hair.name,'actualBirths':births.name,'actualSkin':skin.name,'originalSource':t['source'],'editingSource':str(EDIT),'actualMode':hair.mode,'actualBrush':brush.name,'activation':str(activation),'viewportSize':[region.width,region.height],'rawSHA256':last,'originalFullDisplayedSHA256':digest(canonical0),'originalFullDisplayedUVSHA256':digest(uv0[np.argsort(ids0)]),'partGroupNamedNodesChanged':changed,'actualGuidePartCounts':np.bincount(gSide).tolist(),'actualBirthPartCounts':np.bincount(bSide).tolist(),'allBirthIDsRetained':True,'anatomicalPartNotPosteriorContinuityOrContactProof':True,'temporaryEditorRadiusM':.0001,'temporaryEditorRadiusMustBeRemovedBeforeCompleteCapture':True,'editorOnlyHiddenObjects':hidden,'allSevenRawMeshUVSignaturesUnchanged':protected,'source209FailedShapeNotAcceptedOrFrozen':True,'sameMaterialRadiusCountNativeGeneratorExceptExplicitPartDomain':True});bpy.app.timers.register(observe,first_interval=.5);print('R210_NATIVE_ACTUAL_UI_EDITOR_READY',flush=True)
 except Exception as er:save('native-editor-initialization-failure.json',{'UTC':stamp(),'error':repr(er),'traceback':traceback.format_exc()});traceback.print_exc();bpy.ops.wm.quit_blender()
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
