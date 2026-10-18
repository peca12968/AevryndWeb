"""Explicit neutral surface triangles, with all-pose offending-strand culling."""
import bpy,json,hashlib,importlib.util
import numpy as np
from pathlib import Path
spec=importlib.util.spec_from_file_location('build',Path(__file__).with_name('build-female-next-r0018-layered-brows.py'));build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
S,E,solid=build.S,build.E,build.solid
def main():
    b=json.loads((E/'b-saved-build-verification.json').read_text());assert build.sha(b['output'])==b['outputSha256'];bpy.ops.wm.open_mainfile(filepath=b['output']);rig=bpy.data.objects['AFN_R0005_Rig'];before=build.controls();brows=[bpy.data.objects['AFN11_'+side+'_BrowFibres'] for side in ('L','R')];records=json.loads(Path(b['browBindings']).read_text());raw={};quadRows=[]
    for pose in ('neutral','gaze-left','gaze-right','turn-left','turn-right'):
        solid.stage.set_pose(rig,pose)
        for o in brows:
            P,T,tree=solid.data(o);pairs=[(a,z) for a,z in tree.overlap(tree) if a<z and set(T[a]).isdisjoint(T[z])]
            quadRows.append({'pose':pose,'object':o.name,'triangleIndexSha256':hashlib.sha256(np.array(T,np.int32).tobytes()).hexdigest(),'selfFibrePairs':[(int(T[a][0]//40),int(T[z][0]//40)) for a,z in pairs]})
    solid.stage.set_pose(rig,'neutral')
    for o in brows:
        _,T,_=solid.data(o);mesh=o.data;raw[o.name]={'coords':np.array([tuple(v.co) for v in mesh.vertices],np.float32),'pigment':np.array([v.value for v in mesh.attributes['AFN11_BrowPigment'].data],np.float32),'weights':[[(o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in mesh.vertices],'triangles':T,'materials':list(mesh.materials)}
        # Make the saved primitive definition equal to the evaluated neutral surface.
        m=bpy.data.meshes.new(o.name+'_ExplicitTriangles');m.from_pydata(raw[o.name]['coords'].tolist(),[],T);m.update()
        for material in raw[o.name]['materials']:m.materials.append(material)
        attr=m.attributes.new('AFN11_BrowPigment','FLOAT','POINT');attr.data.foreach_set('value',raw[o.name]['pigment']);o.data=m
        o.vertex_groups.clear();groups={name:o.vertex_groups.new(name=name) for name in sorted({name for weights in raw[o.name]['weights'] for name,_ in weights})}
        for i,weights in enumerate(raw[o.name]['weights']):
            for name,value in weights:groups[name].add([i],value,'REPLACE')
        for p in m.polygons:p.use_smooth=True
    triRows=[];edges={o.name:[] for o in brows}
    for pose in ('neutral','gaze-left','gaze-right','turn-left','turn-right'):
        solid.stage.set_pose(rig,pose)
        for o in brows:
            P,T,tree=solid.data(o);pairs=[(a,z) for a,z in tree.overlap(tree) if a<z and set(T[a]).isdisjoint(T[z])];fibrePairs=[(int(T[a][0]//40),int(T[z][0]//40)) for a,z in pairs];edges[o.name].extend(fibrePairs)
            triRows.append({'pose':pose,'object':o.name,'triangleIndexSha256':hashlib.sha256(np.array(T,np.int32).tobytes()).hexdigest(),'selfFibrePairs':fibrePairs})
    solid.stage.set_pose(rig,'neutral');keptRecords=[];rows=[];witness=[]
    for o in brows:
        local=[x for x in records if x['object']==o.name];byId={x['hair']:x for x in local};dropped=set();remaining=edges[o.name].copy()
        while remaining:
            counts={h:sum(h in pair for pair in remaining) for pair in remaining for h in pair};h=max(counts,key=lambda i:(counts[i],-byId[i]['lengthM'],-i));dropped.add(h);remaining=[pair for pair in remaining if h not in pair]
        kept=[x for x in local if x['hair'] not in dropped];ids=np.concatenate([np.arange(x['firstVertex'],x['firstVertex']+40) for x in kept]);mapping={int(i):j for j,i in enumerate(ids)};source=raw[o.name];F=[tuple(mapping[i] for i in f) for f in source['triangles'] if all(i in mapping for i in f)]
        m=bpy.data.meshes.new(o.name+'_StableCleanTriangles');m.from_pydata(source['coords'][ids].tolist(),[],F);m.update()
        for material in source['materials']:m.materials.append(material)
        attr=m.attributes.new('AFN11_BrowPigment','FLOAT','POINT');attr.data.foreach_set('value',source['pigment'][ids]);o.data=m;o.vertex_groups.clear();names=sorted({name for i in ids for name,_ in source['weights'][i]});groups={n:o.vertex_groups.new(name=n) for n in names}
        for j,i in enumerate(ids):
            for n,value in source['weights'][i]:groups[n].add([j],value,'REPLACE')
        for p in m.polygons:p.use_smooth=True
        for j,x in enumerate(kept):keptRecords.append(dict(x,sourceCandidateBHair=x['hair'],hair=j,firstVertex=j*40))
        o['aevrynd_revision']='female-next-r0018-c';o['aevrynd_root_binding']='aevrynd-female-next-r0018-c-brow-bindings.json';witness.append((o.name,source['coords'][ids],source['pigment'][ids],[source['weights'][i] for i in ids],F))
        rows.append({'object':o.name,'fibres':len(kept),'vertices':len(m.vertices),'triangles':len(F),'removedAdditionalFibres':sorted(dropped),'allFacesExplicitTriangles':True})
    assert build.controls()==before
    dst=S/'aevrynd-female-next-r0018-c-triangulated-brows-study.blend';bpy.context.scene['aevrynd_revision']='female-next-r0018-c';bpy.context.scene['aevrynd_release_state']='EXPLICIT_BROW_TRIANGLES_PENDING_INDEPENDENT_GATES';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(dst));bpy.ops.wm.open_mainfile(filepath=str(dst));assert build.controls()==before
    for name,p,pig,weights,F in witness:
        o=bpy.data.objects[name];assert np.array_equal(np.array([tuple(v.co) for v in o.data.vertices],np.float32),p);assert np.array_equal(np.array([v.value for v in o.data.attributes['AFN11_BrowPigment'].data],np.float32),pig);assert [[(o.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in o.data.vertices]==weights;assert [tuple(x.vertices) for x in o.data.polygons]==F
    path=S/'aevrynd-female-next-r0018-c-brow-bindings.json';path.write_text(json.dumps(keptRecords,separators=(',',':'))+'\n')
    build.save('triangle-stability-diagnosis.json',{'sourceCandidateB':b['output'],'sourceSha256':b['outputSha256'],'quadSurfaceAcrossPoses':quadRows,'explicitTriangleSurfaceBeforeCulling':triRows,'finalRemovedFibres':rows,'scope':'Actual evaluated primitive IDs and nonadjacent triangle checks in five sampled poses, before independent final verification. This does not establish a continuous-motion certificate or prove a general Blender defect.'})
    build.save('c-saved-build-verification.json',dict(b,output=str(dst),outputSha256=build.sha(dst),browBindings=str(path),browBindingsSha256=build.sha(path),layers=rows,subsetOfCandidateA=False,rootFibreSubsetOfCandidateB=True,retainedVerticesPigmentsWeightsExact=True,neutralSurfaceExplicitlyTriangulated=True,fileBytes=dst.stat().st_size,wallSeconds=None,status='REOPEN_EXPLICIT_TRIANGLE_CONTROL_PASS_COLLISION_PENDING'))
    build.save('candidate-c-contract.json',{'reason':'B passes three static cases but its left brow has four nonadjacent intersections in turn-left. Diagnose actual tessellation and test all five poses before final culling.','hypothesis':'Define the authoring/render surface with explicit neutral triangles and remove the union of localized offending strands across all sampled poses; preserve all retained vertices, pigment and weights.','maximumCandidatesThisRound':3,'rejectIf':['Any independent final pose crossing or unresolved containment.','Any non-brow state change.','Loss of the full-face readability gain.'],'limits':'No fourth style candidate and no relaxed collision exclusion.'})
    print('R0018_EXPLICIT_TRIANGLES_DONE '+json.dumps(rows),flush=True)
if __name__=='__main__':main()
