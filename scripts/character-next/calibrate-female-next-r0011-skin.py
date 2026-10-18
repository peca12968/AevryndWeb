"""Calibrate only texture reflectance to the existing clay's six skin reference points."""
import json,hashlib,statistics
from pathlib import Path
from PIL import Image
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0011-skin-brows'
inspection=json.loads((E/'uv-and-skin-inspection.json').read_text());path=R/'engine/assets/characters/female-next/source/textures/makehuman-system-cc0/young_lightskinned_female_diffuse3.png';im=Image.open(path).convert('RGB')
def linear(v):
    v=v/255.;return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
samples=[]
for record in inspection['referenceSkinSamples']:
    u,v=record['uv'];x=min(im.width-1,max(0,int(u*im.width)));y=min(im.height-1,max(0,int((1-v)*im.height)))
    points=[im.getpixel((min(im.width-1,max(0,x+dx)),min(im.height-1,max(0,y+dy)))) for dx in range(-3,4) for dy in range(-3,4)]
    samples.append({**record,'pixel':[x,y],'linearRGB':[statistics.median(linear(p[c]) for p in points) for c in range(3)]})
mean=[statistics.mean(p['linearRGB'][c] for p in samples) for c in range(3)];target=[.32,.23,.18];gain=[target[c]/mean[c] for c in range(3)]
assert all(.25<g<2 for g in gain),gain
result={'source':str(path),'sourceSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'textureSize':list(im.size),'sampledSkinRGBLinear':mean,'targetRGBLinear':target,'perChannelReflectanceGain':gain,'samples':samples,'purpose':'Keep six reference skin sites at the prior average linear albedo while adding mapped anatomical pigment. This is explicit albedo colour calibration, not a lighting/exposure edit or a claim of measured human skin reflectance.'}
(E/'skin-albedo-calibration.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'linearSourceMean':mean,'gain':gain,'target':target}))
