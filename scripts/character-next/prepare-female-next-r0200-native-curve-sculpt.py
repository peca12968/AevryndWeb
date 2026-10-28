"""Open one isolated interactive native Curves Sculpt session and observe real edits."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,datetime,importlib.util
from mathutils import Vector
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0200-native-curve-sculpt'
sp=importlib.util.spec_from_file_location('r200base',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);h=m.h
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(n,x):(E/n).write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
t=json.loads((E/'before.json').read_text('utf-8'));assert hashlib.file_digest(Path(t['source']).open('rb'),'sha256').hexdigest()==t['sourceSha256']
bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);hair=bpy.data.objects['AFN198_ACTUAL_SURFACE_BORN_NATIVE_GROOM']
for ob in bpy.context.view_layer.objects:ob.select_set(False)
hair.hide_set(False);hair.hide_render=False;hair.select_set(True);bpy.context.view_layer.objects.active=hair
bpy.context.view_layer.update();raw0=h.arr(hair.data.position_data,'vector',len(hair.data.position_data),3);P0,off0=m.curveworld(hair)
np.savez_compressed(E/'native-sculpt-baseline.npz',guideWorld=raw0,evaluatedWorld=P0,offsets=off0)
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        space=area.spaces.active;space.region_3d.view_rotation=s.camera.matrix_world.to_quaternion();space.region_3d.view_location=Vector((0,-.025,1.47));space.region_3d.view_distance=.42;space.region_3d.view_perspective='ORTHO';space.shading.type='SOLID';space.shading.color_type='MATERIAL';space.overlay.show_floor=False;space.overlay.show_axis_x=False;space.overlay.show_axis_y=False
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(E/'native-sculpt-working.blend'),compress=True)
modeResult=None
try:modeResult=str(bpy.ops.object.mode_set(mode='SCULPT_CURVES'))
except Exception as error:modeResult=repr(error)
events=[];last=hashlib.sha256(raw0.tobytes()).hexdigest()
save('native-sculpt-session-start.json',{'UTC':stamp(),'input':t['source'],'inputSHA256':t['sourceSha256'],'isolatedEditableSession':bpy.data.filepath,'actualHair':hair.name,'actualMode':hair.mode,'modeResult':modeResult,'actualGuideCount':len(hair.data.curves),'actualPoints':len(raw0),'actualBrush':getattr(getattr(s.tool_settings.curves_sculpt,'brush',None),'name',None),'baselineRawSHA256':last,'scriptAuthoredNoGeometry':True})
def observe():
    global last
    try:
        raw=h.arr(hair.data.position_data,'vector',len(hair.data.position_data),3);sig=hashlib.sha256(raw.tobytes()).hexdigest()
        if sig!=last:
            P,off=m.curveworld(hair);ev=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
            ids=h.arr(ev.attributes['AFN198_PERSISTENT_BIRTH_ID'].data,'value',len(off),dtype='i4')
            layout=len(P)==len(P0) and np.array_equal(off,off0) and len(ids)==10191 and np.array_equal(np.sort(ids),np.arange(10191))
            event={'UTC':stamp(),'rawSHA256':sig,'rawGuidePoints':len(raw),'rawMaximumMovementFromBaselineM':float(np.linalg.norm(raw-raw0,axis=1).max()) if raw.shape==raw0.shape else None,'actualMode':hair.mode,'actualBrush':getattr(getattr(s.tool_settings.curves_sculpt,'brush',None),'name',None),'actualCurves':len(off),'completeBirthIDs':layout,'evaluatedMaximumMovementFromBaselineM':float(np.linalg.norm(P-P0,axis=1).max()) if layout else None,'evaluatedRootMaximumMovementFromBaselineM':float(np.linalg.norm(P[off]-P0[off0],axis=1).max()) if layout else None,'observedNotFullCurveCorrespondenceProof':True}
            events.append(event);save('native-sculpt-edit-events.json',events)
            np.savez_compressed(E/'native-sculpt-latest-observed.npz',guideWorld=raw,evaluatedWorld=P,offsets=off,birthIDs=ids)
            last=sig
        save('native-sculpt-current-state.json',{'UTC':stamp(),'mode':hair.mode,'brush':getattr(getattr(s.tool_settings.curves_sculpt,'brush',None),'name',None),'events':len(events),'rawSHA256':sig,'loadedFile':bpy.data.filepath})
    except Exception as error:save('native-sculpt-observer-error.json',{'UTC':stamp(),'error':repr(error)})
    return 2.0
bpy.app.timers.register(observe,first_interval=2)
print('R200_INTERACTIVE_NATIVE_CURVE_SCULPT_READY',modeResult,flush=True)
