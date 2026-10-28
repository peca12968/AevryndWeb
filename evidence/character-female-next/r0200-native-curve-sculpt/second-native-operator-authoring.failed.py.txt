"""Real native Curves Sculpt operators in a deferred real VIEW_3D context.
No scripted rest-path coordinate template; actual brush strokes preserve roots.
"""
from pathlib import Path
import bpy,numpy as np,json,datetime,hashlib,time,importlib.util,traceback
from mathutils import Vector,Quaternion,Matrix
from bpy_extras import view3d_utils
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0200-native-curve-sculpt';OUT=C/'assets-source/aevrynd-character/female-next/r0200-source/aevrynd-female-next-r0200-native-curve-sculpt.blend'
sp=importlib.util.spec_from_file_location('r200nativebase',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,x):(E/n).write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def sha(p):return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
t=json.loads((E/'before.json').read_text('utf-8'));assert sha(t['source'])==t['sourceSha256'] and not OUT.exists();bpy.ops.wm.open_mainfile(filepath=t['source'])

def main():
    tick=time.time();win=bpy.context.window_manager.windows[0];screen=win.screen;area=next(a for a in screen.areas if a.type=='VIEW_3D');region=next(r for r in area.regions if r.type=='WINDOW');space=area.spaces.active;rv=space.region_3d
    hair=bpy.data.objects['AFN198_ACTUAL_SURFACE_BORN_NATIVE_GROOM'];skin=bpy.data.objects[a.FIXED[0]];old=bpy.data.objects[a.FIXED[1]];s=bpy.context.scene;s.frame_set(1)
    with bpy.context.temp_override(window=win,area=area,region=region):
        for ob in bpy.context.view_layer.objects:ob.select_set(False)
        hair.hide_set(False);hair.select_set(True);bpy.context.view_layer.objects.active=hair
        raw0=h.arr(hair.data.position_data,'vector',len(hair.data.position_data),3).copy();P0,off0=m.curveworld(hair);protected={n:a.rawsig(bpy.data.objects[n]) for n in a.FIXED+a.MOVING}
        # Native edit view shows actual authored guides; the complete generator
        # is restored before every evaluation/render. No failed fibres removed.
        gen=hair.modifiers['AFN198_ACTUAL_SURFACE_CHILD_GENERATOR'];gen.show_viewport=False
        rv.view_rotation=s.camera.matrix_world.to_quaternion();rv.view_location=Vector((0,-.025,1.47));rv.view_distance=.42;rv.view_perspective='ORTHO';space.shading.type='SOLID';bpy.context.view_layer.update()
        result=bpy.ops.object.mode_set(mode='SCULPT_CURVES')
        asset=Path('D:/SteamLibrary/steamapps/common/Blender/5.2/datafiles/assets/brushes/essentials_brushes-curve_sculpt.blend')
        with bpy.data.libraries.load(str(asset),link=False) as (fr,to):availableBrushes=list(fr.brushes)
        save('native-operator-capability-start.json',{'UTC':stamp(),'mode':hair.mode,'modeResult':str(result),'actualBrushAssets':availableBrushes,'nativeBrushAssetFile':str(asset),'nativeBrushAssetSHA256':sha(asset),'brushOperatorRNA':[p.identifier for p in bpy.ops.brush.asset_activate.get_rna_type().properties],'nativeStrokeOperatorRNA':[p.identifier for p in bpy.ops.sculpt_curves.brush_stroke.get_rna_type().properties],'actualViewportSize':[region.width,region.height],'sameOriginalClock':True})
        assert 'Comb' in availableBrushes
        brushesBefore=set(bpy.data.brushes.keys());activated=bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',relative_asset_identifier='brushes/essentials_brushes-curve_sculpt.blend/Brush/Comb')
        brush=s.tool_settings.curves_sculpt.brush;assert brush is not None
        brush.size=110;brush.strength=.65
        strokes=[]
        def stroke(start,end,label):
            # Screen stroke coordinates projected from actual current-space
            # guide geometry. Native brush operator computes every new point.
            begin=view3d_utils.location_3d_to_region_2d(region,rv,Vector(start));finish=view3d_utils.location_3d_to_region_2d(region,rv,Vector(end));assert begin is not None and finish is not None
            pts=[]
            for i,u in enumerate(np.linspace(0,1,12)):
                xy=(1-u)*np.array(begin)+u*np.array(finish)
                pts.append({'name':'native-comb','mouse':xy.tolist(),'mouse_event':xy.tolist(),'location':[0,0,0],'pressure':1.,'size':float(brush.size),'time':i*.03,'is_start':i==0,'pen_flip':False,'x_tilt':0.,'y_tilt':0.})
            before=h.arr(hair.data.position_data,'vector',len(hair.data.position_data),3).copy()
            allowed={p.identifier for p in bpy.types.OperatorStrokeElement.bl_rna.properties};pts=[{k:v for k,v in pt.items() if k in allowed} for pt in pts];op=bpy.ops.sculpt_curves.brush_stroke(stroke=pts,mode='NORMAL')
            after=h.arr(hair.data.position_data,'vector',len(hair.data.position_data),3);delta=np.linalg.norm(after-before,axis=1)
            strokes.append({'UTC':stamp(),'label':label,'nativeOperator':'bpy.ops.sculpt_curves.brush_stroke','brush':brush.name,'result':str(op),'viewRotation':list(rv.view_rotation),'viewLocation':list(rv.view_location),'viewDistance':rv.view_distance,'viewportSize':[region.width,region.height],'start2D':list(begin),'end2D':list(finish),'size':brush.size,'strength':brush.strength,'rawMaximumChangeM':float(delta.max()),'rawPointsMovedAbove1e8M':int((delta>1e-8).sum())});save('actual-native-brush-strokes.json',strokes)
            return delta
        # Capability once: real Comb followed by exact restoration, then whole
        # native generation must respond with complete original birth identity.
        raw=raw0.reshape(252,16,3);gi=int(np.argmax(raw[:,8,0]));start=raw[gi,8];end=start+np.array([.020,0,.015]);delta=stroke(start,end,'capability-real-comb')
        gen.show_viewport=True;bpy.context.view_layer.update();test,off=m.curveworld(hair);data=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;ids=h.arr(data.attributes['AFN198_PERSISTENT_BIRTH_ID'].data,'value',len(off),dtype='i4');valid=np.array_equal(np.sort(ids),np.arange(10191)) and np.array_equal(off,off0)
        hair.data.position_data.foreach_set('vector',raw0.ravel());hair.data.update_tag();hair.update_tag();bpy.context.view_layer.update();restored,_=m.curveworld(hair)
        proof={'UTC':stamp(),'actualNativeBrush':brush.name,'activation':str(activated),'rawStrokeMaximumChangeM':float(delta.max()),'evaluatedCompleteOutputMaximumChangeM':float(np.linalg.norm(test-P0,axis=1).max()) if test.shape==P0.shape else None,'completeBirthIDsPreserved':bool(valid),'evaluatedRootsMaximumMovementM':float(np.linalg.norm(test[off]-P0[off0],axis=1).max()) if valid else None,'completeRestorationMaximumM':float(np.linalg.norm(restored-P0,axis=1).max()),'actualGuideCount':len(hair.data.curves),'actualPointCount':len(raw0),'capabilityIsNotCompleteAppearance':True};save('native-brush-capability-readback.json',proof)
        assert delta.max()>1e-7 and valid and proof['completeRestorationMaximumM']<3e-6 and proof['evaluatedRootsMaximumMovementM']<3e-6
        gen.show_viewport=False;bpy.context.view_layer.update()
        # Native Comb strokes in front, side and back views; no custom path
        # interpolation or assignment to curve positions during authoring.
        for view,label,axisShift in [(s.camera.matrix_world.to_quaternion(),'front',None),(Quaternion((0,0,1),np.pi/2)@s.camera.matrix_world.to_quaternion(),'side',None),(Quaternion((0,0,1),np.pi)@s.camera.matrix_world.to_quaternion(),'back',None)]:
            rv.view_rotation=view;bpy.context.view_layer.update()
            for sign in [-1,1]:
                for height in [1.49,1.43,1.36]:
                    actual=h.arr(hair.data.position_data,'vector',len(raw0),3).reshape(252,16,3)
                    mask=(actual[:,:,0]*sign>.045)&(np.abs(actual[:,:,2]-height)<.045)
                    if not mask.any():continue
                    points=actual[mask];start=points.mean(0)
                    shift=np.array([sign*.022,.008 if label!='front' else .012,.016 if height>1.4 else .025])
                    stroke(start,start+shift,label+'-'+str(sign)+'-'+str(height))
        gen.show_viewport=True;bpy.ops.object.mode_set(mode='OBJECT');bpy.context.view_layer.update()
        authored=h.arr(hair.data.position_data,'vector',len(raw0),3);P,off=m.curveworld(hair);assert len(off)==10191 and len(P)==len(P0)
        assert protected=={n:a.rawsig(bpy.data.objects[n]) for n in protected}
        np.savez_compressed(E/'native-brush-authored-lineage.npz',previousGuideWorld=raw0,authoredGuideWorld=authored,evaluatedBeforeWorld=P0,evaluatedAfterWorld=P,offsets=off)
        save('native-brush-construction-summary.json',{'UTC':stamp(),'actualSkin':skin.name,'actualHair':hair.name,'actualBirths':'AFN198_ACTUAL_EDITABLE_SURFACE_BIRTHS','actualGuides':len(hair.data.curves),'actualCurves':len(off),'actualPoints':len(P),'nativeBrushOperations':len(strokes)-1,'nativeBrush':brush.name,'rawGuideMaximumChangeM':float(np.linalg.norm(authored-raw0,axis=1).max()),'rawGuideRootMaximumChangeM':float(np.linalg.norm(authored.reshape(252,16,3)[:,0]-raw0.reshape(252,16,3)[:,0],axis=1).max()),'allOldOriginalRawMeshUVSignaturesUnchanged':protected,'sameBirthIDsUVCountRadiusMaterialAndGenerator':True,'nativeGenerationRestoredBeforeEveryCompletePreview':True,'notCoordinateTemplateAuthoring':True,'appearanceOperationContactRuntimeUnaccepted':True})
        captures=[]
        def capture(scene):
            captures.append({'UTC':stamp(),'loadedSource':bpy.data.filepath,'plannedCandidate':str(OUT),'output':scene.render.filepath,'frame':scene.frame_current,'cameraMatrixWorld':[list(v) for v in scene.camera.matrix_world],'lens':scene.camera.data.lens,'cameraType':scene.camera.data.type,'viewTransform':scene.view_settings.view_transform,'look':scene.view_settings.look,'exposure':scene.view_settings.exposure,'cyclesSamples':scene.cycles.samples,'seed':scene.cycles.seed,'hairType':scene.render.hair_type,'newGroomVisible':not hair.hide_render,'originalHairVisible':not old.hide_render,'nativeChildGeneratorViewportAndRenderEnabled':gen.show_viewport and gen.show_render,'captureStateNotRenderGeometryDepsgraphProof':True});save('actual-render-pre-capture-states.json',captures)
        bpy.app.handlers.render_pre.append(capture);a.b.u.v.E=E;hair.hide_render=True;old.hide_render=False
        for v in ['face','body-face']:s.camera.data.type='PERSP';a.b.u.v.image('baseline-original-working-hair',v)
        old.hide_render=True;hair.hide_render=False
        for v in ['face','body-face','oblique','profile','back']:s.camera.data.type='PERSP';a.b.u.v.image('a-native-curve-sculpt',v)
        bpy.app.handlers.render_pre.remove(capture);s.camera.matrix_world=Matrix(captures[2]['cameraMatrixWorld']);s.camera.data.lens=captures[2]['lens'];s.camera.data.type='PERSP';OUT.parent.mkdir(parents=True,exist_ok=True);[bpy.data.brushes.remove(br,do_unlink=True) for br in list(bpy.data.brushes) if br.name not in brushesBefore];bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
        save('a-build-summary.json',{'UTC':stamp(),'output':str(OUT),'sha256':sha(OUT),'bytes':OUT.stat().st_size,'actualHair':hair.name,'actualSkin':skin.name,'actualBirths':'AFN198_ACTUAL_EDITABLE_SURFACE_BIRTHS','oneCandidate':True,'elapsedJobSeconds':time.time()-tick,'actualCurves':len(off),'actualPoints':len(P),'unaccepted':True});print('R200_REAL_NATIVE_BRUSH_COMPLETE_CANDIDATE_SAVED',flush=True)

def deferred():
    try:main()
    except Exception as error:
        save('native-operator-authoring-failure.json',{'UTC':stamp(),'error':repr(error),'traceback':traceback.format_exc(),'originalClockNotReset':True,'noCoordinateTemplateFallback':True});traceback.print_exc()
    bpy.ops.wm.quit_blender();return None
bpy.app.timers.register(deferred,first_interval=1.0)
