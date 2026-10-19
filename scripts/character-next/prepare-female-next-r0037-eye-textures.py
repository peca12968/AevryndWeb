"""CC0 iris structural detail on preserved radial mean, vein-only sclera map.

Do not transfer the donor atlas's baked broad lighting, fake pupil or blue
marker. This is artist texture data, not subject-specific measured albedo.
"""
import numpy as np,json,hashlib
from pathlib import Path
from PIL import Image,ImageFilter
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0037-eye-margin';D=S/'eyes/makehuman-system-cc0';OUT=S/'textures';src=D/'brown_eye.png'
def lin(a):return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
def srgb(a):return np.where(a<=.0031308,12.92*a,1.055*np.maximum(a,0)**(1/2.4)-.055)
def main():
    image=Image.open(src).convert('RGB');a=np.array(image,dtype='f8')/255;old=lin(np.array(Image.open(OUT/'aevrynd-r0030-b-own-iris.png').convert('RGB'),dtype='f8')/255);n=old.shape[0];q=(np.arange(n)+.5)/n*2-1;xx,yy=np.meshgrid(q,q);rr=np.hypot(xx,yy);bucket=np.clip((rr*255).astype('i4'),0,255);base=np.zeros((256,3))
    for k in range(256):
        m=(bucket==k)&(rr<=1.01);base[k]=np.median(old[m],axis=0) if np.any(m) else base[max(0,k-1)]
    rows=[]
    for side,(cx,cy,rad) in [('L',(721,301,121)),('R',(303,730,123))]:
        # Pillow's transform reads the actual atlas rectangle, no new source art.
        crop=image.crop((cx-rad,cy-rad,cx+rad,cy+rad)).resize((n,n),Image.Resampling.LANCZOS);rgb=lin(np.array(crop,dtype='f8')/255);luma=rgb@np.array((.2126,.7152,.0722));radial=np.zeros(256)
        for k in range(256):
            m=(bucket==k)&(rr<=1.01);radial[k]=np.median(luma[m]) if np.any(m) else radial[max(0,k-1)]
        detail=np.clip(luma/np.maximum(radial[bucket],.001),.45,1.85);result=np.clip(base[bucket]*detail[...,None],0,1);path=OUT/f'aevrynd-r0037-{side}-iris-detail.png';Image.fromarray(np.round(np.clip(srgb(result),0,1)*255).astype('u1')).save(path);rows.append({'side':side,'sourceCentrePixel':[cx,cy],'radiusPixels':rad,'output':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    excess=np.maximum(a[:,:,0]-(a[:,:,1]+a[:,:,2])*.5,0);blur=np.array(Image.fromarray(np.uint8(np.clip(excess,0,1)*255)).filter(ImageFilter.GaussianBlur(6)),dtype='f8')/255;vessel=np.clip((excess-blur-.003)/.055,0,1)
    # Atlas's pupil/iris and marker are not scleral vascular information.
    yy0,xx0=np.mgrid[:a.shape[0],:a.shape[1]]
    for cx,cy,rad in [(721,301,130),(303,730,132),(955,955,80)]:vessel[(xx0-cx)**2+(yy0-cy)**2<rad*rad]=0
    vein=OUT/'aevrynd-r0037-sclera-vein-only.png';Image.fromarray(np.round(vessel*255).astype('u1')).save(vein)
    report={'source':str(src),'sourceSha256':hashlib.sha256(src.read_bytes()).hexdigest(),'license':'CC0-1.0','iris':rows,'irisMethod':'Donor nonperiodic local luminance structure normalized by donor annular median, multiplied by exact previous iris texture annular median RGB. Same overall radial brown reflectance; no donor pupil or broad atlas shading. Not measured photometric albedo.','irisDetailClamp':[.45,1.85],'scleraVeinImage':str(vein),'scleraVeinSha256':hashlib.sha256(vein.read_bytes()).hexdigest(),'scleraMethod':'Positive local red-excess residual after6pixel Gaussian low-frequency removal, iris/pupil/marker regions explicitly excluded. No baked gray lighting transferred.','sourceGeometryImported':False};(E/'b-texture-registration.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report))
if __name__=='__main__':main()
