"""One bounded check for authored parent-guide construction, not a model trial."""
from pathlib import Path
import bpy,json
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0094-authored-growth-routing'
with bpy.data.libraries.load(str(R/'Reference/character/charmorph-vitruvian-cc0/hair.blend'),link=False) as (src,dst):dst.objects=['hair-src']
o=dst.objects[0];rows=[]
for ps in o.particle_systems:
 s=ps.settings;rows.append({'name':ps.name,'parents':len(ps.particles),'settingName':s.name,'childType':s.child_type,'children':s.rendered_child_count,'rootRadius':s.root_radius,'tipRadius':s.tip_radius,'radiusScale':s.radius_scale,'roundness':s.child_roundness,'kink':s.kink,'clump':s.clump_factor})
(E/'source-guide-library.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8');print('SOURCE_AUTHORED_GUIDES',json.dumps(rows),flush=True)
