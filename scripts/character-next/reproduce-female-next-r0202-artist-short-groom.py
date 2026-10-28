"""Original CC0 short style full-look reproduction, not a woman candidate."""
from pathlib import Path
import bpy,numpy as np,json,datetime,hashlib,importlib.util
from mathutils import Vector
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0202-independent-complete-groom';ART=Path('C:/Users/USER/AppData/Local/Temp/Aevrynd-hair-editor-reference/hair.blend')
sp=importlib.util.spec_from_file_location('r202refbase',C/'scripts/character-next/build-female-next-r0169-coherent-native-carrier.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
bpy.ops.wm.open_mainfile(filepath=str(ART));s=bpy.context.scene;hair=bpy.data.objects['basic_short_hair'];body=hair.data.surface
def layer(l):
 l.exclude=False;l.hide_viewport=False
 for c in l.children:layer(c)
layer(bpy.context.view_layer.layer_collection)
for o in bpy.data.objects:o.hide_render=o not in [hair,body];o.hide_set(o not in [hair,body])
for c in bpy.data.collections:c.hide_render=False;c.hide_viewport=False
for md in hair.modifiers:md.show_viewport=md.show_render
bpy.context.view_layer.update();raw=h.arr(hair.data.position_data,'vector',len(hair.data.position_data),3);rawWorld=np.array([hair.matrix_world@Vector(x) for x in raw]);rawOffsets=np.array([x.first_point_index for x in hair.data.curves],'i4');V,T=a.geometry(body);P,off=m.curveworld(hair);d=hair.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
assert len(P)<2000000
np.savez_compressed(E/'original-short-style-data.npz',rawWorld=rawWorld.astype('f4'),rawOffsets=rawOffsets,bodyWorld=V.astype('f4'),bodyTriangles=T,evaluatedRoots=P[off].astype('f4'),evaluatedOffsets=off)
camera=bpy.data.objects.new('AFN202_REFERENCE_CAMERA',bpy.data.cameras.new('AFN202_REFERENCE_CAMERA'));s.collection.objects.link(camera);s.camera=camera;camera.data.lens=65
target=Vector((0,-.04,1.55));camera.location=(0,-1.15,1.58);camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
for n,power,size,loc in [('Key',180,1.0,(-.5,-.6,2.1)),('Fill',100,1.0,(.6,-.5,1.7)),('Rim',140,.7,(.2,.5,2.0))]:
 ob=bpy.data.objects.new('AFN202_REFERENCE_'+n,bpy.data.lights.new('AFN202_REFERENCE_'+n,'AREA'));s.collection.objects.link(ob);ob.data.energy=power;ob.data.shape='DISK';ob.data.size=size;ob.location=loc;ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=16;s.cycles.seed=61061;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=-.5;s.world.color=(.04,.04,.04);s.render.film_transparent=False;s.render.hair_type='STRAND';s.render.hair_subdiv=3
captures=[]
def record(scene):captures.append({'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(ART),'style':hair.name,'surface':body.name,'actualCurves':len(off),'actualPoints':len(P),'output':scene.render.filepath,'camera':[list(x) for x in camera.matrix_world],'scope':'Original source reference only, not a new current-woman result.'})
bpy.app.handlers.render_pre.append(record)
for label,loc in [('front',(0,-1.15,1.58)),('side',(.95,-.04,1.58))]:
 camera.location=loc;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(E/('original-cc0-short-reference-'+label+'.png'));bpy.ops.render.render(write_still=True)
q={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':str(ART),'sourceSHA256':hashlib.file_digest(ART.open('rb'),'sha256').hexdigest(),'style':hair.name,'surface':body.name,'rawGuides':len(rawOffsets),'rawPoints':len(raw),'evaluatedCurves':len(off),'evaluatedPoints':len(P),'rawGuideRootBounds':np.stack([rawWorld[rawOffsets].min(0),rawWorld[rawOffsets].max(0)]).tolist(),'sourceBodyBounds':np.stack([V.min(0),V.max(0)]).tolist(),'effectiveMaterials':[x.name for x in d.materials],'modifiers':[{'name':x.name,'type':x.type,'viewport':x.show_viewport,'render':x.show_render} for x in hair.modifiers],'captures':captures,'originalSourceNotSaved':True,'currentWomanNotReplaced':True,'embeddedCodeNotExecuted':True}
(E/'original-short-style-reproduction.json').write_bytes((json.dumps(q,indent=2)+'\n').encode());print('R202_ORIGINAL_SHORT_FULL_STYLE_REPRODUCED',flush=True)
