import json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[1];ASSETS=ROOT/'assets-source/aevrynd-character'
BASE=ASSETS/'aevrynd-female-authoring-v249-mainline-runtime-brows-r480.blend';CAND=ASSETS/'aevrynd-female-authoring-v249-mainline-continuous-upper-lip-r484.blend'
BASE_IMG=ASSETS/'reviews/v249r480-runtime-brows/01-face-front-f01.png';CAND_IMG=ASSETS/'reviews/v249r484-continuous-upper-lip/face-front-f01.png';REPORT=ASSETS/'female-v249-mainline-continuous-upper-lip-r484.tone-contract-audit.json';BODY='AevryndFemaleBodyBaseV118';LIGHTS=('Aevrynd Review Face Fill','Aevrynd Review Fill','Aevrynd Review Hair Rim','Aevrynd Review Key','Aevrynd Review Top')
def scalar(v):
 try:return [round(float(x),8) for x in v]
 except TypeError:return round(float(v),8)
def snapshot(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene;body=bpy.data.objects[BODY];mat=body.active_material;shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bg=next((n for n in s.world.node_tree.nodes if n.type=='BACKGROUND'),None)
 return {'file':path.name,'viewTransform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma,'worldStrength':float(bg.inputs['Strength'].default_value),'lights':{n:{'energy':float(bpy.data.objects[n].data.energy),'color':scalar(bpy.data.objects[n].data.color)} for n in LIGHTS},'nonColorShader':{n:scalar(shader.inputs[n].default_value) for n in ('Roughness','Subsurface Weight','Subsurface Scale','Specular IOR Level')},'material':mat.name,'maskMaximum':(max((d.color[0] for d in body.data.color_attributes['AevryndVermilionPlaneR484_c-defined-280'].data),default=0) if body.data.color_attributes.get('AevryndVermilionPlaneR484_c-defined-280') else None)}
def luma(path,rect):
 im=bpy.data.images.load(str(path),check_existing=False);w,h=im.size;pix=im.pixels[:];x0,y0,x1,y1=[int(v*(w if i%2==0 else h)) for i,v in enumerate(rect)];total=0;count=0
 for y in range(y0,y1):
  for x in range(x0,x1):
   j=(y*w+x)*4;total+=.2126*pix[j]+.7152*pix[j+1]+.0722*pix[j+2];count+=1
 bpy.data.images.remove(im);return total/count
base=snapshot(BASE);cand=snapshot(CAND);rects={'leftCheek':(.13,.28,.31,.54),'rightCheek':(.69,.28,.87,.54),'forehead':(.42,.77,.58,.90),'wholeFace':(.08,.02,.92,.92)};regions={};viol=[]
for k in ('viewTransform','look','exposure','gamma','worldStrength','lights','nonColorShader'):
 if base[k]!=cand[k]:viol.append({'type':'lockedToneSettingChanged','field':k,'baseline':base[k],'candidate':cand[k]})
for name,rect in rects.items():
 a=luma(BASE_IMG,rect);b=luma(CAND_IMG,rect);delta=(b-a)*100/a if a else 0;regions[name]={'baseline':a,'candidate':b,'deltaPercent':delta}
 if abs(delta)>1:viol.append({'type':'luminanceDriftOver1Percent','region':name,'deltaPercent':delta})
if not 0.339<cand['maskMaximum']<0.341:viol.append({'type':'unexpectedVermilionMaskMaximum','value':cand['maskMaximum']})
report={'baseline':base,'candidate':cand,'linearLuminanceRegions':regions,'violations':viol,'status':'PASS' if not viol else 'FAIL'};REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8');print('AEVRYND_R484_TONE='+json.dumps({'status':report['status'],'regions':regions,'violations':viol},sort_keys=True))
