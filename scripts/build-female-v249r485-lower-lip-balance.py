import json,math
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];ASSETS=ROOT/'assets-source/aevrynd-character';SOURCE=ASSETS/'aevrynd-female-authoring-v249-mainline-continuous-upper-lip-r484.blend';OUTPUT=ASSETS/'aevrynd-female-authoring-v249-mainline-balanced-lower-lip-r485.blend';REPORT=ASSETS/'female-v249-mainline-balanced-lower-lip-r485.build-report.json';OUT=ASSETS/'reviews/v249r485-balanced-lower-lip';BODY='AevryndFemaleBodyBaseV118'
def clamp(v):return max(0,min(1,v))
def smoothstep(v):v=clamp(v);return v*v*(3-2*v)
def gauss(v,c,s):return math.exp(-.5*((v-c)/s)**2)
def delta(p):
 ax=abs(p.x)
 if ax>.052 or p.y>-.106 or not 1.498<p.z<1.534:return Vector()
 width=1-smoothstep((ax-.031)/.019);front=1-smoothstep((p.y+.123)/.022)
 if width<=0 or front<=0:return Vector()
 bulb=gauss(p.z,1.516,.0075)*width*front
 lower_edge=gauss(p.z,1.507,.0048)*width*front
 inner_upper=gauss(p.z,1.5300,.00115)*width*front
 tubercle=gauss(p.x,0,.0060);peaks=gauss(ax,.0105,.0048)
 inner_lower=gauss(p.z,1.5273,.0013)*width*front
 return Vector((0, +.00072*bulb, +.00042*lower_edge + (-.00034*tubercle+.00016*peaks)*inner_upper + .00012*tubercle*inner_lower))
def look(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
def render(s,cam,frame,label,loc,target,lens,size):s.frame_set(frame);bpy.context.view_layer.update();cam.location=loc;cam.data.lens=lens;look(cam,target);s.render.resolution_x,s.render.resolution_y=size;s.render.filepath=str(OUT/f'{label}.png');bpy.ops.render.render(write_still=True)
def variant(label,strength):
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();body=bpy.data.objects[BODY];dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);mesh=ev.to_mesh();pts=[ev.matrix_world@v.co for v in mesh.vertices];ev.to_mesh_clear();inv=body.matrix_world.inverted().to_3x3();ds={i:delta(p)*strength for i,p in enumerate(pts)};ds={i:d for i,d in ds.items() if d.length>1e-6}
 for key in body.data.shape_keys.key_blocks:
  for i,d in ds.items():key.data[i].co+=inv@d
 body.data.update();s.render.engine='BLENDER_EEVEE';s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';cam=bpy.data.objects.get('Aevrynd R249 Review Camera') or bpy.data.objects['Aevrynd Review Camera'];s.camera=cam
 views=[('mouth',(0,-.405,1.528),(0,-.115,1.528),135,(1400,800)),('oblique',(.235,-.405,1.53),(0,-.112,1.528),135,(1400,800)),('face',(0,-.56,1.585),(0,-.06,1.585),108,(1100,1100)),('three-quarter',(.40,-.57,1.58),(0,-.03,1.56),92,(1000,1000))]
 for n,loc,target,lens,size in views:render(s,cam,1,f'{n}-f01',loc,target,lens,size)
 for n,loc,target,lens,size in (views[1],views[2]):render(s,cam,20,f'{n}-f20',loc,target,lens,size)
 s.frame_set(1);s['aevrynd_revision']='v249r485-balanced-lower-lip';s['aevrynd_parent']=SOURCE.name;s['aevrynd_release_state']='TECHNICAL_CANDIDATE_AUDITS_PENDING';body['aevrynd_lower_lip_method']='continuous volume reduction and central seam curvature';bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
 return {'strength':strength,'verticesMoved':len(ds),'maximumMoveMm':max((d.length for d in ds.values()),default=0)*1000}
OUT.mkdir(parents=True,exist_ok=True);result=variant('selected',1.3);report={'revision':'v249r485','source':str(SOURCE),'output':str(OUTPUT),'method':'continuous lower-lip volume reduction and central mouth-seam curvature','result':result,'bodyTopologyChanged':False,'shapeKeysMovedTogether':6,'runtimeDependencyAdded':False,'status':'TECHNICAL_CANDIDATE_AUDITS_PENDING','reviewDirectory':str(OUT)};REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8');print('AEVRYND_R485_LOWER_LIP='+json.dumps(report,sort_keys=True))
