"""Reopen proof and actual complete-character authoring demonstration renders."""
import bpy,importlib.util,json,time,sys
from pathlib import Path
import numpy as np
from mathutils import Vector
sp=importlib.util.spec_from_file_location('live38',Path(__file__).with_name('build-female-next-r0038-live-groom.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
f=m.f;b=m.b;v=m.v;E=m.E;S=m.S
def render_extras(label):
    s=bpy.context.scene;rows=[]
    lights=[(o,list(o.location),list(o.rotation_euler),list(o.scale)) for o in s.objects if o.type=='LIGHT']
    for view in ('opposite-oblique','alternate-oblique','body-face','back'):
        b.camera('body-face' if view=='body-face' else 'oblique');s.camera.data.lens=85
        if view=='opposite-oblique':
            s.camera.location.x=-s.camera.location.x;s.camera.rotation_euler=(Vector(b.TARGET)-s.camera.location).to_track_quat('-Z','Y').to_euler()
        if view=='back':
            s.camera.location=(0,.80,1.47);s.camera.rotation_euler=(Vector(b.TARGET)-s.camera.location).to_track_quat('-Z','Y').to_euler()
        if view=='alternate-oblique':
            for o,loc,rot,scale in lights:o.location.x=-o.location.x;o.rotation_euler=(Vector(b.TARGET)-o.location).to_track_quat('-Z','Y').to_euler()
        bpy.context.view_layer.update();s.render.resolution_x=s.render.resolution_y=800;s.render.filepath=str(E/f'{label}-{view}.png')
        bpy.ops.render.render(write_still=True)
        rows.append({'view':view,'camera':b.matrix(s.camera.matrix_world),'lens':85,'stage':v.stage(),'resolution':[800,800]})
        for o,loc,rot,scale in lights:o.location=loc;o.rotation_euler=rot;o.scale=scale
        bpy.context.view_layer.update()
    return rows
def main():
    start=time.time();build=json.loads((E/'b-build.json').read_text());path=Path(build['output'])
    assert b.sha(path)==build['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(m.SRC));before=f.state();hp,hr=v.hair_arrays(bpy.data.objects[f.OLD])
    original_native_types=np.array([a.value for a in bpy.data.objects[f.OLD].data.attributes['curve_type'].data],dtype='i4')
    original_native_materials=np.array([a.value for a in bpy.data.objects[f.OLD].data.attributes['material_index'].data],dtype='i4')
    f.render('before');before_extra=render_extras('before')
    bpy.ops.wm.open_mainfile(filepath=str(path));assert f.state()==before
    hair=bpy.data.objects[f.OLD];p,r=m.eval_arrays(hair)
    assert np.array_equal(p,hp) and np.array_equal(r,hr)
    eo=hair.evaluated_get(bpy.context.evaluated_depsgraph_get())
    assert np.array_equal(np.array([a.value for a in eo.data.attributes['curve_type'].data]),original_native_types)
    assert np.array_equal(np.array([a.value for a in eo.data.attributes['material_index'].data]),original_native_materials)
    bind=np.load(S/'aevrynd-female-next-r0038-b-live-guide-bindings.npz')
    guide=bpy.data.objects[m.GUIDE];rest=bpy.data.objects[m.REST];gp,gr=v.hair_arrays(guide);rp,rr=v.hair_arrays(rest)
    assert np.array_equal(gp,rp) and np.array_equal(gp,bind['guideRestPositions'])
    indices=bind['indices'];weights=bind['weights'];ids=bind['guideRootIds'];data=np.load(S/'aevrynd-female-next-r0033-c-bob-fibres.npz');parts=data['parts']
    assert np.all(parts[ids[indices]]==parts[:,None]) and np.all(weights>=0) and np.max(np.abs(weights.sum(1)-1))<2e-7
    assert b.matrix(guide.matrix_world)==b.matrix(hair.matrix_world)==b.matrix(rest.matrix_world)
    assert not bpy.data.libraries and not bpy.data.texts
    # Deliberately move a guide root; the display follicles must remain fixed,
    # and this CV0-only edit must affect no rendered point.
    root_only=gp.copy();control=build['controlTest']['guideIndex'];root_only[control,0,0]+=.001
    guide.data.position_data.foreach_set('vector',root_only.ravel());guide.data.update_tag();rooted,root_r=m.eval_arrays(hair)
    assert np.array_equal(rooted,hp) and np.array_equal(root_r,hr)
    guide.data.position_data.foreach_set('vector',gp.ravel());guide.data.update_tag()
    f.render('b-rest');after_extra=render_extras('b-rest');assert before_extra==after_extra
    # Compare one local guide edit with the exact own weighted-delta formula.
    test=gp.copy();t=np.linspace(0,1,m.N);test[control,:,0]+=(.006*np.sin(.5*np.pi*t)**2).astype('f4');test[control,0]=gp[control,0]
    guide.data.position_data.foreach_set('vector',test.ravel());guide.data.update_tag();edited,editR=m.eval_arrays(hair)
    delta=test-gp;expected=hp.copy()
    acc=np.zeros_like(hp)
    for k in range(3):acc+=delta[indices[:,k]]*weights[:,k,None,None]
    acc[:,0]=0;expected+=acc
    error=float(np.max(np.linalg.norm(edited.astype('f8')-expected,axis=2)))
    assert error<3e-7 and np.array_equal(edited[:,0],hp[:,0]) and np.array_equal(editR,hr)
    # Actual full-head clip showing a bounded authoring operation. It is
    # explicitly not hair simulation or an adopted groom/contact pose.
    selected=np.flatnonzero((parts[ids]>0)&(gp[:,0,1]<-.015)&(gp[:,0,2]>1.52))
    frames=[];s=bpy.context.scene
    for frame,amount in enumerate((0,.35,.7,1.,.7,.35,0.)):
        Q=gp.copy();Q[selected,:,0]+=(.006*amount*np.sin(.5*np.pi*t)**2)[None,:].astype('f4');Q[:,0]=gp[:,0]
        guide.data.position_data.foreach_set('vector',Q.ravel());guide.data.update_tag();out,outr=m.eval_arrays(hair)
        assert np.array_equal(out[:,0],hp[:,0]) and np.array_equal(outr,hr) and not np.any(out[parts<0]!=hp[parts<0])
        b.camera('oblique');s.camera.data.lens=85;s.render.resolution_x=s.render.resolution_y=800;s.render.filepath=str(E/f'b-edit-frame-{frame:02d}.png')
        bpy.ops.render.render(write_still=True);frames.append({'frame':frame,'amount':amount,'camera':b.matrix(s.camera.matrix_world),'stage':v.stage(),'affectedFibres':int(np.any(out!=hp,axis=(1,2)).sum()),'rootsExact':True})
    guide.data.position_data.foreach_set('vector',gp.ravel());guide.data.update_tag();pp,pr=m.eval_arrays(hair)
    assert np.array_equal(pp,hp) and np.array_equal(pr,hr)
    # No edits saved into the authoritative file; verify its on-disk bytes.
    assert b.sha(path)==build['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=str(S/'aevrynd-female-next-r0038-a-root-volume-flow.blend'))
    a_extra=render_extras('a-after');assert before_extra==a_extra
    proof={'status':'PASS_REOPENED_LIVE_AUTHORING_REST_EXACT_SCOPE','source':str(path),'sourceSha256':build['outputSha256'],
        'baseline':str(m.SRC),'baselineSha256':b.sha(m.SRC),
        'allOriginalVisibleMeshGeometryNativeUVMaterialsSkinFieldsAndStageExact':True,
        'all12000EvaluatedScalpCurves1536000PositionsRadiiTypesMaterialsWorldPoseExactAtRest':True,
        'guideRootEditCannotMoveDisplayedHairRoots':True,'localDeltaFormulaMaximumPointErrorM':error,
        'formulaValidationToleranceM':3e-7,'toleranceScope':'Floating-point evaluator agreement, not relaxed contact tolerance',
        'weightsNonnegativeSumOneSamePart':True,'standaloneNoLibrariesOrTexts':True,'completeHeadAndExtraViewsMatched':True,
        'guideCount':len(ids),'ownNodeCount':build['nodes'],'clip':{'selectedGuides':selected.tolist(),'frames':frames,'scope':'Offline guide-edit demonstration; not physical simulation or contact-qualified edited poses.'},
        'contact':'Only exact retained neutral rest can inherit prior version-specific static evidence. No new hairstyle/self/dynamic/cloth contact claims.',
        'runtime':'NOT_IMPLEMENTED','appearance':'UNCHANGED_AT_REST_NO_SCORE_INCREASE','seconds':time.time()-start}
    f.save('b-reopened-verification.json',proof);print('R38_REOPENED_PROOF_DONE',error,time.time()-start,flush=True)
if __name__=='__main__':main()
