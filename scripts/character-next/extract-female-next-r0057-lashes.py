"""Read original authored hair keys via their supported object-space API."""
from pathlib import Path
import bpy,numpy as np,json,sys
R=Path(r'D:\Download\Aevrynd');D=R/'Reference/character/charmorph-vitruvian-cc0';E=R/'Evidence/character-female-next/r0057-coherent-foundation'
FEMALE='--female' in sys.argv;PREFIX='female' if FEMALE else 'canonical'
bpy.ops.wm.open_mainfile(filepath=str(D/'canonical-female-data.blend'));o=bpy.data.objects['cm_vitruvian'];o.data.shape_keys.key_blocks['AFN57_Supplied_Female_Morph'].value=float(FEMALE);bpy.context.scene.frame_set(1);bpy.context.view_layer.update();o=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
for system,label in ((0,'lashes'),(1,'brows')):
    ps=o.particle_systems[system];mod=next(m for m in o.modifiers if m.type=='PARTICLE_SYSTEM' and m.particle_system==ps);key=ps.particles[0].hair_keys[0]
    schema={f.identifier:[{'name':p.identifier,'type':p.type,'output':p.is_output} for p in f.parameters] for f in key.bl_rna.functions}
    curves=[];counts=[]
    for particle in ps.particles:
        P=np.array([k.co_object(o,mod,particle)[:] for k in particle.hair_keys],dtype='f4');curves.append(P);counts.append(len(P))
    P=np.concatenate(curves);assert np.isfinite(P).all() and P[:,2].max()>1.5 and P[:,2].min()>1.5,('Object-space keys unavailable',P.min(0),P.max(0))
    np.savez_compressed(E/(PREFIX+'-object-space-'+label+'.npz'),positions=P,counts=np.array(counts,dtype='i4'))
    row={'curves':len(counts),'points':len(P),'countRange':[min(counts),max(counts)],'boundsM':[P.min(0).tolist(),P.max(0).tolist()],'source':'Canonical source facial hair, female morph disabled; evaluated ParticleHairKey.co_object API, no addon code.','schema':schema,'sourceRadiusM':ps.settings.root_radius*ps.settings.radius_scale}
    row['suppliedFemaleMorphValue']=float(FEMALE)
    (E/(PREFIX+'-object-space-'+label+'.json')).write_text(json.dumps(row,indent=2)+'\n',encoding='utf8');print('R57_FACIAL_HAIR_EXTRACTED',label,len(counts),len(P),flush=True)
