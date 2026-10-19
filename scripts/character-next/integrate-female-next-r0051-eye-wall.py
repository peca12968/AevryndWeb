"""Integrate B with rebuilt exact wet-surface source bindings, original tolerance."""
from pathlib import Path
import bpy,importlib.util,numpy as np,json,time
sp=importlib.util.spec_from_file_location('rebase51',Path(__file__).with_name('build-female-next-r0051-rebased-wall.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
a=k.a;b=k.b;f=k.f;E=k.E
OUT=b.S/'aevrynd-female-next-r0051-b-integrated-eye-wall.blend'

def localcoords(o):
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
    P=np.empty(len(m.vertices)*3,dtype='f4');m.vertices.foreach_get('co',P)
    ev.to_mesh_clear();return P.reshape(-1,3).astype('f8')

def main():
    tick=time.time();report=json.loads((E/'b-build-summary.json').read_text());assert b.sha(k.OUT)==report['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(k.OUT));before=f.state();body=bpy.data.objects[b.BODY];V=localcoords(body)
    records=json.loads((b.R/'Evidence/character-female-next/r0037-eye-margin/c-review-tissue-bindings.json').read_text());rows=[]
    for rec in records['patches']:
        o=bpy.data.objects[rec['object']];assert not o.modifiers
        assert b.matrix(o.matrix_world)==b.matrix(body.matrix_world)
        P=localcoords(o);base=np.array([np.array(n['weights'])@V[n['indices']] for n in rec['nodes']])
        delta=base-P[:rec['baseNodeCount']];mapping=np.array(rec['vertexBaseNode'],dtype='i4')
        target=P+delta[mapping];target[:rec['baseNodeCount']]=base
        beforeSignature=b.mesh_signature(o.data)
        o.data.vertices.foreach_set('co',target.astype('f4').ravel());o.data.update()
        assert b.mesh_signature(o.data)['uv']==beforeSignature['uv']
        rows.append({'object':o.name,'baseNodes':rec['baseNodeCount'],
                     'maximumLocalRebindDisplacementM':float(np.linalg.norm(target-P,axis=1).max()),
                     'sourceLineage':'Same native body vertex indices and barycentric weights; update foot and corresponding raised points together.',
                     'originalInterfaceToleranceM':1e-6})
    bpy.context.view_layer.update();after=f.state();changed={r['object'] for r in rows}
    assert all(after[key]==before[key] for key in ('materials','skinFields','curves','stage'))
    assert all(after['meshes'][n]==row for n,row in before['meshes'].items() if n not in changed)
    bpy.context.scene['AFN51_status']='INTEGRATED_POSTERIOR_REPAIR_WITH_REBOUND_WET_TISSUES_UNVERIFIED'
    b.camera('face');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    k.k.save('b-integrated-build-summary.json',{'source':str(k.OUT),'sourceSha256':b.sha(k.OUT),
        'output':str(OUT),'outputSha256':b.sha(OUT),'reboundTissues':rows,
        'bodyNativeAndEvaluatedGeometryExactFromB':True,'allOtherMeshesExact':True,
        'materialsSkinFieldsCurvesStageExact':True,'seconds':time.time()-tick,
        'status':'INTEGRATED_B_PENDING_EXACT_INTERFACE_CHECK_NO_APPEARANCE_SCORE'})
    f.E=E;f.render('b-integrated',('face','oblique','profile'));a.i.i.E=E;a.i.i.closeup('b-integrated');a.i.ch.review.extras('b-integrated',E)
    print('R51_B_INTEGRATED',rows,time.time()-tick,flush=True)

if __name__=='__main__':main()
