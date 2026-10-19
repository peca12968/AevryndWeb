"""Recover bounded local stroke orientation from the selected CC0 artist image.

This infers a usable groom field, not unique historical follicles or 3D capture.
No photographic face pigment is transferred. Source pixels remain attributable.
"""
import numpy as np,json,hashlib,math
from pathlib import Path
from PIL import Image
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0036-data-informed-brows';S=R/'engine/assets/characters/female-next/source'
TEX=S/'brows/makehuman-system-cc0/eyebrow001.png'
def blur(a,r=4):
    k=np.exp(-np.arange(-r,r+1)**2/(2*(r/2)**2));k/=k.sum();x=np.pad(a,((0,0),(r,r)),mode='edge');x=sum(w*x[:,j:j+a.shape[1]] for j,w in enumerate(k));y=np.pad(x,((r,r),(0,0)),mode='edge');return sum(w*y[j:j+a.shape[0]] for j,w in enumerate(k))
def sample(a,x,y):
    x=float(np.clip(x,0,510.999));y=float(np.clip(y,0,510.999));ix,iy=int(x),int(y);u,w=x-ix,y-iy
    return (1-w)*((1-u)*a[iy,ix]+u*a[iy,ix+1])+w*((1-u)*a[iy+1,ix]+u*a[iy+1,ix+1])
def halton(i,base):
    x=0.;f=1.
    while i:f/=base;x+=f*(i%base);i//=base
    return x
def main():
    img=np.array(Image.open(TEX),dtype='f8')/255;alpha=img[:,:,3];lum=img[:,:,:3]@np.array((.2126,.7152,.0722));signal=alpha*(.4+lum)
    gy,gx=np.gradient(signal);xx=blur(gx*gx);yy=blur(gy*gy);xy=blur(gx*gy);angle=.5*np.arctan2(2*xy,xx-yy)+math.pi/2
    fx=np.cos(angle);fy=np.sin(angle);flip=fx<0;fx[flip]*=-1;fy[flip]*=-1
    # Orientation is unsigned in image evidence. Choose outward (+image x).
    # Authorial medial growth/arch direction fixes the sign only where needed.
    coherence=np.sqrt((xx-yy)**2+4*xy*xy)/np.maximum(xx+yy,1e-10)
    P=[];colors=[];rr=[];root=[];attempts=0;reject={};overlay=Image.open(TEX).convert('RGBA');from PIL import ImageDraw;draw=ImageDraw.Draw(overlay)
    for i in range(1,16001):
        attempts=i;x=16+halton(i,2)*465;y=155+halton(i,3)*105;a=float(sample(alpha,x,y));gate=halton(i,5)
        if a<.12 or gate>a*.70:continue
        # Exact image-root spacing, before committing any 3D follicles.
        if root and np.min(np.linalg.norm(np.array(root)-[x,y],axis=1))<1.7:continue
        points=[[x,y]];length=25+halton(i,7)*37;direction=None
        for j in range(int(length/.70)):
            x,y=points[-1];d=np.array((sample(fx,x,y),sample(fy,x,y)));d/=max(np.linalg.norm(d),1e-12)
            if direction is not None:
                if d@direction<0:d=-d
                d=.70*direction+.30*d;d/=np.linalg.norm(d)
            if d[0]<.12:d[0]=.12;d/=np.linalg.norm(d)
            nxt=np.array((x,y))+.70*d
            if not (10<nxt[0]<485 and 147<nxt[1]<265) or float(sample(alpha,*nxt))<.018:break
            points.append(nxt.tolist());direction=d
        p=np.array(points);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
        if arc[-1]<13:reject['short_image_streamline']=reject.get('short_image_streamline',0)+1;continue
        p=np.column_stack([np.interp(np.linspace(0,arc[-1],24),arc,p[:,k]) for k in range(2)]);P.append(p);root.append(p[0].tolist())
        rgb=np.array(sample(img[:,:,:3],*p[len(p)//2]));colors.append(np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4))
        radius=(23+halton(i,11)*5)*1e-6;rr.append(2.0e-6+(radius-2e-6)*(1-np.linspace(0,1,24))**.6)
        draw.line([tuple(v) for v in p],fill=(30,210,245,220),width=1)
        if len(P)==450:break
    assert len(P)==450,len(P)
    path=S/'aevrynd-female-next-r0036-image-flow.npz';np.savez_compressed(path,pixelPaths=np.array(P,dtype='f4'),radii=np.array(rr,dtype='f4'),linearColors=np.array(colors,dtype='f4'),flowX=fx.astype('f4'),flowY=fy.astype('f4'),coherence=coherence.astype('f4'))
    overlay.save(E/'cc0-stroke-flow-inspection.png');meta={'source':str(TEX),'sourceSha256':hashlib.sha256(TEX.read_bytes()).hexdigest(),'cache':str(path),'cacheSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'pathsPerSide':len(P),'stations':24,'attempts':attempts,'rejectedBefore3DFollicleCommitment':reject,'method':'Artist alpha-weighted low-discrepancy roots and locally filtered structure-tensor tangent streamlines, outward sign resolved by source layout; bounded source-alpha truncation. No original 3D root identities claimed.','radiusRangeM':[float(np.min(rr)),float(np.max(rr))],'scope':'2D authored image silhouette/local direction inference only. No 3D/contact/runtime pass.'}
    (E/'image-flow-inspection.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8');print(json.dumps(meta))
if __name__=='__main__':main()
