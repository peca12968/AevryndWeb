"""Reopen actual pinned complete sources; render missing matched baseline views.

No model edit or contact-gate bypass. R50A is a rejected static eye-rest study.
"""
from pathlib import Path
import importlib.util, json, time
import bpy

spec = importlib.util.spec_from_file_location('r50build', Path(__file__).with_name('build-female-next-r0050-neutral-rest.py'))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
b, f, E = a.b, a.f, a.E

def main():
    tick = time.time()
    build = json.loads((E / 'a-build-summary.json').read_text())
    assert b.sha(a.SRC) == build['sourceSha256']
    assert b.sha(a.OUT) == build['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(a.OUT))
    candidate = f.state()
    value = bpy.data.objects[a.CONTROL].data.attributes[a.ATTRIBUTE].data[0].value
    assert abs(value-a.ANGLE) < 1e-7
    bpy.ops.wm.open_mainfile(filepath=str(a.SRC))
    source = f.state()
    for key in ('materials', 'skinFields', 'curves', 'stage'):
        assert source[key] == candidate[key], key
    f.E = E
    f.render('before', ('face', 'oblique', 'profile'))
    a.i.ch.review.extras('before', E)
    assert f.state() == source
    a.save('reopened-delivery-verification.json', {
        'status': 'SOURCE_AND_CANDIDATE_REOPENED_MATCHED_MATERIAL_HAIR_STAGE_NOT_CONTACT_ACCEPTANCE',
        'source': str(a.SRC), 'sourceSha256': b.sha(a.SRC),
        'candidate': str(a.OUT), 'candidateSha256': b.sha(a.OUT),
        'controlReadbackRadians': value,
        'materialsSkinFieldsScalpAndBrowCurvesStageIdentical': True,
        'sourceUnchangedAfterRendering': True,
        'sourceAndCandidateNotResaved': True,
        'limits': ['Rejected appearance; existing source and candidate self intersections',
                   'No completed wet/lash contact qualification after body gate stopped',
                   'No animation, hair physics, runtime or website acceptance'],
        'seconds': time.time()-tick,
    })
    print('R50_DELIVERY_BASELINE_COMPLETE', time.time()-tick, flush=True)

if __name__ == '__main__':
    main()
