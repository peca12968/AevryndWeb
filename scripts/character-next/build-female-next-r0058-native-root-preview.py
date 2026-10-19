"""Actual 17-key native source groom on its exact canonical female emitter.

No root clamping, nearest-point fitting, children or margin sweep. The native
API source includes the omitted follicle key and female root-frame evaluation.
"""
from pathlib import Path
import bpy,importlib.util,numpy as np,json,time,hashlib
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('base58',Path(__file__).with_name('build-female-next-r0057-coherent-preview.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=b.R/'Evidence/character-female-next/r0058-source-emitter';PREV=b.R/'Evidence/character-female-next/r0057-coherent-foundation'
OUT=b.S/'aevrynd-female-next-r0058-a-native-root-groom-study.blend'
def save(name,x):(E/name).write_text(json.dumps(x,indent=2)+'\n',encoding='utf8')
def main():
    tick=time.time();report=json.loads((PREV/'d-build-summary.json').read_text());source=Path(report['output']);assert b.sha(source)==report['outputSha256'];raw=np.load(E/'c-female-native-emitter-and-bob-data.npz');canonical=np.load(PREV/'d-canonical-female-data.npz')
    assert np.array_equal(raw['emitterPositions'],canonical['canonical'].astype('f4'))
    assert np.array_equal(raw['evaluatedEmitterPositions'],canonical['female'].astype('f4'))
    assert np.all(raw['hairCounts']==17)
    bpy.ops.wm.open_mainfile(filepath=str(source));stage=f.v.stage();body=bpy.data.objects['AFN57_CC0_COHERENT_FEMALE_BODY'];hair=bpy.data.objects['AFN57_CANONICAL_BOB_GUIDES'];oldP,oldR=f.v.hair_arrays(hair)
    Q=raw['hairPositions'].reshape(-1,17,3);R=np.concatenate((oldR[:,:1],oldR),axis=1).astype('f4')
    hair.data.resize_curves([17]*len(Q));hair.data.position_data.foreach_set('vector',Q.ravel());hair.data.attributes['radius'].data.foreach_set('value',R.ravel());hair.data.attributes['curve_type'].data.foreach_set('value',[1]*len(Q));hair.data.attributes['material_index'].data.foreach_set('value',[0]*len(Q))
    hair.name='AFN58_NATIVE_SOURCE_BOB_17KEY_GUIDES';hair['scope']='Original evaluated native source Bob17keys including follicle; canonical female1 direct emitter data. No fitted roots, children or accepted complete contacts/dynamics.'
    body['scope']='r57D coherent female unchanged; r58 changes only head-hair native positions/count. Body/eye/oral still combined; no full rig or accepted layers/runtime.'
    assert f.v.stage()==stage;b.camera('face');bpy.context.scene.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0
    bpy.context.scene['AFN58_status']='ACTUAL_NATIVE_ROOT_SOURCE_GROOM_UNACCEPTED'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
    np.savez_compressed(E/'a-native-guide-data.npz',positions=Q,radii=R,matrix=np.array(hair.matrix_world),previousPositions=oldP,previousRadii=oldR)
    # Evaluate actual render-level body in memory only. Saved source retains its
    # original viewport/render settings. All finite segments are checked.
    for md in body.modifiers:
        if md.type=='SUBSURF':md.levels=md.render_levels
    bpy.context.view_layer.update();V,T=b.evaluated(body,True);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);matrix=np.array(hair.matrix_world);world=Q.astype('f8')@matrix[:3,:3].T+matrix[:3,3];radius=R.astype('f8')*np.linalg.norm(matrix[:3,:3],ord=2)
    contact=f.flowcheck.check(world,radius,tree,V[T],roots=True)
    for md in body.modifiers:
        if md.type=='SUBSURF':md.levels=1
    save('a-build-summary.json',{'revision':'female-next-r0058','output':str(OUT),'outputSha256':b.sha(OUT),'source':str(source),'sourceSha256':b.sha(source),'method':'Direct original evaluated native17key Bob data on exact canonical female1 emitter; no nearest-root/cross-body fitting or clamping.','guides':len(Q),'pointsPerGuide':17,'rootKeyIncluded':True,'nativeCanonicalTopologyAndFemaleCoordinatesExact':True,'nonrootRadiiIdenticalToR57':bool(np.array_equal(R[:,1:],oldR)),'children':0,'stageUnchanged':True,'body':{'vertices':len(V),'triangles':len(T)},'headHairActualFullStaticBodyCapsules':contact,'selfFacialHairDynamicsRuntime':'NOT_ACCEPTED','seconds':time.time()-tick})
    f.E=E;f.render('a-native',('face','oblique','profile'));k.k.k.k.k.a.i.ch.review.extras('a-native',E)
    print('R58_NATIVE_SOURCE_PREVIEW',contact['status'],contact['unqualifiedSegments'],len(contact['rootFailures']),time.time()-tick,flush=True)
if __name__=='__main__':main()
