"""Verify saved playback in safe mode agrees with the static study endpoints."""
import bpy,importlib.util,json
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('b24',Path(__file__).with_name('build-female-next-r0024-oral-layers.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
def main():
    report=json.loads((b.E/'b-motion-render.json').read_text(encoding='utf8'));path=Path(report['source']);assert b.sha(path)==report['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(path));cache=np.load(b.S/'aevrynd-female-next-r0024-oral-fit-data.npz');body=bpy.data.objects['AFN_R0008_Body'];rows=[]
    for frame,w in ((1,0.),(13,.2),(25,0.)):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();actual=b.evaluate(body);error=float(np.linalg.norm(actual-(cache['bodyNeutral']+cache['bodyDeltaOpen']*w),axis=1).max());assert error<5.e-7
        rows.append({'frame':frame,'expectedWeight':w,'actualWeight':float(bpy.data.objects['AFN24_MouthControl']['open']),'bodyEvaluatorMaximumErrorM':error})
    invalid=[]
    for obj in bpy.data.objects:
        targets=[obj]+([obj.data.shape_keys] if obj.type=='MESH' and obj.data.shape_keys else [])
        for target in targets:
            if target.animation_data:
                invalid.extend((obj.name,c.data_path) for c in target.animation_data.drivers if not c.driver.is_valid)
    assert not invalid
    images=[{'name':i.name,'packed':bool(i.packed_file)} for i in bpy.data.images if i.source=='FILE'];assert all(i['packed'] for i in images) and not bpy.data.libraries
    s=bpy.context.scene
    b.save('b-saved-motion-review-verification.json',{'asset':str(path),'sha256':b.sha(path),'status':'PASS_REOPEN_AND_SAMPLED_PLAYBACK_ONLY_CONTACT_FAILURES_UNRESOLVED','safeModeAutoexecFail':bpy.app.autoexec_fail,'frames':rows,'invalidDrivers':invalid,'images':images,'externalLibraries':len(bpy.data.libraries),'cameraLocation':list(s.camera.location),'timeline':[s.frame_start,s.frame_end,s.render.fps],'limitations':'Playback correctness only; this is not a contact, natural-motion or runtime pass.'})
    print('R0024_MOTION_REOPEN_PASS',flush=True)
if __name__=='__main__':main()
