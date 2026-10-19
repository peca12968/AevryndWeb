"""Inspect actual installed curve primitive/width controls before any claim."""
import bpy,json
from pathlib import Path
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0034-master-locks'
bpy.ops.wm.open_mainfile(filepath=str(R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0034-c-preview.blend'))
s=bpy.context.scene;result={}
for name,owner in [('render',s.render),('eevee',s.eevee),('cycles',s.cycles),('curves',getattr(s,'curves',None))]:
    if owner is None:continue
    rows={}
    for p in owner.bl_rna.properties:
        if any(w in p.identifier.lower() for w in ('hair','curve','shape','width','subdiv')):
            v=getattr(owner,p.identifier)
            if p.type in ('BOOLEAN','INT','FLOAT','STRING','ENUM'):rows[p.identifier]={'value':v,'enum':[x.identifier for x in p.enum_items] if p.type=='ENUM' else None}
    result[name]=rows
o=next(o for o in s.objects if o.type=='CURVES' and not o.hide_render);d=o.data;result['native']={'name':o.name,'curves':len(d.curves),'points':len(d.points),'attributes':[(x.name,x.data_type,x.domain) for x in d.attributes],'pointRadiusFirst':[float(d.attributes['radius'].data[i].value) for i in range(8)]}
(E/'actual-curve-display-settings.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
