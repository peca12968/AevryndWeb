"""Bounded eye appearance falsification before neutral-rest production.

Cornea visibility toggle is a diagnostic ONLY, not a replacement asset or a
collision/appearance acceptance. Native rejected Half is a shape reference.
"""
import bpy,importlib.util,time,json,numpy as np
from pathlib import Path
sp=importlib.util.spec_from_file_location('eye50base',Path(__file__).with_name('inspect-female-next-r0043-ocular-junction.py'));i=importlib.util.module_from_spec(sp);sp.loader.exec_module(i)
b=i.b;f=i.f;v=i.v;R=b.R;S=b.S;E=R/'Evidence/character-female-next/r0050-eye-rest';E.mkdir(exist_ok=True);SRC=S/'aevrynd-female-next-r0048-anatomical-authoring-retained.blend';HALF=S/'aevrynd-female-next-r0044-c-rejected-native-lid-shapes.blend'
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
    tick=time.time();assert b.sha(SRC)=='49f76186981a7244444e37b950eab6acd24e34be15a65d855cee527422405c67';bpy.ops.wm.open_mainfile(filepath=str(SRC));before=f.state();f.E=E;f.render('before',('face',));i.i.E=E;i.i.closeup('before');parts={}
    for side in ('L','R'):
        parts[side]={}
        for part in ('Sclera','Cornea','Iris','Pupil'):
            o=bpy.data.objects[f'AFN30_{side}_{part}'];P,T=b.evaluated(o,True);parts[side][part]={'boundsM':[P.min(0).tolist(),P.max(0).tolist()],'vertices':len(P),'triangles':len(T),'materials':[v.v32.material_signature(m)for m in o.data.materials]}
    for side in ('L','R'):bpy.data.objects[f'AFN30_{side}_Cornea'].hide_render=True
    f.render('diagnostic-no-cornea',('face',));i.i.closeup('diagnostic-no-cornea')
    for side in ('L','R'):bpy.data.objects[f'AFN30_{side}_Cornea'].hide_render=False
    assert f.state()==before
    assert b.sha(HALF)=='746df2c37a625af9c97ecede362361e9b828147da2c822103374d6c081939e06';bpy.ops.wm.open_mainfile(filepath=str(HALF));body=bpy.data.objects[b.BODY];assert body.modifiers[0].render_levels==0;key=body.data.shape_keys.key_blocks['AFN44_C_Half_NATIVE_ONLY'];key.value=1.;bpy.context.view_layer.update();f.render('reference-rejected-native-half',('face',));i.i.closeup('reference-rejected-native-half');save('appearance-falsification.json',{'completeSource':str(SRC),'completeSourceSha256':b.sha(SRC),'sourceVisibleGeometryMatchesR42B':True,'currentEyeParts':parts,'corneaToggle':'Diagnostic visibility only; no saved candidate, not a completed model or collision exclusion. Exact source restored after render.','halfReference':{'source':str(HALF),'sha256':b.sha(HALF),'nativeOnly':True,'multiresLevel':0,'halfKeyValue':1,'attachments':'Original neutral frozen lash/wet tissues; not rebuilt. Do not inherit any full-sculpt or contact qualification.'},'knownSourceActualUpperIrisCoverageM':{'L':.0012979911804196888,'R':.0011889518737793871},'geometryReference':'https://eyewiki.org/Upper_Eyelid_Retraction','inference':'Existing central geometric upper coverage is already in the cited1..2mm reference range. Apparent iris/eyelid relation must be checked before shrinking aperture or adopting rejected Half.','seconds':time.time()-tick});print('R50_APPEARANCE_DIAGNOSTICS_READY',time.time()-tick,flush=True)
if __name__=='__main__':main()
