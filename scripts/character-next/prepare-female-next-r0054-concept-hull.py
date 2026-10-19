"""Analyze an explicitly labelled authored concept into a design visual hull.

This constructs numerical modelling constraints, not edited proof images or a
reconstruction claim about a real person. No additional packages are installed.
"""
from pathlib import Path
import numpy as np,json,sys,time
from PIL import Image
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0054-clump-volume'
STEP=.0012
CLEAN='--clean-masks' in sys.argv;TAG='clean-' if CLEAN else ''

def write(name,data):(E/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def large_hair_components(mask):
    h,w=mask.shape;visited=np.zeros_like(mask);result=np.zeros_like(mask)
    for y,x in zip(*np.nonzero(mask)):
        if visited[y,x]:continue
        stack=[(int(y),int(x))];visited[y,x]=True;component=[];top=h
        while stack:
            a,b=stack.pop();component.append((a,b));top=min(top,a)
            for c,d in ((a-1,b),(a+1,b),(a,b-1),(a,b+1)):
                if 0<=c<h and 0<=d<w and mask[c,d] and not visited[c,d]:visited[c,d]=True;stack.append((c,d))
        if len(component)>=1500 and top<350:
            a,b=np.array(component,dtype='i4').T;result[a,b]=True
    return result

def masks():
    image=np.array(Image.open(E/'design-concept-reference-only.png').convert('RGB'));assert image.shape[:2]==(1024,1536)
    output=[];ranges=[]
    for ci in range(3):
        p=image[:,512*ci:512*(ci+1)].astype('i2')
        mask=(p[:,:,0]<185)&(p[:,:,1]<155)&(p[:,:,2]<140)&(p[:,:,0]>p[:,:,1]+6)
        mask[:115]=False;mask[680:]=False
        mask=large_hair_components(mask)
        if CLEAN:
            # Coarse modelling silhouette, not the individual light/dark
            # strand pixels. Close sub3mm texture slits, then fill enclosed
            # holes while leaving the face opening connected to background.
            def dilate(m):
                out=m.copy()
                out[1:]|=m[:-1];out[:-1]|=m[1:];out[:,1:]|=m[:,:-1];out[:,:-1]|=m[:,1:]
                return out
            def erode(m):
                out=m.copy()
                out[1:]&=m[:-1];out[:-1]&=m[1:];out[:,1:]&=m[:,:-1];out[:,:-1]&=m[:,1:]
                out[[0,-1]]=False;out[:,[0,-1]]=False;return out
            for _ in range(6):mask=dilate(mask)
            for _ in range(6):mask=erode(mask)
            h,w=mask.shape;outside=np.zeros_like(mask);stack=[(0,0)];outside[0,0]=True
            while stack:
                a,b=stack.pop()
                for c,d in ((a-1,b),(a+1,b),(a,b-1),(a,b+1)):
                    if 0<=c<h and 0<=d<w and not mask[c,d] and not outside[c,d]:outside[c,d]=True;stack.append((c,d))
            mask=~outside
        output.append(mask)
        lo=np.full(1024,512,dtype='i4');hi=np.full(1024,-1,dtype='i4')
        for y in range(115,680):
            xs=np.flatnonzero(mask[y])
            if len(xs)>5:
                lo[y]=int(np.quantile(xs,.02)) if CLEAN else int(xs[0]);hi[y]=int(np.quantile(xs,.98)) if CLEAN else int(xs[-1])
        if CLEAN:
            for bounds in (lo,hi):
                original=bounds.copy()
                for row in range(120,675):
                    values=original[max(115,row-4):min(680,row+5)]
                    valid=values[(values>=0)&(values<512)]
                    if len(valid):bounds[row]=int(np.median(valid))
        ranges.append((lo,hi))
    x=np.arange(-.115,.115+STEP/2,STEP);y=np.arange(-.16,.10+STEP/2,STEP);z=np.arange(1.335,1.590+STEP/2,STEP)
    v=np.clip(np.rint(125+(1.576-z)/.00042).astype('i4'),0,1023)
    uf=np.clip(np.rint(256+x/.000405).astype('i4'),0,511)
    ub=np.clip(np.rint(256-x/.000405).astype('i4'),0,511)
    us=np.clip(np.rint((y+.145)/.00043).astype('i4'),0,511)
    F=output[0][v[None,:],uf[:,None]];B=output[2][v[None,:],ub[:,None]];P=output[1][v[None,:],us[:,None]]
    outer=[]
    for ci,u in [(0,uf),(2,ub),(1,us)]:
        lo,hi=ranges[ci];outer.append((u[:,None]>=lo[v][None,:])&(u[:,None]<=hi[v][None,:]))
    np.savez_compressed(E/(TAG+'concept-hull-masks.npz'),x=x,y=y,z=z,hairFront=F,hairBack=B,hairProfile=P,
        outerFront=outer[0],outerBack=outer[1],outerProfile=outer[2])
    write(TAG+'concept-hull-design.json',{'source':'design-concept-reference-only.png','sourceType':'AI-authored concept, not scan or model result','coarseSilhouetteCleanup':CLEAN,
        'coordinateDesign':{'gridStepM':STEP,'frontXPerPixelM':.000405,'profileYPerPixelM':.00043,'zPerPixelM':.00042,
            'crownDesignZAtRow125M':1.576,'profileYAtColumn0M':-.145},
        'gridShape':[len(x),len(y),len(z)],'maskPixels':[int(m.sum()) for m in output],
        'scope':'Authored silhouette normalization to the existing head; not measured photo/head identity alignment.',
        'method':'Three concept silhouettes plus hair/skin visibility masks, actual body depth intervals, conservative inner cavity; mesh design proxy only.'})
    print('R54_CONCEPT_MASKS',len(x),len(y),len(z),[int(m.sum()) for m in output],flush=True)

def mesh():
    tick=time.time();a=np.load(E/(TAG+'concept-hull-masks.npz'));d=np.load(E/'concept-hull-body-depths.npz')
    x,y,z=a['x'],a['y'],a['z'];FY,BY=d['frontY'],d['backY'];LX,RX=d['leftX'],d['rightX']
    X=x[:,None,None];Y=y[None,:,None]
    occupied=a['outerFront'][:,None,:]&a['outerBack'][:,None,:]&a['outerProfile'][None,:,:]
    occupied&=(a['hairFront'][:,None,:]|(Y>FY[:,None,:]+.0005))
    occupied&=(a['hairBack'][:,None,:]|(Y<BY[:,None,:]-.0005))
    occupied&=(a['hairProfile'][None,:,:]|((X>LX[None,:,:]+.0005)&(X<RX[None,:,:]-.0005)))
    cavity=(Y>FY[:,None,:]-.0006)&(Y<BY[:,None,:]+.0006)
    occupied&=~cavity
    assert 20000<int(occupied.sum())<2000000,('Unexpected volume size',int(occupied.sum()))
    faces=[]
    offsets=[
        [(1,0,0),(1,1,0),(1,1,1),(1,0,1)],[(0,0,0),(0,0,1),(0,1,1),(0,1,0)],
        [(0,1,0),(0,1,1),(1,1,1),(1,1,0)],[(0,0,0),(1,0,0),(1,0,1),(0,0,1)],
        [(0,0,1),(1,0,1),(1,1,1),(0,1,1)],[(0,0,0),(0,1,0),(1,1,0),(1,0,0)]]
    for axis in range(3):
        for direction in (1,-1):
            neighbor=np.zeros_like(occupied);target=[slice(None)]*3;source=[slice(None)]*3
            target[axis]=slice(None,-1) if direction==1 else slice(1,None)
            source[axis]=slice(1,None) if direction==1 else slice(None,-1)
            neighbor[tuple(target)]=occupied[tuple(source)]
            indices=np.argwhere(occupied&~neighbor)
            faces.append(indices[:,None,:]+np.array(offsets[axis*2+(0 if direction==1 else 1)])[None])
    corners=np.concatenate(faces).astype('i4');vertices,index=np.unique(corners.reshape(-1,3),axis=0,return_inverse=True)
    origin=np.array((x[0],y[0],z[0]))-STEP/2
    points=origin+vertices*STEP;quads=index.reshape(-1,4).astype('i4')
    np.savez_compressed(E/(TAG+'concept-hull-mesh.npz'),vertices=points.astype('f4'),quads=quads,occupied=occupied)
    write(TAG+'concept-hull-construction.json',{'occupiedVoxels':int(occupied.sum()),'vertices':len(points),'quads':len(quads),
        'gridStepM':STEP,'boundsM':[points.min(0).tolist(),points.max(0).tolist()],
        'bodyCavity':'Conservative front/back depth interval, not signed-distance or collision proof. Occlusion-aware front/back/profile hair masks retain hidden rear hair.',
        'scope':'Numerical concept visual-hull design proxy. Actual body unchanged; no physical hair or contact acceptance.',
        'seconds':time.time()-tick})
    print('R54_CONCEPT_HULL',occupied.sum(),len(points),len(quads),time.time()-tick,flush=True)

if __name__=='__main__':mesh() if '--mesh' in sys.argv else masks()
