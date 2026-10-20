"""One controlled hypothesis: remove redundant inner iris/pupil reflection.

The original outer corneal reflection, all geometry/UV/texture, skin, lights
and exposure remain fixed. This is an immersed-tissue shading approximation.
"""
from pathlib import Path
import bpy,json,importlib.util,time,numpy as np,sys
s=importlib.util.spec_from_file_location('diagnose65build',Path(__file__).with_name('inspect-female-next-r0065-eye-shading.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
E=m.E;S=m.S;SRC=m.SRC;OUT=S/'aevrynd-female-next-r0065-a-inner-eye-diffuse-study.blend'

def main():
    tick=time.time();m.g.E=E;m.shade.g.E=E
    if '--views' in sys.argv:
        ref=json.loads((E/'a-build-summary.json').read_text());assert m.g.sha(OUT)==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(OUT));m.shade.settings();m.save('a-extra-view-controls.json',m.shade.render('a-eye',('oblique','profile','opposite-oblique','alternate-oblique','body-face','back')));return
    assert not OUT.exists();assert m.g.sha(SRC)==m.g.SOURCE_SHA
    m.save('round-contract.json',{'previousGoalTurnClassification':'progress: r64 actual complete guide/card trial, own atlas/native readback/real self-surface witnesses and three saved sources; rejected, GitHubc4e92ac verified. No appearance gain.',
      'sixLines':['Exact r60B complete woman SHA3324231...; no live heavy job or r65model at start.','Main selected face defect: visually dominant iris/pupil highlights and poor iris readability; hair remains incomplete and stopped methods are not resumed.','Deliver actual same-light full-head/body eye improvement if the inner specular hypothesis survives a cheap close-up, then integrate into the same complete woman.','Outer cornea already carries reflection/refraction. Treat inner iris and pupil as non-glossy immersed tissue/absorbing aperture approximation; only disable their redundant specular lobe. No lens/illumination edit.','Compare exact close camera + full head before spending on more views. Reject invisible effect, lost natural wet highlights or no full-head benefit; no specular/roughness sweep.','One heavy job,4threads; diagnosis10min and first preview before45min. One candidate; original full objective including hair/layers/actions/contact/runtime remains.'],
      'reference':{'url':'https://dev.epicgames.com/documentation/en-us/unreal-engine/digital-humans?application_version=4.27','use':'Eye appearance depends jointly on geometry/UV and separating wet refractive outer surface from iris/pupil. General principle only; no sample assets/material/code or plugin copied. Our zero-inner-specular approximation is a hypothesis, not a validated optical model.'}})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.scene.frame_set(1);before=m.k.f.v.stage();new=[]
    for oldname,newname in [('AFN57_CANONICAL_IRIS','AFN65_IMMERSED_IRIS_DIFFUSE_APPROX'),('AFN57_CANONICAL_PUPIL','AFN65_ABSORBING_PUPIL_APPROX')]:
        mat=bpy.data.materials[oldname].copy();mat.name=newname;bs=next(n for n in mat.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled');old=float(bs.inputs['Specular IOR Level'].default_value);assert old==.5;bs.inputs['Specular IOR Level'].default_value=0.
        for name in ('AFN60_L_IRIS_PUPIL_SURFACE','AFN60_R_IRIS_PUPIL_SURFACE'):
            o=bpy.data.objects[name]
            for i,slot in enumerate(o.data.materials):
                if slot.name==oldname:o.data.materials[i]=mat
        new.append({'sourceMaterial':oldname,'candidateMaterial':newname,'input':'Specular IOR Level','before':old,'after':0.})
    assert m.k.f.v.stage()==before;m.shade.settings();m.k.b.camera('face');bpy.context.preferences.filepaths.save_version=0;bpy.context.scene['AFN65_status']='INNER_EYE_SPECULAR_HYPOTHESIS_UNACCEPTED';bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    m.save('a-build-summary.json',{'source':str(SRC),'sourceSha256':m.g.sha(SRC),'output':str(OUT),'outputSha256':m.g.sha(OUT),'changes':new,'scope':'Only two copied inner-eye materials assigned to two iris/pupil components; original materials and outer corneal layer retained. Geometry, UV, all texture files, skin, lights, exposure unchanged.','physicalEyeOrRuntimeAccepted':False,'secondsBeforePreview':time.time()-tick})
    m.save('a-close-control.json',m.close_render('a'));m.save('a-face-control.json',m.shade.render('a-eye',('face',)))
if __name__=='__main__':main()
