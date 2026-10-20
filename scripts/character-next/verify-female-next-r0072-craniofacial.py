"""Saved source-indexed morph readback; reversible control and pose scope only."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,sys,time,importlib.util
def module(n,p):
    s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
q=module('verify72form','build-female-next-r0072-craniofacial.py');v=module('verify72mesh','verify-female-next-r0061-complete-groom.py')
KEYS=['AFN72_CC0_'+n for n in q.COEFFICIENTS];BODY='AFN60_BODY_ORAL_AND_OCULAR_LINING';HAIR=('AFN68_MAIN_RENDER_CURVES','AFN68_FLYAWAY_RENDER_CURVES','AFN57_NATIVE_BROWS','AFN57_NATIVE_LASHES')
def digest(a):return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()
def world(o):
    d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;P=q.m.base.array3(d.position_data,'vector').astype('f8');A=np.array(o.matrix_world);return P@A[:3,:3].T+A[:3,3]
def controls():
    rig=bpy.data.objects['AFN69_BODY_CONTROLS'];out={'bones':[(b.name,b.parent.name if b.parent else None,np.array(b.matrix_local).tolist(),b.length) for b in rig.data.bones],'weights':{}}
    for n in q.m.native_names():
        o=bpy.data.objects[n];out['weights'][n]=digest(np.array([(i,g.group,g.weight) for i,p in enumerate(o.data.vertices) for g in p.groups],dtype='f8'))
    return out
def actual():
    out={}
    for n in q.m.native_names():
        o=bpy.data.objects[n];x=q.m.k.mesh(o);assert np.isfinite(x['V']).all();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
        loops=np.empty(len(me.loops),'i4');me.loops.foreach_get('vertex_index',loops);starts=np.empty(len(me.polygons),'i4');me.polygons.foreach_get('loop_start',starts);counts=np.empty(len(me.polygons),'i4');me.polygons.foreach_get('loop_total',counts);topology=digest(np.r_[loops,starts,counts]);ev.to_mesh_clear()
        out[n]={'V':x['V'],'T':x['T'],'evaluatedPolygonTopologySha256':topology}
    for n in HAIR:out[n]={'V':world(bpy.data.objects[n])}
    return out
def pose_rows():
    out={}
    for f in (1,13,49):
        bpy.context.scene.frame_set(f);bpy.context.view_layer.update();out[f]=actual()
    return out
def main():
    tick=time.time();assert q.sha(q.SRC)==q.SOURCE_SHA;bpy.ops.wm.open_mainfile(filepath=str(q.SRC));bpy.context.scene.frame_set(1)
    native={n:v.mesh_signature(bpy.data.objects[n]) for n in q.m.native_names()};hair={n:q.m.k.v59.native_curves(bpy.data.objects[n]) for n in HAIR};mats={x.name:q.m.k.f.v.v32.material_signature(x) for x in bpy.data.materials if x.use_nodes};ctrl=controls();lights=q.q.lights();view=[bpy.context.scene.view_settings.exposure,bpy.context.scene.view_settings.view_transform,bpy.context.scene.view_settings.look];v.raise_subdivision();baseline=pose_rows()
    ref=json.loads((q.E/'a-build-summary.json').read_text());path=Path(ref['output'])
    if '--history' in sys.argv:path=q.R/'sites-engine-journey/assets-source/aevrynd-character/female-next'/path.name
    assert q.sha(path)==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(1);body=bpy.data.objects[BODY];stored=[]
    for n in q.m.native_names():
        row=v.mesh_signature(bpy.data.objects[n])
        if n==BODY:
            for key in KEYS:assert key in row['keys'];row['keys'].pop(key)
        assert row==native[n],n
    assert hair=={n:q.m.k.v59.native_curves(bpy.data.objects[n]) for n in HAIR}
    assert mats=={n:q.m.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats};assert controls()==ctrl and q.q.lights()==lights
    assert view==[bpy.context.scene.view_settings.exposure,bpy.context.scene.view_settings.view_transform,bpy.context.scene.view_settings.look]
    ids=np.empty(len(body.data.vertices),'i4');body.data.attributes['AFN60_NativeVertexID'].data.foreach_get('value',ids);base=np.array([p.co[:] for p in body.data.shape_keys.key_blocks[0].data])
    for name,value in q.COEFFICIENTS.items():
        z=np.load(q.D/'morphs/L2'/(name+'.npz'),allow_pickle=False);delta=np.zeros((37436,3));delta[z['idx']]=z['delta'];key=body.data.shape_keys.key_blocks['AFN72_CC0_'+name];P=np.array([p.co[:] for p in key.data]);expected=(base+delta[ids]).astype('f4');assert np.array_equal(P,expected)
        assert abs(key.value-value)<1e-7 and key.relative_key==body.data.shape_keys.key_blocks[0];stored.append({'key':key.name,'value':key.value,'originalNativeIndexSculptDeltaExact':True})
    v.raise_subdivision();posed=pose_rows();rows=[]
    for f,p in posed.items():
        row={'frame':f,'parts':{}}
        for n,x in p.items():
            b=baseline[f][n];assert x['V'].shape==b['V'].shape
            if 'T' in x:
                # Quad tessellation is geometry-dependent. Verify the actual
                # evaluated polygon connectivity, then report changed diagonals.
                assert x['evaluatedPolygonTopologySha256']==b['evaluatedPolygonTopologySha256']
                assert x['T'].shape==b['T'].shape
            error=np.linalg.norm(x['V']-b['V'],axis=1);row['parts'][n]={'verticesOrPoints':len(error),'maximumComparedToR69M':float(error.max()),'changedAbove1Micrometre':int((error>1e-6).sum()),'currentGeometrySha256':digest(x['V'])}
            if 'T' in x:row['parts'][n].update(evaluatedPolygonTopologyExact=True,changedTessellationTriangleRows=int(np.any(x['T']!=b['T'],axis=1).sum()))
            if n in q.m.native_names()[:4] or n in HAIR[2:]:assert np.array_equal(x['V'],b['V']),n
        rows.append(row)
    for n in KEYS:body.data.shape_keys.key_blocks[n].value=0
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update();disabled=actual()
    for n,x in disabled.items():assert np.array_equal(x['V'],baseline[1][n]['V']),n
    for name,value in q.COEFFICIENTS.items():body.data.shape_keys.key_blocks['AFN72_CC0_'+name].value=value
    external=[];packed=0
    for im in bpy.data.images:
        if im.packed_file:packed+=1
        elif im.source=='FILE':
            p=Path(bpy.path.abspath(im.filepath));assert im.filepath.startswith('//') and p.exists();external.append({'relative':im.filepath,'sha256':q.sha(p)})
    assert len(external)==15 and not bpy.data.libraries and not bpy.app.handlers.frame_change_pre and not bpy.app.handlers.frame_change_post
    q.save('history-readback.json' if '--history' in sys.argv else 'independent-readback.json',{'status':'PASS_SAVED_NATIVE_SCULPT_AND_REVERSIBLE_CONTROLS_ONLY','source':str(path),'sha256':q.sha(path),'originalNativeGeometryKeysUVMaterialsExactExceptTwoAddedKeys':True,'originalRigWeightsBonesLightsAndColorManagementExact':True,'originalHairAndFacialFibreNativeDataExact':True,'eyesAndEvaluatedFacialFibresExactAtThreePoses':True,'newControls':stored,'disableNewControlsRecoversExactR69ActualNeutralGeometryIncludingHair':True,'actualPosedGeometryChanges':rows,'externalTextures':external,'packedImages':packed,'wholeAppearanceOrSelfContactOrNaturalMotionOrRuntimeAccepted':False,'scope':'Native author deltas, reversible controls and three sampled deformed configurations; not a contact certificate. Body-form changes do not inherit body/hair/oral contact acceptance.','seconds':time.time()-tick})
    print('R72_NATIVE_MORPH_READBACK_PASS',time.time()-tick,flush=True)
if __name__=='__main__':main()
