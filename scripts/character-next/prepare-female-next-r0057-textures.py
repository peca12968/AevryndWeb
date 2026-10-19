"""Bounded sequential texture derivatives through installed Blender only."""
from pathlib import Path
import bpy,json,hashlib,time,numpy as np,shutil
R=Path(r'D:\Download\Aevrynd');D=R/'Reference/character/charmorph-vitruvian-cc0';O=R/'engine/assets/characters/female-next/source/study-vitruvian-textures';O.mkdir(parents=True,exist_ok=True)
E=R/'Evidence/character-female-next/r0057-coherent-foundation';E.mkdir(parents=True,exist_ok=True)
provenance=json.loads((D/'r0057-texture-provenance.json').read_text());rows=[];tick=time.time()
if (E/'texture-derivatives.json').exists() and not (E/'texture-derivatives-first-32bit.json').exists():shutil.copy2(E/'texture-derivatives.json',E/'texture-derivatives-first-32bit.json')
scene=bpy.context.scene;scene.render.image_settings.file_format='OPEN_EXR';scene.render.image_settings.color_depth='16';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.exr_codec='ZIP'
scene.view_settings.view_transform='Raw';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
for row in provenance['files']:
    p=D/'textures-4k'/row['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
    image=bpy.data.images.load(str(p),check_existing=False);sourceSize=list(image.size);size=2048 if row['file'].startswith('Light_Skin_Color') else 1024
    image.scale(size,size);sample=np.array(image.pixels[:],dtype='f4').reshape(-1,4)[::1024].copy();out=O/p.name;image.save_render(str(out),scene=scene)
    check=bpy.data.images.load(str(out),check_existing=False);actual=np.array(check.pixels[:],dtype='f4').reshape(-1,4)[::1024]
    error=float(np.abs(actual-sample).max());bound=np.abs(np.spacing(sample.astype('f2')).astype('f4'))*.501+1e-7
    assert actual.shape==sample.shape and np.all(np.abs(actual-sample)<=bound),('Linear sample transfer exceeds half-float rounding',out.name,error)
    bpy.data.images.remove(check)
    rows.append({'file':out.name,'sourceSHA256':row['sha256'],'sourceSize':sourceSize,'size':[size,size],'colorSpace':image.colorspace_settings.name,'precision':'half16','codec':'ZIP','sampledLinearTransferMaximumError':error,'sampleCount':len(sample),'bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
    bpy.data.images.remove(image);print('R57_TEXTURE_DERIVATIVE',out.name,size,flush=True)
(E/'texture-derivatives.json').write_text(json.dumps({'source':str(D/'r0057-texture-provenance.json'),'directory':str(O),'files':rows,'scope':'Sequential resolution reduction only, OpenEXR linear data retained. No generated painting or exposure/darkening operation.','seconds':time.time()-tick},indent=2)+'\n',encoding='utf8')
print('R57_DERIVATIVES_READY',sum(r['bytes'] for r in rows),time.time()-tick,flush=True)
