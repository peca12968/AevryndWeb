import bpy,json
from pathlib import Path
R=Path(r'D:\Download\Aevrynd');bpy.ops.wm.open_mainfile(filepath=str(R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0003-b-relaxed-study.blend'))
a=bpy.data.objects['AevryndFemaleCC0PalpebralClosure_R1097'];b=bpy.data.objects['AevryndFemaleNextPerioral_R0003'];plan=json.loads((R/'Evidence/character-female-next/r0003-topology/patch-plan.json').read_text());removed=set(plan['removedFaces']);kept=sorted({i for p in a.data.polygons if p.index not in removed for i in p.vertices})
for o in (a,b):
 o.hide_viewport=False;o.hide_set(False)
 for m in o.modifiers:
  if m.type=='SUBSURF':m.show_viewport=False
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ea=a.evaluated_get(dg).to_mesh();eb=b.evaluated_get(dg).to_mesh();diff=[((ea.vertices[i].co-eb.vertices[j].co).length,i,j) for j,i in enumerate(kept)];diff.sort(reverse=True);print('COMPARED='+json.dumps({'maxM':diff[0][0],'over1micrometre':sum(d[0]>1e-6 for d in diff),'top':diff[:4]}))
