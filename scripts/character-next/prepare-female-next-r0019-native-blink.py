"""Own sparse-data importer; native CC0 closure + exact subdivision correspondence."""
import bpy,json,gzip,hashlib,shutil,sys,time,importlib.util
import numpy as np
from pathlib import Path
spec=importlib.util.spec_from_file_location('inspect_source',Path(__file__).with_name('inspect-female-next-r0019-blink-source.py'));inspect=importlib.util.module_from_spec(spec);spec.loader.exec_module(inspect)
R,S,E,SRC,ADDON=inspect.R,inspect.S,inspect.E,inspect.SRC,inspect.ADDON
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,data):(E/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def positions(mesh):
    p=np.empty((len(mesh.vertices),3),np.float32);mesh.vertices.foreach_get('co',p.ravel());return p
def evaluate(o,with_support=False):
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();obj=o.evaluated_get(dg);m=obj.to_mesh(preserve_all_data_layers=True,depsgraph=dg);p=positions(m).astype(np.float64);f=np.array([tuple(x.vertices) for x in m.polygons],np.int32);M=np.array(o.matrix_world,dtype=np.float64);p=p@M[:3,:3].T+M[:3,3]
    support={}
    if with_support:
        for side in ('L','R'):
            v=np.empty(len(m.vertices),np.float32);m.attributes['AFN19_Support_'+side].data.foreach_get('value',v);support[side]=v>0
    obj.to_mesh_clear();return (p,f,support) if with_support else (p,f)
def main():
    start=time.time();manifest=json.loads((S.parent/'female-next.asset.json').read_text());assert sha(SRC)==manifest['workingReviewSha256']
    save('iteration-contract.json',{'previousGoalTurnClassification':'progress: r0018 C integrated brow geometry retained after controlled whole-face/closeup views and scoped five-pose checks; no full character acceptance.','source':str(SRC),'sourceSha256':sha(SRC),'stage':'B_COMPLETE_HEAD_IN_PROGRESS','primaryDefect':'No eyelid or lash blink deformation exists; head is a rigid stare.','hypothesis':'The retained native base has exact subdivision correspondence to the current high-resolution body. Transfer authored core CC0 eye-closure data through that correspondence, then bind lash/brow fibre motion to the actual deformed skin.','minimalExperiment':'Prove vertex/polygon correspondence and export separate L/R high-resolution closure deltas before creating a candidate.','rejectIf':['Native and current body polygon/vertex IDs do not correspond exactly.','Closure changes unsupported far regions or closes through the actual eye geometry.','Lashes/brows remain frozen or lose their skin anchors.','Neutral appearance, eye position, skin/material/exposure change.'],'resources':{'threads':4,'nativeVertices':19158,'bodyVertices':214050,'initialTargets':6,'candidatesMaximum':3,'initialClosureSamples':[0,.5,1]},'licensing':'Installed core target graphical data is CC0 per official MPFB FAQ; no MPFB program source imported/copied into engine.'})
    refs=E/'cc0-native-targets';refs.mkdir(exist_ok=True);sources=[];D={}
    for side in ('left','right'):
        delta=np.zeros((19158,3),np.float64)
        for race,weight in (('african',.2),('asian',.5),('caucasian',.3)):
            p=ADDON/f'data/targets/expression/units/{race}/eye-{side}-closure.target.gz';dst=refs/f'{race}-eye-{side}-closure.target.gz';shutil.copy2(p,dst);assert sha(p)==sha(dst)
            raw=gzip.decompress(p.read_bytes()).decode('utf8');rows=np.array([[float(v) for v in line.split()] for line in raw.splitlines() if line and not line.startswith('#')]);ids=rows[:,0].astype(np.int64)
            # MakeHuman decimetres, Y-up/front +Z -> Blender metres, Z-up/front -Y.
            dv=rows[:,[1,3,2]]*.1;dv[:,1]*=-1;delta[ids]+=weight*dv;sources.append({'installedSource':str(p),'archive':str(dst),'sha256':sha(p),'weight':weight,'license':'CC0-1.0 core graphical target data','reference':'https://static.makehumancommunity.org/mpfb/faq/build_other_chargen.html'})
        D['L' if side=='left' else 'R']=delta
    save('references.json',{'coreAssets':sources,'targetConcepts':'https://static.makehumancommunity.org/mpfb/docs/assets/concept_targets.html','licenseDeclaration':'https://static.makehumancommunity.org/mpfb/faq/build_other_chargen.html','scope':'Only sparse geometric data reused. Axis/unit conversion, delta transfer, binding and verification code authored locally. Blender is the offline evaluator; no MPFB Python source or runtime dependency copied.'})
    bpy.ops.wm.open_mainfile(filepath=str(SRC));rig=bpy.data.objects['AFN_R0005_Rig']
    for bone in rig.pose.bones:bone.matrix_basis.identity()
    bpy.context.view_layer.update();raw=bpy.data.objects['AFN_R0005_EditableNativeCC0'];current=bpy.data.objects['AFN_R0008_Body'];original=positions(current.data)
    temp=raw.copy();temp.data=raw.data.copy();temp.name='AFN19_TEMP_NATIVE_TRANSFER';bpy.context.scene.collection.objects.link(temp);temp.hide_viewport=False;temp.hide_set(False);temp.hide_render=True
    sub=temp.modifiers.new('AFN19_MATCH_SOURCE_SUBDIVISION','SUBSURF');sub.levels=2;sub.render_levels=2;sub.subdivision_type='CATMULL_CLARK'
    for side in ('L','R'):
        active=np.linalg.norm(D[side],axis=1)>0
        # Generic point attributes use a different interpolation kernel from
        # Catmull-Clark positions. Conservatively expand four coarse edge rings
        # for two subdivision levels, then independently bound outside deltas.
        edges=np.array([tuple(e.vertices) for e in temp.data.edges],np.int32)
        for _ in range(4):
            grow=edges[active[edges].any(axis=1)].ravel();active[grow]=True
        a=temp.data.attributes.new('AFN19_Support_'+side,'FLOAT','POINT');a.data.foreach_set('value',active.astype(np.float32))
    baseline,faces,support=evaluate(temp,True);currentFaces=np.array([tuple(f.vertices) for f in current.data.polygons],np.int32)
    topology={'nativeEvaluatedVertices':len(baseline),'currentBodyVertices':len(original),'nativePolygons':len(faces),'currentPolygons':len(currentFaces),'exactPolygonIndices':bool(np.array_equal(faces,currentFaces))}
    save('topology-correspondence.json',topology)
    assert len(baseline)==len(original) and topology['exactPolygonIndices'],topology
    basis=temp.data.shape_keys.key_blocks[0];P=np.empty((len(basis.data),3),np.float32);basis.data.foreach_get('co',P.ravel());key=temp.shape_key_add(name='AFN19_TEMP_CLOSURE',from_mix=False);key.relative_key=basis
    fields={};rows=[]
    inverse=np.linalg.inv(np.array(current.matrix_world,dtype=np.float64))[:3,:3]
    for side in ('L','R'):
        key.data.foreach_set('co',(P.astype(np.float64)+D[side]).astype(np.float32).ravel());key.value=1.;closed,closedFaces=evaluate(temp);assert np.array_equal(faces,closedFaces);key.value=0.;delta=(closed-baseline)@inverse.T
        outsideLengths=np.linalg.norm(delta[~support[side]],axis=1);outsideNoise=float(outsideLengths.max())
        if outsideNoise>=5.e-7:
            outsideIds=np.flatnonzero(~support[side]);bad=outsideIds[outsideLengths>5.e-7]
            save('support-mask-diagnosis.json',{'side':side,'attributeSupportVertices':int(support[side].sum()),'outsideMaximumMoveM':outsideNoise,'outsideAbove0p5um':len(bad),'outsideSampleIds':bad[:20].tolist(),'outsideAffectedBoundsM':[[float(original[bad,a].min()),float(original[bad,a].max())] for a in range(3)],'status':'ATTRIBUTE_INTERPOLATION_IS_NOT_A_SUFFICIENT_POSITION_STENCIL_BOUND'})
        assert outsideNoise<5.e-7
        delta[~support[side]]=0
        fields['support'+side]=support[side]
        lengths=np.linalg.norm(delta,axis=1);changed=lengths>1.e-7
        fields['delta'+side]=delta.astype(np.float32);rows.append({'side':side,'affectedAbove0p1um':int(changed.sum()),'subdivisionSupportVertices':int(support[side].sum()),'maximumDiscardedUnrelatedEvaluationNoiseM':outsideNoise,'maximumMoveM':float(lengths.max()),'affectedBoundsM':[[float(original[changed,a].min()),float(original[changed,a].max())] for a in range(3)],'nativeTargetCoordinateProof':{'axisMap':'(x,-z,y)','scale':.1,'rawSparseDeltaVertexBounds':[[float(P[np.linalg.norm(D[side],axis=1)>0,a].min()),float(P[np.linalg.norm(D[side],axis=1)>0,a].max())] for a in range(3)]}})
    fields['neutralBody']=original;fields['nativeNeutral']=baseline.astype(np.float32);fields['faces']=faces
    cache=S/'aevrynd-female-next-r0019-native-blink-data.npz';np.savez_compressed(cache,**fields)
    mesh=temp.data;bpy.data.objects.remove(temp,do_unlink=True);bpy.data.meshes.remove(mesh)
    save('native-delta-transfer.json',{'status':'PASS_EXACT_NATIVE_SUBDIVISION_CORRESPONDENCE','source':str(SRC),'sourceSha256':sha(SRC),'cache':str(cache),'cacheSha256':sha(cache),'topology':topology,'bodyDifferenceVsNativeNeutralMaxM':float(np.linalg.norm(original-baseline,axis=1).max()),'closureFields':rows,'originalBodyNotModified':bool(np.array_equal(positions(current.data),original)),'sourceFileNotSaved':True,'wallSeconds':time.time()-start,'scope':'Authored closure displacement transferred by exact indexed subdivision lineage. No collision, anatomical closure, lash binding, visual or runtime acceptance yet.'})
    print('R0019_NATIVE_TRANSFER_PASS '+json.dumps(rows),flush=True)
if __name__=='__main__':main()
