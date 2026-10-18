"""Diagnose exact intersecting fibre IDs; remove only a minimal offending set."""
import bpy,json,importlib.util
import numpy as np
from pathlib import Path
spec=importlib.util.spec_from_file_location('build',Path(__file__).with_name('build-female-next-r0018-layered-brows.py'));build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
R,S,E=build.R,build.S,build.E;solid=build.solid
def main():
    a=json.loads((E/'saved-build-verification.json').read_text());assert build.sha(a['output'])==a['outputSha256']
    failed=json.loads((E/'saved-static-verification.json').read_text());assert failed['status']=='FAIL_OR_UNRESOLVED' and failed['candidateSha256']==a['outputSha256']
    bpy.ops.wm.open_mainfile(filepath=a['output']);before=build.controls();rig=bpy.data.objects['AFN_R0005_Rig'];solid.stage.set_pose(rig,'neutral');records=json.loads(Path(a['browBindings']).read_text());newRecords=[];diagnoses=[];witness=[];rows=[]
    for side in ('L','R'):
        o=bpy.data.objects['AFN11_'+side+'_BrowFibres'];P,T,tree=solid.data(o);pairs=[(i,j) for i,j in tree.overlap(tree) if i<j and set(T[i]).isdisjoint(T[j])]
        local=[x for x in records if x['object']==o.name];byId={x['hair']:x for x in local};edges=[(int(T[i][0]//40),int(T[j][0]//40)) for i,j in pairs];dropped=set();remaining=edges.copy()
        while remaining:
            counts={h:sum(h in edge for edge in remaining) for edge in remaining for h in edge}
            remove=max(counts,key=lambda h:(counts[h],-byId[h]['lengthM'],-h));dropped.add(remove);remaining=[e for e in remaining if remove not in e]
        diagnoses.append({'object':o.name,'trianglePairs':pairs,'fibrePairs':edges,'removedFibreIds':sorted(dropped),'failurePositionsM':[[list(P[T[i][0]]),list(P[T[j][0]])] for i,j in pairs],'classification':'within-strand self fold' if edges and all(x==y for x,y in edges) else 'between-strand or mixed' if edges else 'none'})
        old=o.data;oldCoords=np.array([tuple(v.co) for v in old.vertices],np.float32);oldPigment=np.array([v.value for v in old.attributes['AFN11_BrowPigment'].data],np.float32);oldWeights=[[(o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in old.vertices]
        kept=[x for x in local if x['hair'] not in dropped];ids=np.concatenate([np.arange(x['firstVertex'],x['firstVertex']+40) for x in kept]);mapping={int(oldIndex):i for i,oldIndex in enumerate(ids)}
        newFaces=[tuple(mapping[i] for i in f.vertices) for f in old.polygons if all(i in mapping for i in f.vertices)]
        mesh=bpy.data.meshes.new('AFN18_'+side+'_CleanLayeredBrows');mesh.from_pydata(oldCoords[ids].tolist(),[],newFaces);mesh.update()
        for mat in old.materials:mesh.materials.append(mat)
        attr=mesh.attributes.new('AFN11_BrowPigment','FLOAT','POINT');attr.data.foreach_set('value',oldPigment[ids]);o.data=mesh;o.vertex_groups.clear();groups={name:o.vertex_groups.new(name=name) for name in sorted({name for i in ids for name,_ in oldWeights[i]})}
        for j,i in enumerate(ids):
            for name,value in oldWeights[i]:groups[name].add([j],value,'REPLACE')
        for poly in mesh.polygons:poly.use_smooth=True
        o['aevrynd_revision']='female-next-r0018-b';o['aevrynd_root_binding']='aevrynd-female-next-r0018-b-brow-bindings.json'
        for j,x in enumerate(kept):
            y=dict(x,sourceCandidateAHair=x['hair'],sourceCandidateAFirstVertex=x['firstVertex'],hair=j,firstVertex=j*40);newRecords.append(y)
        assert np.array_equal(np.array([tuple(v.co) for v in mesh.vertices],np.float32),oldCoords[ids])
        witness.append((o.name,oldCoords[ids],oldPigment[ids],[oldWeights[i] for i in ids]))
        rows.append({'object':o.name,'fibres':len(kept),'vertices':len(mesh.vertices),'triangles':sum(len(p.vertices)-2 for p in mesh.polygons),'removedFibres':len(dropped)})
    assert build.controls()==before
    dest=S/'aevrynd-female-next-r0018-b-clean-layered-brows-study.blend';scene=bpy.context.scene;scene['aevrynd_revision']='female-next-r0018-b';scene['aevrynd_release_state']='TARGETED_BROW_SELF_FOLD_REMOVAL_PENDING_GATES';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(dest));bpy.ops.wm.open_mainfile(filepath=str(dest));assert build.controls()==before
    for name,p,pig,weights in witness:
        o=bpy.data.objects[name];assert np.array_equal(np.array([tuple(v.co) for v in o.data.vertices],np.float32),p);assert np.array_equal(np.array([v.value for v in o.data.attributes['AFN11_BrowPigment'].data],np.float32),pig);assert [[(o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in o.data.vertices]==weights
    bindingPath=S/'aevrynd-female-next-r0018-b-brow-bindings.json';bindingPath.write_text(json.dumps(newRecords,separators=(',',':'))+'\n')
    build.save('self-crossing-diagnosis.json',{'sourceSha256':a['outputSha256'],'diagnosis':diagnoses,'repair':'Greedy minimal incident-fibre removal; all retained fibre vertices, pigments and weights are bitwise/equal unchanged. No collision exclusions or moved roots. Full saved checks follow.','removedFibres':sum(x['removedFibres'] for x in rows)})
    build.save('b-saved-build-verification.json',dict(a,output=str(dest),outputSha256=build.sha(dest),browBindings=str(bindingPath),browBindingsSha256=build.sha(bindingPath),layers=rows,subsetOfCandidateA=True,retainedVerticesPigmentsWeightsExact=True,fileBytes=dest.stat().st_size,wallSeconds=None,status='REOPEN_SUBSET_CONTROL_PASS_COLLISION_PENDING'))
    build.save('candidate-b-contract.json',{'sourceCandidateA':a['output'],'sourceCandidateASha256':a['outputSha256'],'originalControlSource':a['source'],'reason':'Candidate A improves full-face brow readability but fails four nonadjacent self-triangle pair checks.','hypothesis':'Remove only individually localized offending fibres, preserving every retained vertex/weight/pigment, then independently recheck all five poses.','rejectIf':['Any remaining crossing or containment ambiguity.','Any non-brow state change.','Brow appearance loses the A improvement.'],'maximumCandidatesThisRound':2})
    print('R0018_TARGETED_REMOVAL '+str(sum(x['removedFibres'] for x in rows)),flush=True)
if __name__=='__main__':main()
