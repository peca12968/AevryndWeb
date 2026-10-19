"""Correct actual-width fidelity; same geometry/radii, not a hairstyle variant.

The inherited EEVEE STRAND primitive ignores diameter. STRIP respects radius
and subdivision0 keeps the tested piecewise-linear path. Old capsule evidence
applies to physical geometry only, not the old one-pixel rendered footprint.
"""
import bpy,importlib.util,json,hashlib,time
from pathlib import Path
import numpy as np
spec=importlib.util.spec_from_file_location('f34',Path(__file__).with_name('build-female-next-r0034-lock-fibres.py'));f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f);a=f.a;g=f.g

def main():
    f.c.configure();g.b.E=a.E;report=a.read('c-preview-build.json');path=Path(report['output']);assert g.b.sha(path)==report['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(path));scene=bpy.context.scene;o=bpy.data.objects['AFN34_C_INDEPENDENT_LOCK_FIBRES'];p,r=f.arrays(o.data);before_hashes=(hashlib.sha256(p.tobytes()).hexdigest(),hashlib.sha256(r.tobytes()).hexdigest());assert before_hashes==(report['positionsSha256'],report['radiiSha256']);original={n:g.signature(bpy.data.objects[n]) for n in report['originalNineMeshesExact']};mx=np.array(o.matrix_world)
    observed_primitive=scene.render.hair_type;assert observed_primitive in ('STRAND','STRIP') and scene.render.hair_subdiv==0
    # Rebuilding with the corrected generator already produces STRIP. Recreate
    # the legacy setting only as a labeled same-data diagnostic; never undo
    # the corrected saved source or claim the new generator still has the bug.
    if observed_primitive=='STRIP':
        scene.render.hair_type='STRAND';g.q.render('c-preview')
    scene.render.hair_type='STRIP';scene.render.hair_subdiv=0;out=a.S/'aevrynd-female-next-r0034-c-preview-physical-width.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
    assert {n:g.signature(bpy.data.objects[n]) for n in original}==original;pp,rr=f.arrays(o.data);assert np.array_equal(pp,p) and np.array_equal(rr,r) and np.array_equal(np.array(o.matrix_world),mx)
    g.q.render('c-preview-physical')
    # A fair shape comparison needs the old r33 data under the same physical
    # primitive. This is a separate corrected rendering, not a past approval.
    bpy.ops.wm.open_mainfile(filepath=str(f.CONTAINER));g.b.setup(bpy.context.scene,g.b.config(bpy.context.scene));bpy.context.scene.render.hair_type='STRIP';bpy.context.scene.render.hair_subdiv=0;g.q.render('r33-physical-wide')
    a.save('physical-width-correction.json',{'status':'CORRECTED_PREVIEW_PHYSICAL_WIDTH_NOT_APPEARANCE_APPROVAL','originalPreview':str(path),'originalPreviewSha256':g.b.sha(path),'correctedPreview':str(out),'correctedPreviewSha256':g.b.sha(out),'changedOnly':['RenderSettings.hair_type STRAND -> STRIP'],'hairSubdivision':0,'nativePositionsRadiiAndWorldMatrixExact':True,'originalNineMeshesExact':True,'materialsLightExposureExact':True,'bodyContactInheritance':{'report':'c-preview-body-contact.json','scope':'Exact unchanged physical POLY data/radii and world matrix. Old STRAND footprint was not bounded by those radii.'},'officialSource':'https://docs.blender.org/manual/en/latest/render/eevee/render_settings/curves.html','observedInstalledSetting':'STRAND','documentedBehavior':'STRAND ignores diameter and renders about1pixel wide; STRIP uses ribbon width with rounded normals','notClaimed':['No hairstyle quality promotion','No anisotropic hair scattering implementation','No hair self collision, dynamics or runtime proof'],'comparison':'New and r33 old are both freshly rendered with85mm full-head cameras, same stage and STRIP/subdivision0. A same-geometry preview STRAND/STRIP comparison is separate from geometry comparison.'})
    report=a.read('physical-width-correction.json');report['originalSavedPreviewPrimitive']=observed_primitive;report['legacyComparisonReconstructedWhenAlreadyCorrected']=observed_primitive=='STRIP';a.save('physical-width-correction.json',report)
    print('R34_PHYSICAL_WIDTH_CORRECTED',flush=True)
if __name__=='__main__':main()
