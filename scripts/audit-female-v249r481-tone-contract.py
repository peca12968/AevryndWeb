import json, math
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];ASSETS=ROOT/'assets-source/aevrynd-character';BASE=ASSETS/'aevrynd-female-authoring-v249-mainline-runtime-brows-r480.blend';CAND=ASSETS/'aevrynd-female-authoring-v249-mainline-smoothed-lip-margin-r481.blend';BASE_IMG=ASSETS/'reviews/v249r480-runtime-brows/01-face-front-f01.png';CAND_IMG=ASSETS/'reviews/v249r481-smoothed-lip-margin/01-face-front-f01.png';REPORT=ASSETS/'female-v249-mainline-smoothed-lip-margin-r481.tone-contract-audit.json';BODY='AevryndFemaleBodyBaseV118';LIGHTS=('Aevrynd Review Face Fill','Aevrynd Review Fill','Aevrynd Review Hair Rim','Aevrynd Review Key','Aevrynd Review Top')
def scalar(v):
 try:return [round(float(x),8) for x in v]
 except TypeError:
  try:return round(float(v),8)
  except Exception:return str(v)
def snapshot(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene;body=bpy.data.objects[BODY];mat=body.data.materials[0];shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bg=next((n for n in s.world.node_tree.nodes if n.type=='BACKGROUND'),None) if s.world and s.world.use_nodes else None
 inputs={n:{'value':scalar(shader.inputs[n].default_value),'linkedFrom':[f'{l.from_node.name}.{l.from_socket.name}' for l in shader.inputs[n].links]} for n in ('Base Color','Roughness','Subsurface Weight','Subsurface Scale','Specular IOR Level') if shader.inputs.get(n)}
 lights={n:{'energy':round(float(bpy.data.objects[n].data.energy),6),'color':scalar(bpy.data.objects[n].data.color)} for n in LIGHTS}
 return {'file':path.name,'bodyVisible':not body.hide_render,'bodyMaterial':mat.name,'shaderInputs':inputs,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'worldStrength':float(bg.inputs['Strength'].default_value) if bg else None,'lights':lights}
def luma(path,rect):
 im=bpy.data.images.load(str(path),check_existing=False);w,h=im.size;pix=im.pixels[:];x0,y0,x1,y1=[int(v*(w if i%2==0 else h)) for i,v in enumerate(rect)];total=0;count=0
 for y in range(y0,y1):
  for x in range(x0,x1):
   j=(y*w+x)*4;r,g,b=pix[j],pix[j+1],pix[j+2];total+=.2126*r+.7152*g+.0722*b;count+=1
 bpy.data.images.remove(im);return total/count
base=snapshot(BASE);cand=snapshot(CAND);rects={'leftCheek':[.13,.28,.31,.54],'rightCheek':[.69,.28,.87,.54],'centralLowerFace':[.38,.10,.62,.30]};lum={}
for name,rect in rects.items():
 a=luma(BASE_IMG,rect);b=luma(CAND_IMG,rect);lum[name]={'baseline':a,'candidate':b,'deltaPercent':(b-a)*100/a if a else 0}
viol=[]
for key in ('bodyVisible','bodyMaterial','shaderInputs','viewTransform','look','exposure','gamma','worldStrength','lights'):
 if base[key]!=cand[key]:viol.append({'type':'tone_contract_changed','field':key,'baseline':base[key],'candidate':cand[key]})
for name,v in lum.items():
 if abs(v['deltaPercent'])>1:viol.append({'type':'skin_luminance_drift_over_1pct','region':name,'deltaPercent':v['deltaPercent']})
report={'baseline':base,'candidate':cand,'linearLuminanceRegions':lum,'violations':viol,'status':'PASS' if not viol else 'FAIL'};REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8');print('AEVRYND_R481_TONE_CONTRACT='+json.dumps({'status':report['status'],'luminance':lum,'violations':viol},sort_keys=True))

