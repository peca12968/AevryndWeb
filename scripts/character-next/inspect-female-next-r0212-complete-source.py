
from pathlib import Path
import bpy,numpy as np,json,datetime,hashlib,importlib.util
from mathutils import Vector
p=json.loads(Path('F:/AevryndStorage/character-development-paths.json').read_text('utf-8'));A=Path(p['directCharacterArchiveAccess']);E=A/'evidence/character-female-next/r0212-complete-artist-volume-foundation';F=Path('F:/AevryndEvidence/r0212-complete-artist-volume-foundation');ART=Path('C:/Users/USER/AppData/Local/Temp/Aevrynd-hair-editor-reference/hair.blend');assert hashlib.file_digest(ART.open('rb'),'sha256').hexdigest()=='93aedaef061dc14618a0fcfad33c3df816fa755e8093381cbdfd0fd4c34527f5';sp=importlib.util.spec_from_file_location('r209base',A/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h;bpy.ops.wm.open_mainfile(filepath=str(ART));s=bpy.context.scene;names=['straight_hair_to_shoulder'];hairs=[bpy.data.objects[n] for n in names];body=hairs[0].data.surface
for col in bpy.data.collections:col.hide_viewport=False;col.hide_render=False
def layer(l):
 l.exclude=False;l.hide_viewport=False
 for c in l.children:layer(c)
layer(bpy.context.view_layer.layer_collection)
for ob in bpy.data.objects:ob.hide_render=ob not in hairs+[body];ob.hide_set(ob not in hairs+[body])
rows=[];arrays={}
for name,ob in zip(names,hairs):
 for md in ob.modifiers:md.show_viewport=md.show_render
 bpy.context.view_layer.update();P,off=m.curveworld(ob);assert len(P)<2000000;rows.append({'name':name,'rawGuides':len(ob.data.curves),'rawPoints':len(ob.data.position_data),'effectiveCurves':len(off),'effectivePoints':len(P),'boundsWorld':np.stack([P.min(0),P.max(0)]).tolist(),'effectiveModifierInputs':{md.name:{sock.identifier:{'name':sock.name,'fields':{prop.identifier:list(getattr(getattr(md.properties.inputs,sock.identifier),prop.identifier)) if getattr(prop,'is_array',False) else getattr(getattr(md.properties.inputs,sock.identifier),prop.identifier) for prop in getattr(md.properties.inputs,sock.identifier).bl_rna.properties if prop.identifier not in ['name','rna_type'] and not prop.is_readonly and prop.type not in ['POINTER','COLLECTION']}} for sock in md.node_group.interface.items_tree if sock.item_type=='SOCKET' and sock.in_out=='INPUT' and sock.socket_type!='NodeSocketGeometry'} for md in ob.modifiers if md.type=='NODES'}})
 # Actual operative pre-generation guides, full IDs/UV/material-independent geometry.
 for md in ob.modifiers:md.show_viewport=(md==ob.modifiers[0])
 bpy.context.view_layer.update();gp,go=m.curveworld(ob);de=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;uv=h.arr(de.attributes['surface_uv_coordinate'].data,'vector',len(go),2);arrays[name+'_operativeP']=gp;arrays[name+'_operativeOffsets']=go;arrays[name+'_operativeUV']=uv;arrays[name+'_rawP']=h.arr(ob.data.position_data,'vector',len(ob.data.position_data),3);arrays[name+'_matrixWorld']=np.array(ob.matrix_world)
 for md in ob.modifiers:md.show_viewport=md.show_render
np.savez_compressed(E/'source-operative-complete-rest-guide-data.npz',**arrays)
sourceSnapshot=F/'aevrynd-female-next-r0212-cc0-shoulder-input.blend';keep=set(hairs+[body]);discard=[o for o in bpy.data.objects if o not in keep]
for ob in discard:bpy.data.objects.remove(ob,do_unlink=True)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(sourceSnapshot),compress=True)
q0={'file':str(sourceSnapshot),'sha256':hashlib.file_digest(sourceSnapshot.open('rb'),'sha256').hexdigest(),'bytes':sourceSnapshot.stat().st_size,'author':'Tomas Klecer','license':'CC0','originalAssetHash':'93aedaef061dc14618a0fcfad33c3df816fa755e8093381cbdfd0fd4c34527f5','scope':'Exact source geometry/effective nodes after removing unrelated styles, before own camera/light; no style parameter changed.'};(E/'source-input-snapshot.json').write_bytes((json.dumps(q0,indent=2)+'\n').encode())
camera=bpy.data.objects.new('AFN212_SOURCE_ONLY_CAMERA',bpy.data.cameras.new('AFN212_SOURCE_ONLY_CAMERA'));s.collection.objects.link(camera);s.camera=camera;camera.data.lens=65;target=Vector((0,-.02,1.48))
for name,energy,size,loc in [('Key',180,1.0,(-.5,-.6,2.1)),('Fill',100,1.0,(.6,-.5,1.7)),('Rim',140,.7,(.2,.5,2.0))]:
 ob=bpy.data.objects.new('AFN212_SOURCE_ONLY_'+name,bpy.data.lights.new('AFN212_SOURCE_ONLY_'+name,'AREA'));s.collection.objects.link(ob);ob.data.energy=energy;ob.data.shape='DISK';ob.data.size=size;ob.location=loc;ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=16;s.cycles.seed=61061;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=-.5;s.world.color=(.04,.04,.04);s.render.film_transparent=False;s.render.hair_type='STRAND';s.render.hair_subdiv=3
for label,loc in [('front',(0,-1.4,1.5)),('profile',(1.2,-.02,1.5)),('back',(0,1.4,1.5))]:
 camera.location=loc;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(F/f'original-cc0-shoulder-source-{label}.png');bpy.ops.render.render(write_still=True)
q={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(ART),'sourceOnlyNotCurrentWomanResult':True,'rows':rows,'sourceBody':body.name,'originalSourceUnmodified':True};(E/'complete-different-source-rest-reference.json').write_bytes((json.dumps(q,ensure_ascii=False,indent=2)+'\n').encode());print('R212_COMPLETE_DIFFERENT_SOURCE_REST_INSPECTED',json.dumps(rows),flush=True)
