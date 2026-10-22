"""Inspect licensed artist groom on its ORIGINAL source head; not a woman candidate."""
from pathlib import Path
import bpy,json,numpy as np,datetime,time
from mathutils import Vector
P=Path('C:/Users/USER/AppData/Local/Temp/Aevrynd-hair-editor-reference');E=Path('D:/Download/Aevrynd/Evidence/character-female-next/support-r0152-render-representation')
bpy.ops.wm.open_mainfile(filepath=str(P/'hair.blend'));s=bpy.context.scene
hair=bpy.data.objects['straight_hair_to_shoulder']
for o in bpy.data.objects:
 if o.type=='CURVES':o.hide_render=o!=hair;o.hide_set(o!=hair)
 if o.type=='LIGHT':o.hide_render=True
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=16;s.cycles.use_denoising=True;s.cycles.seed=61061;s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=s.render.resolution_y=512;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.hair_type='STRIP';s.render.hair_subdiv=3;s.world.color=(.025,.025,.025);s.view_settings.exposure=-.5
target=Vector((0,0,1.48))
for name,loc,power,size in [('reference-key',(-.5,-.6,2.0),100,0.6),('reference-fill',(.5,-.3,1.7),55,0.5),('reference-back',(0,.5,1.9),80,.5)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects['Camera'];s.camera=cam;cam.data.lens=60
bpy.context.view_layer.update();evalHair=hair.evaluated_get(bpy.context.evaluated_depsgraph_get());d=evalHair.data
counts={'rawGuides':len(hair.data.curves),'rawPoints':len(hair.data.points),'evaluatedCurves':len(d.curves),'evaluatedPoints':len(d.points),'surface':hair.data.surface.name if hair.data.surface else None,'UV':hair.data.surface_uv_map,'nodeModifiers':[m.node_group.name for m in hair.modifiers if m.type=='NODES']}
rows=[]
for view,loc in [('face',(0,-.85,1.49)),('back',(0,.85,1.49))]:
 cam.location=loc;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.view_layer.update();s.render.filepath=str(E/('cc0-original-artist-groom-'+view+'.png'));bpy.ops.render.render(write_still=True);rows.append({'view':view,'file':s.render.filepath})
(E/'new-cc0-original-source-reference-preview.json').write_bytes((json.dumps({'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'counts':counts,'images':rows,'purpose':'Inspect original source rest form and scalp layout before transfer decisions. Different original woman/reference stage, not an Aevrynd candidate or matched gain.','noSourceFileWritten':True,'noInstall':True,'adopted':False},indent=2)+'\n').encode());print('NEW_CC0_ORIGINAL_GROOM_REFERENCE_PREVIEW_DONE',flush=True)
