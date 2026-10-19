"""Final supplemental complete-character views and actual Blender edit modes."""
import bpy,importlib.util,json,time
from pathlib import Path
import numpy as np
sp=importlib.util.spec_from_file_location('v38supp',Path(__file__).with_name('verify-female-next-r0038-live-groom.py'));v38=importlib.util.module_from_spec(sp);sp.loader.exec_module(v38)
m=v38.m;f=m.f;b=m.b;E=m.E;S=m.S
def main():
    proof=json.loads((E/'b-reopened-verification.json').read_text());path=Path(proof['source'])
    assert b.sha(path)==proof['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=str(path))
    guide=bpy.data.objects[m.GUIDE];hair=bpy.data.objects[f.OLD];P,R=m.eval_arrays(hair)
    bpy.ops.object.select_all(action='DESELECT');guide.hide_set(False);guide.select_set(True);bpy.context.view_layer.objects.active=guide
    modes={}
    for mode in ('EDIT','SCULPT_CURVES'):
        try:
            result=bpy.ops.object.mode_set(mode=mode);modes[mode]={'result':list(result),'actualMode':guide.mode}
        except RuntimeError as exc:modes[mode]={'result':'UNAVAILABLE','reason':str(exc)}
        if guide.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
    assert modes['EDIT']['result']==['FINISHED']
    after,ar=m.eval_arrays(hair);assert np.array_equal(P,after) and np.array_equal(R,ar)
    f.save('b-edit-mode-proof.json',{'source':str(path),'sourceSha256':b.sha(path),'modes':modes,'geometryRadiiExactAfterModeSwitches':True,'scope':'Mode entry only; no brush usability/interactive viewport performance/contact-safety claim.'})
    c=json.loads((E/'c-build.json').read_text());cp=Path(c['output']);assert b.sha(cp)==c['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(cp));extra=v38.render_extras('c-after')
    # Actual controls and stage must match the same recorded baseline views.
    bpy.ops.wm.open_mainfile(filepath=str(m.SRC));base=v38.render_extras('before');assert extra==base
    f.save('c-extra-render-controls.json',{'matched':True,'rows':extra,'scope':'Same full source body/head, neutral static, with regional hair guide edits. Visually rejected, not contact/motion qualified.'})
    print('R38_SUPPLEMENT_DONE',modes,flush=True)
if __name__=='__main__':main()
