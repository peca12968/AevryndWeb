"""Read original studio groom data only; never execute embedded rig/hair code."""
from pathlib import Path
import bpy,numpy as np,json,hashlib
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0091-clump-cross-sections';REF=R/'Reference/character/blender-studio-ellie-v1-cc-by4';src=REF/'ellie.blend'
with bpy.data.libraries.load(str(src),link=False) as (a,b):b.objects=[n for n in a.objects if n.startswith('GEO-ellie_hair') or n in ['GEO-ellie_head','GEO-ellie_eye.L','GEO-ellie_eye.R']];b.texts=['ReadMe.txt']
rows=[];arrays={}
for o in b.objects:
 d=o.data;row={'name':o.name,'type':o.type,'matrix':np.array(o.matrix_world).tolist(),'vertices':len(d.vertices) if hasattr(d,'vertices') else None,'edges':len(d.edges) if hasattr(d,'edges') else None,'faces':len(d.polygons) if hasattr(d,'polygons') else None,'modifiers':[{'name':md.name,'type':md.type,'visible':md.show_viewport,'render':md.show_render} for md in o.modifiers],'particleSystems':[{'name':p.name,'type':p.settings.type,'count':p.settings.count,'particles':len(p.particles),'children':len(p.child_particles),'hairStep':p.settings.hair_step,'childType':p.settings.child_type,'childCount':p.settings.child_percent,'renderedChildren':p.settings.rendered_child_count} for p in o.particle_systems]}
 if o.type=='MESH':
  V=np.empty((len(d.vertices),3),'f4');d.vertices.foreach_get('co',V.ravel());A=np.array(o.matrix_world);arrays[o.name+'_world']=V@A[:3,:3].T+A[:3,3];edge=np.empty((len(d.edges),2),'i4');d.edges.foreach_get('vertices',edge.ravel());arrays[o.name+'_edges']=edge
  for pi,p in enumerate(o.particle_systems):
   if len(p.particles):
    counts=np.array([len(x.hair_keys) for x in p.particles],'i4');points=np.array([list(k.co) for part in p.particles for k in part.hair_keys]);arrays[o.name+'_particle'+str(pi)+'_keyLocal']=points;arrays[o.name+'_particle'+str(pi)+'_counts']=counts;row.setdefault('nativeParticleKeys',[]).append({'points':len(points),'countRange':[int(counts.min()),int(counts.max())]})
 rows.append(row)
readme=b.texts[0].as_string();(E/'ellie-embedded-ReadMe.txt').write_text(readme,encoding='utf8');np.savez_compressed(E/'ellie-original-groom-data.npz',**arrays);(E/'ellie-original-groom-inspection.json').write_text(json.dumps({'source':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'embeddedScriptsExecuted':False,'objects':rows},indent=2)+'\n',encoding='utf8');print('R91_ELLIE_DATA',json.dumps(rows),flush=True)
