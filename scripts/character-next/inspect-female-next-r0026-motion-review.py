"""Reopen the rejected candidate playback; do not turn this into acceptance."""
import bpy,importlib.util,json
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('b26',Path(__file__).with_name('build-female-next-r0026-oral-interface.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
def main():
    report=json.loads((b.E/'c-motion-render.json').read_text(encoding='utf8'));path=Path(report['source']);assert b.b.sha(path)==report['sha256'];bpy.ops.wm.open_mainfile(filepath=str(path));rows=[];cache=np.load(b.S/'aevrynd-female-next-r0024-oral-fit-data.npz')
    for frame,w in ((1,0.),(13,.2),(25,0.)):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();body=b.b.prior.evaluate(bpy.data.objects['AFN_R0008_Body']);error=float(np.linalg.norm(body-cache['bodyNeutral']-cache['bodyDeltaOpen']*w,axis=1).max());assert error<5.e-7
        a=bpy.data.objects['AFN24_LowerRigidControl'].rotation_axis_angle[0];c=bpy.data.objects['AFN26_OralRig'].pose.bones['AFN26_OralJaw'].rotation_euler[0];assert abs(a-c)<1.e-7;rows.append({'frame':frame,'weight':float(bpy.data.objects['AFN24_MouthControl']['open']),'bodyErrorM':error,'dentalAngleRadians':a,'softTissueAngleRadians':c})
    images=[{'name':i.name,'packed':bool(i.packed_file)} for i in bpy.data.images if i.source=='FILE'];assert all(i['packed'] for i in images) and not bpy.data.libraries
    for o in bpy.data.objects:
        for target in [o]+([o.data.shape_keys] if o.type=='MESH' and o.data.shape_keys else []):
            if target.animation_data:assert all(c.driver.is_valid for c in target.animation_data.drivers)
    b.save('c-saved-motion-verification.json',{'asset':str(path),'sha256':b.b.sha(path),'status':'PASS_REOPEN_AND_SAMPLED_CONTROLLER_PLAYBACK_ONLY_CANDIDATE_REJECTED','frames':rows,'images':images,'externalLibraries':len(bpy.data.libraries),'autoexecFail':bpy.app.autoexec_fail,'limits':'No soft-tissue self-contact, full-mouth, continuous motion or realism acceptance.'});print('R0026_REVIEW_REOPEN_PASS_ONLY',flush=True)
if __name__=='__main__':main()
