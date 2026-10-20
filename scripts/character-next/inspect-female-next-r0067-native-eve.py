"""Inspect the actual authored Eve system and native conversion API."""
from pathlib import Path
import bpy,json,numpy as np,time,hashlib
R=Path(r'D:\Download\Aevrynd');D=R/'Reference/character/charmorph-vitruvian-cc0';E=R/'Evidence/character-female-next/r0067-native-eve';E.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(E/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def props(x):
    rows={}
    for p in x.bl_rna.properties:
        if p.identifier=='rna_type' or p.type in ('POINTER','COLLECTION'):continue
        try:v=getattr(x,p.identifier);v=list(v) if getattr(p,'is_array',False) else v;json.dumps(v);rows[p.identifier]=v
        except (TypeError,ValueError,AttributeError):continue
    return rows
def main():
    tick=time.time();p=D/'hair.blend';assert sha(p)=='2abf4b59006148420e0087a98e9e9a13e02e4b0e6cca6ee73c63efbe6e8da811';bpy.ops.wm.open_mainfile(filepath=str(p));o=bpy.data.objects['hair-src'];bpy.context.view_layer.objects.active=o
    if o.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
    for md in o.modifiers:
        if md.type=='PARTICLE_SYSTEM':md.show_viewport=md.show_render=md.particle_system.name=='Eve'
    bpy.context.scene.frame_set(1);bpy.context.view_layer.update();ps=next(ps for ps in o.particle_systems if ps.name=='Eve');native=props(ps.settings)
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());pse=next(s for s in ev.particle_systems if s.name=='Eve');mod=next(m for m in ev.modifiers if m.type=='PARTICLE_SYSTEM' and m.particle_system.name=='Eve');counts=np.array([len(p.hair_keys) for p in pse.particles],dtype='i4');Q=np.array([key.co_object(ev,mod,p)[:] for p in pse.particles for key in p.hair_keys],dtype='f4');assert np.isfinite(Q).all()
    ops={}
    for group,name in [('curves','convert_from_particle_system'),('object','modifier_convert')]:
        try:op=getattr(getattr(bpy.ops,group),name);rna=op.get_rna_type();ops[group+'.'+name]={'available':True,'parameters':[(p.identifier,p.description) for p in rna.properties]}
        except Exception as ex:ops[group+'.'+name]={'available':False,'reason':str(ex)}
    row={'source':str(p),'sha256':sha(p),'settings':native,'particles':len(pse.particles),'evaluatedChildren':len(pse.child_particles),'keys':sorted(set(counts.tolist())),'nativeGuideBounds':[Q.min(0).tolist(),Q.max(0).tolist()],'emitterVertices':len(o.data.vertices),'canonicalPositionsExact':np.array_equal(np.array([v.co[:] for v in o.data.vertices],dtype='f4'),np.load(D/'Default.npy').astype('f4')),'matSlots':[m.name if m else None for m in o.data.materials],'particleMaterial':ps.settings.material,'emitterMatrix':np.array(o.matrix_world).tolist(),'operators':ops,'radiusDescriptions':{n:ps.settings.bl_rna.properties[n].description for n in ('root_radius','tip_radius','radius_scale')},'autoExecutionDisabled':True,'newSoftwareOrAddons':False,'seconds':time.time()-tick}
    save('native-eve-inspection.json',row);print('R67_EVE_NATIVE',len(pse.particles),len(pse.child_particles),'KEYS',row['keys'],'OPS',ops,flush=True)
if __name__=='__main__':main()
