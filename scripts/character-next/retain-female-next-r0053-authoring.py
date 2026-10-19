"""Keep qualified root data in a complete unchanged review character.

Rejected master paths remain hidden and labelled; the old approved working
appearance is restored. This research container does not promote the groom.
"""
from pathlib import Path
import bpy,importlib.util,json,numpy as np,time
sp=importlib.util.spec_from_file_location('retain53',Path(__file__).with_name('build-female-next-r0053-scalp-foundation.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=k.E;OUT=b.S/'aevrynd-female-next-r0053-authoring-retained.blend'

def main():
    tick=time.time();proof=json.loads((E/'grown-fixed-saved-readback.json').read_text())
    assert proof['surfaceUVExactlyExpectedFloat32'] and proof['rootClassificationCounts']=={'outside':64}
    assert proof['minimumSampledRootCapsuleSurfaceGapM']>1e-6 and proof['inheritedSixExact']
    source=Path(proof['source']);assert b.sha(source)==proof['sourceSha256']
    bpy.ops.wm.open_mainfile(filepath=str(k.SRC));before=f.state()
    bpy.ops.wm.open_mainfile(filepath=str(source));o=bpy.data.objects[k.NAME];P,R=f.v.hair_arrays(o)
    o.hide_render=True;o.hide_set(True)
    o['aevrynd_layer']='REJECTED_PRIMARY_SHAPE_ROOT_AUTHORING_RETAINED'
    o['scope']='Full hairstyle visually rejected.64root positions,barycentric/UV attachment and uniform native sampling retained only; no full-path/self/dynamic/runtime acceptance.'
    scalp=bpy.data.objects['AFN53_ANATOMICAL_SCALP'];scalp.hide_render=True;scalp.hide_set(True)
    scalp['scope']='Owned actual evaluated body-skin triangle region; artist boundary, not measured follicle truth. Native UV preserved. Final hairline styling remains unaccepted.'
    old=bpy.data.objects[k.OLD];old.hide_render=False;old.hide_set(False)
    for ob in bpy.context.view_layer.objects:ob.select_set(False)
    body=bpy.data.objects[b.BODY];body.select_set(True);bpy.context.view_layer.objects.active=body
    b.camera('face');bpy.context.scene['AFN53_status']='RETAIN_AUTHORING_ONLY_COMPLETE_R51_APPEARANCE_UNCHANGED'
    assert f.state()==before
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    digest=b.sha(OUT)
    bpy.ops.wm.open_mainfile(filepath=str(OUT));assert f.state()==before
    o=bpy.data.objects[k.NAME];Q,RR=f.v.hair_arrays(o)
    assert np.array_equal(Q,P) and np.array_equal(RR,R)
    assert o.hide_render and o.hide_get() and o.data.surface.name==b.BODY
    assert o.data.attributes['surface_uv_coordinate'].data_type=='FLOAT2'
    report={'source':str(OUT),'sourceSha256':digest,'reopened':True,
        'entireVisibleCharacterStateExactR51':True,'hiddenNativeAuthoringPointsAndRadiiExact':True,
        'hiddenRootCount':len(P),'pointsPerCurve':P.shape[1],
        'surfaceUVType':'FLOAT2','rejectedGroomHiddenInViewportAndRender':True,
        'scope':'Complete unchanged r51 appearance with scoped hidden authoring research. Not a new appearance improvement, accepted full groom, dynamics or runtime.',
        'sourceRootEvidence':str(E/'grown-fixed-saved-readback.json'),'seconds':time.time()-tick}
    k.save('retained-authoring-readback.json',report)
    f.E=E;f.render('retained-authoring',('face',));k.k.k.a.i.ch.review.extras('retained-authoring',E)
    print('R53_RETAINED_AUTHORING',report['entireVisibleCharacterStateExactR51'],flush=True)

if __name__=='__main__':main()
