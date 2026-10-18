"""Independently reopen all r0004 saved candidates and inspect mesh contracts."""
import bpy, json, math, hashlib
from collections import Counter
from pathlib import Path
ROOT=Path(r'D:\Download\Aevrynd')
OUT=ROOT/'Evidence/character-female-next/r0004-surface-conforming'
source=ROOT/'engine/assets/characters/female-next/source'
results=[]
for label in ('a-soft-contact','b-relaxed','c-parted'):
    path=source/f'aevrynd-female-next-r0004-{label}-study.blend'
    bpy.ops.wm.open_mainfile(filepath=str(path))
    obj=bpy.data.objects['AevryndFemaleNextPerioral_R0004'];mesh=obj.data
    counts=Counter(tuple(sorted((p.vertices[j],p.vertices[(j+1)%len(p.vertices)]))) for p in mesh.polygons for j in range(len(p.vertices)))
    deform_names={b.name for b in bpy.data.objects['AevryndFemaleRig'].data.bones if b.use_deform}
    deform_ids={g.index for g in obj.vertex_groups if g.name in deform_names}
    sums=[sum(g.weight for g in v.groups if g.group in deform_ids) for v in mesh.vertices]
    missing=[i for i,s in enumerate(sums) if s<1e-6]
    badkey=[]
    for key in mesh.shape_keys.key_blocks:
        if len(key.data)!=len(mesh.vertices):badkey.append(key.name)
        if any(not math.isfinite(x) for v in key.data for x in v.co):badkey.append(key.name+':nonfinite')
    invalid_material_faces=sum(p.material_index>=len(mesh.materials) or mesh.materials[p.material_index] is None for p in mesh.polygons)
    mesh.calc_loop_triangles()
    dg=bpy.context.evaluated_depsgraph_get();dg.update()
    evaluated=obj.evaluated_get(dg);evaluated_mesh=evaluated.to_mesh();evaluated_mesh.calc_loop_triangles()
    evaluated_counts={'vertices':len(evaluated_mesh.vertices),'triangles':len(evaluated_mesh.loop_triangles),'scope':'body with current subdivision and armature modifiers'}
    evaluated.to_mesh_clear()
    results.append({'label':label,'path':str(path),'reopenSucceeded':True,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'vertices':len(mesh.vertices),'polygons':len(mesh.polygons),'triangles':len(mesh.loop_triangles),'shapeKeys':len(mesh.shape_keys.key_blocks),'badShapeKeys':badkey,'boundaryEdges':sum(n==1 for n in counts.values()),'edgesWithMoreThanTwoFaces':sum(n>2 for n in counts.values()),'looseVertices':len(mesh.vertices)-len({i for p in mesh.polygons for i in p.vertices}),'missingDeformWeights':len(missing),'deformWeightMin':min(sums),'deformWeightMax':max(sums),'invalidMaterialFaces':invalid_material_faces,'materialSlots':len(mesh.materials),'images':len(bpy.data.images),'rigBones':len(bpy.data.objects['AevryndFemaleRig'].data.bones),'hairCurves':len(bpy.data.objects['AevryndFemaleGradedHairlineGroom_R1081'].data.curves),'hairPoints':len(bpy.data.objects['AevryndFemaleGradedHairlineGroom_R1081'].data.points),'runtimeCpuMs':None,'runtimeGpuMs':None,'runtimeMemoryBytes':None})
    results[-1]['evaluatedGeometry']=evaluated_counts
    results[-1]['statisticsScope']='Per-candidate visible body control cage. The separate eyes and curves, and hidden historical bodies, are not included in its mesh counts.'
(OUT/'saved-files-verification.json').write_text(json.dumps({'revision':'female-next-r0004','results':results,'scope':'file integrity, mesh topology and skinning only; does not supersede collision or visual failures'},indent=2)+'\n',encoding='utf-8')
print(json.dumps(results,indent=2))
