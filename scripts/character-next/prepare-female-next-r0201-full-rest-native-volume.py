"""Resume the preserved native editor after actual storage/process changes.
Observe real UI strokes; never generate guide coordinates or replay failed EXEC.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,datetime,importlib.util,traceback
from mathutils import Vector
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0201-full-rest-native-volume'
EDIT=C/'assets-source/aevrynd-character/female-next/r0201-source/aevrynd-female-next-r0201-editing-session.blend'
sp=importlib.util.spec_from_file_location('r200resume',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);h=m.h
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,x):(E/n).write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
bpy.ops.wm.open_mainfile(filepath=json.loads((E/'before.json').read_text('utf-8'))['source'])
EDIT.parent.mkdir(parents=True,exist_ok=True)
events=[]
def initialize():
    global hair,gen,s,raw0,P0,off0,ids0,last
    try:
        win=bpy.context.window_manager.windows[0];area=next(a for a in win.screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW')
        with bpy.context.temp_override(window=win,area=area,region=region):
            s=bpy.context.scene;s.frame_set(1);hair=bpy.data.objects['AFN198_ACTUAL_SURFACE_BORN_NATIVE_GROOM'];gen=hair.modifiers['AFN198_ACTUAL_SURFACE_CHILD_GENERATOR']
            gen.show_viewport=gen.show_render=True
            editVisibility=[]
            for ob in bpy.context.view_layer.objects:
                ob.select_set(False)
                if ob.hide_render and not ob.hide_get():editVisibility.append(ob.name);ob.hide_set(True)
            hair.hide_set(False);hair.select_set(True);bpy.context.view_layer.objects.active=hair;bpy.context.view_layer.update()
            raw0=h.arr(hair.data.position_data,'vector',len(hair.data.position_data),3).copy();P0,off0=m.curveworld(hair);de=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;ids0=h.arr(de.attributes['AFN198_PERSISTENT_BIRTH_ID'].data,'value',len(off0),dtype='i4')
            np.savez_compressed(E/'resumed-native-editor-baseline.npz',guideWorld=raw0,evaluatedWorld=P0,offsets=off0,birthIDs=ids0)
            rv=area.spaces.active.region_3d;rv.view_rotation=s.camera.matrix_world.to_quaternion();rv.view_location=Vector((0,-.025,1.47));rv.view_distance=.42;rv.view_perspective='ORTHO';area.spaces.active.shading.type='SOLID';area.spaces.active.shading.color_type='MATERIAL';area.spaces.active.overlay.show_floor=False
            bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(EDIT),compress=True)
            bpy.ops.object.mode_set(mode='SCULPT_CURVES');active=bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',relative_asset_identifier='brushes/essentials_brushes-curve_sculpt.blend/Brush/Puff');brush=s.tool_settings.curves_sculpt.brush;assert brush is not None;brush.size=300;brush.strength=.8
            displayHide=[]
            for ob in bpy.context.view_layer.objects:
                if ob.type in {'ARMATURE','LIGHT','CAMERA'} and not ob.hide_get():displayHide.append(ob.name);ob.hide_set(True)
            rad=hair.data.attributes.get('radius');assert rad is None;rad=hair.data.attributes.new('radius','FLOAT','POINT');rad.data.foreach_set('value',np.full(len(raw0),.0001,'f4'));hair.data.update_tag()
            original=bpy.data.objects[m.a.FIXED[1]];original.hide_set(False);original.display_type='WIRE';original.show_in_front=False
            save('native-guide-edit-display-settings.json',{'rawRadiusAttributeInitiallyAbsent':True,'temporaryRawGuideRadiusM':.0001,'editViewOnlyHiddenObjects':editVisibility+displayHide,'referenceOnlyOriginalHairWire':True,'originalHairName':original.name,'originalHairDisplayTypeBefore':'TEXTURED','scope':'Guide-only display; remove raw radius, restore visibility/display type before candidate captures.'})
            gen.show_viewport=False;bpy.context.view_layer.update();last=hashlib.sha256(raw0.tobytes()).hexdigest()
            save('resumed-native-editor-start.json',{'UTC':stamp(),'actualFile':bpy.data.filepath,'actualMode':hair.mode,'actualBrush':brush.name,'brushActivation':str(active),'viewportSize':[region.width,region.height],'actualGuides':len(hair.data.curves),'actualCompleteCurves':len(off0),'rawSHA256':last,'editViewOnlyHiddenRenderDisabledObjects':editVisibility,'childGenerationDisabledOnlyForGuideEditing':True,'childGeneratorRestoredForEveryReadbackAndRequiredCompletePreview':True,'geometryAuthoredByThisScript':False,'previousGUIConfirmedMissing':True,'originalClockNotReset':True})
            bpy.app.timers.register(observe,first_interval=2)
        print('R201_FULL_REST_EDITOR_READY',flush=True)
    except Exception as error:save('resumed-native-editor-initialization-failure.json',{'UTC':stamp(),'error':repr(error),'traceback':traceback.format_exc()});traceback.print_exc()
    return None
def observe():
    global last
    try:
        raw=h.arr(hair.data.position_data,'vector',len(hair.data.position_data),3);sig=hashlib.sha256(raw.tobytes()).hexdigest()
        if sig!=last:
            editFlag=gen.show_viewport;gen.show_viewport=True;bpy.context.view_layer.update()
            P,off=m.curveworld(hair);de=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;ids=h.arr(de.attributes['AFN198_PERSISTENT_BIRTH_ID'].data,'value',len(off),dtype='i4');lengths=np.diff(np.r_[off,len(P)]);valid=len(ids)==10191 and np.array_equal(np.sort(ids),np.arange(10191)) and np.all(lengths==16)
            canonical0=np.empty((10191,16,3));canonical0[ids0]=P0.reshape(10191,16,3);canonical=np.empty_like(canonical0)
            if valid:canonical[ids]=P.reshape(10191,16,3)
            delta=np.linalg.norm(canonical-canonical0,axis=2) if valid else None
            event={'UTC':stamp(),'actualMode':hair.mode,'actualBrush':getattr(s.tool_settings.curves_sculpt.brush,'name',None),'brushSize':s.tool_settings.curves_sculpt.brush.size,'brushStrength':s.tool_settings.curves_sculpt.brush.strength,'rawSHA256':sig,'rawMaximumChangeFromBaselineM':float(np.linalg.norm(raw-raw0,axis=1).max()),'rawRootMaximumChangeFromBaselineM':float(np.linalg.norm(raw.reshape(252,16,3)[:,0]-raw0.reshape(252,16,3)[:,0],axis=1).max()),'completePersistentCurveIdentity':bool(valid),'evaluatedMaximumChangeFromBaselineM':float(delta.max()) if valid else None,'evaluatedRootsMaximumChangeFromBaselineM':float(delta[:,0].max()) if valid else None,'evaluatedPointsMovedAbove1e8M':int((delta>1e-8).sum()) if valid else None}
            events.append(event);save('resumed-native-editor-edit-events.json',events);np.savez_compressed(E/'resumed-native-editor-latest.npz',guideWorld=raw,evaluatedWorld=P,offsets=off,birthIDs=ids);last=sig;gen.show_viewport=editFlag;bpy.context.view_layer.update()
        save('resumed-native-editor-current-state.json',{'UTC':stamp(),'actualMode':hair.mode,'actualBrush':getattr(s.tool_settings.curves_sculpt.brush,'name',None),'brushSize':s.tool_settings.curves_sculpt.brush.size,'brushStrength':s.tool_settings.curves_sculpt.brush.strength,'rawSHA256':sig,'events':len(events),'actualFile':bpy.data.filepath})
    except Exception as error:save('resumed-native-editor-observer-failure.json',{'UTC':stamp(),'error':repr(error),'traceback':traceback.format_exc()})
    return 2.0
bpy.app.timers.register(initialize,first_interval=1)
