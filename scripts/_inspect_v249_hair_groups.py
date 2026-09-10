import bpy
for n in ['HairCoverageTiles_v246','HairCrownCoverage_v212','HairDetailFibers_v246','HairFiberBase','HairFiberDetail','HairFiberLOD1','HairSilhouetteCards_v246','HairlineNaturalCards_v214']:
 o=bpy.data.objects.get(n)
 if not o: continue
 print(n,'hide_render',o.hide_render,'hide_view',o.hide_viewport,'groups',[(g.name,len([v for v in o.data.vertices if any(x.group==g.index and x.weight>0 for x in v.groups)])) for g in o.vertex_groups])
