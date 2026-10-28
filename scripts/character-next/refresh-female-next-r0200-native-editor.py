"""Rebind after actual native Undo replaced Blender Object handles.
Temporary guide-only display radius is removed again before full candidate render.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,hashlib,importlib.util,traceback
from mathutils import Vector
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0200-native-curve-sculpt'
sp=importlib.util.spec_from_file_location('r200refresh',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);h=m.h
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,x):(E/n).write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
baseline=np.load(E/'resumed-native-editor-baseline.npz');raw0=baseline['guideWorld'];P0=baseline['evaluatedWorld'];ids0=baseline['birthIDs'];canonical0=np.empty((10191,16,3));canonical0[ids0]=P0.reshape(10191,16,3)
events=json.loads((E/'resumed-native-editor-edit-events.json').read_text('utf-8'));last=None
editArea=bpy.context.area;editWindow=bpy.context.window
def full(hair):
    gen=hair.modifiers['AFN198_ACTUAL_SURFACE_CHILD_GENERATOR'];flag=gen.show_viewport;gen.show_viewport=True;bpy.context.view_layer.update();P,off=m.curveworld(hair);d=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;ids=h.arr(d.attributes['AFN198_PERSISTENT_BIRTH_ID'].data,'value',len(off),dtype='i4');valid=len(ids)==10191 and np.array_equal(np.sort(ids),np.arange(10191)) and np.all(np.diff(np.r_[off,len(P)])==16);canonical=np.empty_like(canonical0)
    if valid:canonical[ids]=P.reshape(10191,16,3)
    gen.show_viewport=flag;bpy.context.view_layer.update();return P,off,ids,canonical,valid
def observe():
    global last
    try:
        hair=bpy.data.objects['AFN198_ACTUAL_SURFACE_BORN_NATIVE_GROOM'];raw=h.arr(hair.data.position_data,'vector',len(raw0),3);sig=hashlib.sha256(raw.tobytes()).hexdigest()
        if sig!=last:
            P,off,ids,canonical,valid=full(hair);delta=np.linalg.norm(canonical-canonical0,axis=2) if valid else None
            event={'UTC':stamp(),'actualMode':hair.mode,'actualBrush':getattr(bpy.context.scene.tool_settings.curves_sculpt.brush,'name',None),'rawSHA256':sig,'rawMaximumChangeFromBaselineM':float(np.linalg.norm(raw-raw0,axis=1).max()),'rawRootMaximumChangeFromBaselineM':float(np.linalg.norm(raw.reshape(252,16,3)[:,0]-raw0.reshape(252,16,3)[:,0],axis=1).max()),'completePersistentCurveIdentity':bool(valid),'evaluatedMaximumChangeFromBaselineM':float(delta.max()) if valid else None,'evaluatedRootsMaximumChangeFromBaselineM':float(delta[:,0].max()) if valid else None,'evaluatedPointsMovedAbove1e8M':int((delta>1e-8).sum()) if valid else None,'reboundActualObjectAfterUndo':True};events.append(event);save('resumed-native-editor-edit-events.json',events);np.savez_compressed(E/'resumed-native-editor-latest.npz',guideWorld=raw,evaluatedWorld=P,offsets=off,birthIDs=ids);last=sig
        save('resumed-native-editor-current-state.json',{'UTC':stamp(),'actualMode':hair.mode,'actualBrush':getattr(bpy.context.scene.tool_settings.curves_sculpt.brush,'name',None),'rawSHA256':sig,'events':len(events),'actualFile':bpy.data.filepath})
    except Exception as error:save('refreshed-native-editor-observer-failure.json',{'UTC':stamp(),'error':repr(error),'traceback':traceback.format_exc()})
    return 2.0
def initialize():
    try:
        import __main__
        old=getattr(__main__,'observe',None)
        if old is not None and old is not observe and bpy.app.timers.is_registered(old):bpy.app.timers.unregister(old)
        editArea.type='VIEW_3D';region=next(r for r in editArea.regions if r.type=='WINDOW')
        with bpy.context.temp_override(window=editWindow,area=editArea,region=region):
            hair=bpy.data.objects['AFN198_ACTUAL_SURFACE_BORN_NATIVE_GROOM'];gen=hair.modifiers['AFN198_ACTUAL_SURFACE_CHILD_GENERATOR'];gen.show_viewport=True;bpy.context.view_layer.update();raw=h.arr(hair.data.position_data,'vector',len(raw0),3);P,off,ids,canon,valid=full(hair)
            proof={'UTC':stamp(),'rawRestorationMaximumM':float(np.linalg.norm(raw-raw0,axis=1).max()),'completeRestorationMaximumM':float(np.linalg.norm(canon-canonical0,axis=2).max()) if valid else None,'completePersistentBirthIdentity':bool(valid),'observedUndoObjectHandleReplaced':True,'causeNotGuessed':'Actual native Undo replaced Object handles; the prior observer raised StructRNA of type Object has been removed. Current objects are freshly acquired by identity.'};save('real-native-comb-undo-restoration.json',proof);assert valid and proof['rawRestorationMaximumM']<3e-6 and proof['completeRestorationMaximumM']<3e-6
            hide=[]
            for ob in bpy.context.view_layer.objects:
                ob.select_set(False)
                if (ob.hide_render or ob.type in {'ARMATURE','LIGHT','CAMERA'}) and not ob.hide_get():hide.append(ob.name);ob.hide_set(True)
            hair.hide_set(False);hair.select_set(True);bpy.context.view_layer.objects.active=hair
            rad=hair.data.attributes.get('radius');radiusWasAbsent=rad is None
            if rad is not None:np.savez_compressed(E/'original-native-guide-radius.npz',radius=h.arr(rad.data,'value',len(rad.data)))
            else:rad=hair.data.attributes.new('radius','FLOAT','POINT')
            rad.data.foreach_set('value',np.full(len(raw0),.0001,'f4'));hair.data.update_tag();bpy.context.view_layer.update()
            _,_,_,after,ok=full(hair);assert ok and np.linalg.norm(after-canon,axis=2).max()<3e-6
            save('native-guide-edit-display-settings.json',{'UTC':stamp(),'rawRadiusAttributeInitiallyAbsent':radiusWasAbsent,'temporaryRawGuideRadiusM':.0001,'scope':'Guide-only sculpt display. Native complete generator already sets its own unchanged final radius. Remove/restore this raw attribute before complete preview/source freeze. Not a rendered radius change or acceptance rescue.','completePositionChangeM':float(np.linalg.norm(after-canon,axis=2).max()),'editViewOnlyHiddenObjects':hide})
            rv=editArea.spaces.active.region_3d;rv.view_rotation=bpy.context.scene.camera.matrix_world.to_quaternion();rv.view_location=Vector((0,-.025,1.47));rv.view_distance=.42;rv.view_perspective='ORTHO';editArea.spaces.active.shading.type='SOLID'
            bpy.ops.object.mode_set(mode='SCULPT_CURVES');bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',relative_asset_identifier='brushes/essentials_brushes-curve_sculpt.blend/Brush/Comb');bpy.context.scene.tool_settings.curves_sculpt.brush.size=180;bpy.context.scene.tool_settings.curves_sculpt.brush.strength=.7;gen.show_viewport=False;bpy.context.view_layer.update();observe();bpy.app.timers.register(observe,first_interval=2)
        print('R200_REAL_NATIVE_UNDO_RESTORATION_AND_EDIT_VIEW_READY',flush=True)
    except Exception as error:save('refreshed-native-editor-initialization-failure.json',{'UTC':stamp(),'error':repr(error),'traceback':traceback.format_exc()});traceback.print_exc()
    return None
bpy.app.timers.register(initialize,first_interval=1)
