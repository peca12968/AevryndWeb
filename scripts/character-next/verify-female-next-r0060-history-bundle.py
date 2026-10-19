"""Open archived model directly with its local relative resources and controls."""
from pathlib import Path
import bpy,json,hashlib,time,numpy as np
R=Path(r'D:\Download\Aevrynd');M=R/'sites-engine-journey/assets-source/aevrynd-character/female-next';E=R/'Evidence/character-female-next/r0060-ocular-assembly'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    tick=time.time();a=json.loads((E/'b-build-summary.json').read_text());source=M/Path(a['output']).name;assert sha(source)==a['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(source));ctrl=bpy.data.objects['AFN59_FACE_CONTROLS'];body=bpy.data.objects[a['visibleComponents']['4']];rows=[]
    for frame,value in ((1,0.),(18,.5),(21,1.)):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();key=body.data.shape_keys.evaluated_get(deps).key_blocks['AFN59_Blink_Left'];evaluated=body.evaluated_get(deps);me=evaluated.to_mesh();P=np.empty(len(me.vertices)*3,dtype='f4');me.vertices.foreach_get('co',P);assert np.isfinite(P).all();positionHash=hashlib.sha256(P.tobytes()).hexdigest();evaluated.to_mesh_clear();error=abs(key.value-value);ulp=float(np.spacing(np.float32(value)));print('R60_HISTORY_CONTROL',frame,ctrl['blink_left'],key.value,'ERROR',error,'FLOAT32_ULP',ulp,flush=True);assert abs(ctrl['blink_left']-value)<1e-8 and error<=ulp;rows.append({'frame':frame,'left':ctrl['blink_left'],'right':ctrl['blink_right'],'evaluatedBodyLeftShape':key.value,'driverValueAbsoluteError':error,'oneFloat32ULPAtExpected':ulp,'actualEvaluatedBodyPositionHash':positionHash})
    assert len({x['actualEvaluatedBodyPositionHash'] for x in rows})==3
    assert body.data.shape_keys.key_blocks['AFN60_Cavity_Repair'].value==1 and bpy.data.objects['AFN60_ORIGINAL_SOURCE_CAGE'].hide_render;assert all(name in bpy.data.objects for name in a['visibleComponents'].values());assert not any(o.name.startswith('AFN60_JACOBIAN_LOCAL_HALO') for o in bpy.context.scene.objects);assert not bpy.data.libraries and not bpy.app.handlers.frame_change_pre and not bpy.app.handlers.frame_change_post
    images=[]
    for im in bpy.data.images:
        if im.source not in ('FILE','TILED'):continue
        p=Path(bpy.path.abspath(im.filepath)).resolve();assert im.source=='FILE' and im.filepath.startswith('//') and p.is_relative_to(M.resolve()) and p.exists() and len(im.pixels)>0;images.append({'path':str(p),'sha256':sha(p),'dimensions':list(im.size)})
    assert len(images)==15;row={'source':str(source),'sourceSha256':sha(source),'openedFromHistoryLocation':True,'relativeResourcesLoaded':images,'nativePersistedControls':rows,'visibleComponentCount':5,'temporarySolveHelpersRemoved':True,'autoRunAddonOrLibraryRequired':False,'scope':'Portable readback only; does not expand seven-pose contact qualification or runtime acceptance.','seconds':time.time()-tick};(E/'history-b-readback.json').write_text(json.dumps(row,indent=2)+'\n',encoding='utf8');print('R60_HISTORY_REOPENED',len(images),len(rows),time.time()-tick,flush=True)
if __name__=='__main__':main()
