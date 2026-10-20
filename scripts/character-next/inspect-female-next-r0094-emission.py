"""Bounded source-author growth-region lookup, no source/addon execution."""
from pathlib import Path
import bpy,json,numpy as np
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0094-authored-growth-routing';D=R/'Reference/character/charmorph-vitruvian-cc0'
with bpy.data.libraries.load(str(D/'hair.blend'),link=False) as (src,dst):dst.objects=['hair-src']
o=dst.objects[0];bpy.context.scene.collection.objects.link(o);ps=o.particle_systems['Eve'];names=['vertex_group_density','vertex_group_length','vertex_group_clump','vertex_group_kink','vertex_group_roughness_1','vertex_group_roughness_2','vertex_group_roughness_end'];report={'particleSystemFields':{n:getattr(ps,n,None) for n in names},'vertexGroups':[g.name for g in o.vertex_groups],'settings':{p.identifier:getattr(ps.settings,p.identifier) for p in ps.settings.bl_rna.properties if p.type in ['FLOAT','INT','BOOLEAN','ENUM','STRING'] and not p.is_readonly},'bounds':[[min(v.co[i] for v in o.data.vertices),max(v.co[i] for v in o.data.vertices)] for i in range(3)]}
group=ps.vertex_group_density or ("scalp" if "scalp" in o.vertex_groups else "")
if group:
 g=o.vertex_groups[group];ids=[];weights=[]
 for v in o.data.vertices:
  for a in v.groups:
   if a.group==g.index and a.weight>0:ids.append(v.index);weights.append(a.weight)
 np.savez_compressed(E/'original-Eve-density-region.npz',vertexIDs=np.array(ids,'i4'),weights=np.array(weights,'f4'));report['authorScalpRegion']={'group':group,'vertices':len(ids),'scope':'Source-author scalp vertex group, not automatically the Eve particle density/emission setting; Eve density field is separately recorded.'};report['scalpWorldBoundsNative']=[[min(o.data.vertices[i].co[j] for i in ids),max(o.data.vertices[i].co[j] for i in ids)] for j in range(3)]
(E/'original-Eve-emission.json').write_text(json.dumps(report,indent=2,default=lambda x:list(x))+'\n',encoding='utf8');print('EVE_EMISSION',report['particleSystemFields'],report.get('densityRegion'),report['vertexGroups'],flush=True)
