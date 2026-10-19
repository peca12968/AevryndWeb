"""Actual neutral aperture and native inner-wall topology, no saved mutation."""
import bpy,importlib.util,json,time
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
spec=importlib.util.spec_from_file_location('v34',Path(__file__).with_name('verify-female-next-r0034-locks.py'));v34=importlib.util.module_from_spec(spec);spec.loader.exec_module(v34)
g=v34.g;b=g.b;S=b.S;E=b.R/'Evidence/character-female-next/r0035-neutral-lid-rest';E.mkdir(parents=True,exist_ok=True)
SRC=S/'aevrynd-female-next-r0034-p-physical-width-baseline.blend'
FITS=json.loads((b.R/'Evidence/character-female-next/r0030-eye-optics/existing-eye-inspection.json').read_text())['eyes']

def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def tree(v,t):return BVHTree.FromPolygons(v.tolist(),t.tolist(),all_triangles=True,epsilon=0.)
def outer(side):
    values=[];triangles=[];offset=0
    for part in ('Sclera','Cornea'):
        v,t=b.evaluated(bpy.data.objects[f'AFN30_{side}_{part}'],True);values.append(v);triangles.append(t+offset);offset+=len(v)
    return np.vstack(values),np.vstack(triangles)

def aperture(bt,et,center,xoffsets=None):
    rows=[]
    for dx in (np.linspace(-.010,.010,21) if xoffsets is None else xoffsets):
        x=center[0]+dx
        def state(z):
            origin=Vector((x,-.25,z));eh=et.ray_cast(origin,Vector((0,1,0)),.3);bh=bt.ray_cast(origin,Vector((0,1,0)),.3)
            return eh[0] is not None and (bh[0] is None or eh[3]+1e-7<bh[3]),bh,eh
        zs=np.linspace(center[2]-.012,center[2]+.012,193);visible=[state(float(z))[0] for z in zs];ids=np.flatnonzero(visible)
        if len(ids)==0:rows.append({'dx':float(dx),'visible':False});continue
        runs=int(np.sum(np.diff(np.r_[False,visible,False].astype('i4'))==1))
        # First/last visible interval; retain multi-run diagnostic, don't silently
        # call a fragmented aperture valid.
        def transition(lo,hi,top):
            for _ in range(14):
                z=(lo+hi)*.5;seen,*_=state(z)
                if seen==top:lo=z
                else:hi=z
            return (lo+hi)*.5
        lower=transition(float(zs[max(0,ids[0]-1)]),float(zs[ids[0]]),False)
        upper=transition(float(zs[ids[-1]]),float(zs[min(len(zs)-1,ids[-1]+1)]),True)
        seen,bh,eh=state(upper+2e-6)
        rows.append({'dx':float(dx),'x':float(x),'visible':True,'visibleSampleRuns':runs,'lowerZ':lower,'upperZ':upper,'upperAboveEyeCenterM':upper-center[2],'apertureHeightM':upper-lower,'upperOccludingBodyPoint':list(bh[0]) if bh[0] else None,'upperBodyTriangle':bh[2],'topEyeExteriorPoint':list(eh[0]) if eh[0] else None})
    return rows

def closeup(label):
    s=bpy.context.scene;c=s.camera;state=(c.location.copy(),c.rotation_euler.copy(),c.data.lens,s.render.resolution_x,s.render.resolution_y)
    c.location=(0,-.45,1.461);c.rotation_euler=(Vector((0,-.1125,1.45949))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100;s.render.resolution_x=1400;s.render.resolution_y=650;s.render.filepath=str(E/f'{label}-eyes.png');bpy.ops.render.render(write_still=True)
    c.location,c.rotation_euler,c.data.lens,s.render.resolution_x,s.render.resolution_y=state;bpy.context.view_layer.update()

def main():
    start=time.time();assert b.sha(SRC)=='9f2502d4833088cf0dd625201b6e4f2727dfcf632de62f2b5dadb61ce21e6903';bpy.ops.wm.open_mainfile(filepath=str(SRC));body=bpy.data.objects[b.BODY];mod=body.modifiers[0];hv,ht=b.evaluated(body,True);bt=tree(hv,ht);eyes={side:outer(side) for side in ('L','R')};scans={side:aperture(bt,tree(*eyes[side]),np.array(FITS[side]['centerM'])) for side in eyes}
    mod.levels=0;bpy.context.view_layer.update();V,T=b.evaluated(body,True);body.data.calc_loop_triangles();polys=[list(p.vertices) for p in body.data.polygons];native_tri=np.array([list(t.vertices) for t in body.data.loop_triangles]);polyids=np.array([t.polygon_index for t in body.data.loop_triangles]);ct=tree(V,T);edges={}
    for pi,ids in enumerate(polys):
        for x,y in zip(ids,ids[1:]+ids[:1]):edges.setdefault(tuple(sorted((x,y))),[]).append(pi)
    region_source=json.loads((b.R/'Evidence/character-female-next/r0029-native-eye-interface/build-verification.json').read_text())
    region_info=json.loads((b.R/'Evidence/character-female-next/r0029-native-eye-interface/coarse-feasibility.json').read_text())['regions'];rows={}
    for side in ('L','R'):
        name=FITS[side]['name'];center=np.array(FITS[side]['centerM']);region=set(region_info[name]['inwardWallFaces']);boundary=[(x,y) for (x,y),fs in edges.items() if len(set(fs)&region)==1 and len(fs)==2 and len(set(fs)-region)==1];ids=sorted({i for e in boundary for i in e});near=np.flatnonzero((abs(V[:,0]-center[0])<.021)&(V[:,1]<-.095)&(abs(V[:,2]-center[2])<.020));knn=[]
        for row in scans[side]:
            if not row.get('upperOccludingBodyPoint'):continue
            p=np.array(row['upperOccludingBodyPoint']);dist=np.linalg.norm(V-p,axis=1);nearest=np.argsort(dist)[:6];hit=ct.find_nearest(Vector(p));knn.append({'dx':row['dx'],'coarseNearestTriangle':int(hit[2]),'coarsePolygon':int(polyids[hit[2]]),'coarseVertices':native_tri[hit[2]].tolist(),'nearestNativeVertices':[{'id':int(i),'position':V[i].tolist(),'distanceM':float(dist[i])} for i in nearest]})
        rows[side]={'sourceInwardWallFaces':sorted(region),'wallBoundaryEdges':[list(e) for e in boundary],'wallBoundaryVertices':[{'id':i,'position':V[i].tolist()} for i in ids],'nearVertices':[{'id':int(i),'position':V[i].tolist(),'normal':list(body.matrix_world.to_3x3()@body.data.vertices[int(i)].normal)} for i in near],'upperMarginNativeNeighborhood':knn}
    np.savez_compressed(E/'native-topology.npz',worldPositions=V,triangles=T,polygons=np.array(polys,dtype=object),trianglePolygons=polyids)
    mod.levels=3;bpy.context.view_layer.update();closeup('before')
    save('aperture-topology-inspection.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'scans':scans,'native':rows,'bodyEvaluatedVertices':len(hv),'bodyEvaluatedTriangles':len(ht),'nativeVertices':len(V),'resourceSeconds':time.time()-start,'scope':'Actual upper/lower visible exterior eye/body ray switches and native wall boundary/nearest topology only. No geometry mutated or saved; globe fit center is a coordinate reference, not a collision proxy.'})
    print('R35_INSPECT_DONE',json.dumps({'seconds':time.time()-start,'central':{s:scans[s][10] for s in scans},'wallBoundaries':{s:len(rows[s]['wallBoundaryVertices']) for s in rows}}),flush=True)
if __name__=='__main__':main()
