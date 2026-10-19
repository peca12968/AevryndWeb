"""Actual repaired surface sections at exactly the original diagnostic plane."""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
sp=importlib.util.spec_from_file_location('sect60',Path(__file__).with_name('verify-female-next-r0060-assembly.py'));k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
E=k.E
def main():
    tick=time.time();a=k.read(E/'b-build-summary.json');assert k.b.sha(Path(a['output']))==a['outputSha256'];bpy.ops.wm.open_mainfile(filepath=a['output']);original=k.read(E/'rendered-ocular-sections.json');C=np.array(original['centreWorldM']);plane=original['planeXWorldM'];parts=[bpy.data.objects[a['visibleComponents'][str(i)]] for i in range(5)]
    for o in parts:
        for md in o.modifiers:
            if md.type=='SUBSURF':md.levels=md.render_levels
    result={'source':a['output'],'sourceSha256':a['outputSha256'],'centreWorldM':C.tolist(),'planeXWorldM':plane,'poses':{}}
    for frame,label in ((1,'neutral'),(21,'closed')):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();V,T,mi,fi=k.join([k.mesh(o) for o in parts]);tri=V[T];ids=np.flatnonzero((tri[:,:,0].min(1)<=plane)&(tri[:,:,0].max(1)>=plane)&(tri[:,:,2].min(1)<C[2]+.027)&(tri[:,:,2].max(1)>C[2]-.027)&(tri[:,:,1].min(1)<C[1]+.025)&(tri[:,:,1].max(1)>C[1]-.04));sections={}
        for i in ids:
            p=tri[i];points=[]
            for j in range(3):
                aa=p[j];bb=p[(j+1)%3];den=bb[0]-aa[0]
                if abs(den)<1e-15:continue
                t=(plane-aa[0])/den
                if 0<=t<=1:
                    q=aa+t*(bb-aa)
                    if not any(np.linalg.norm(q-z)<1e-10 for z in points):points.append(q)
            if len(points)==2:sections.setdefault(str(mi[i]),[]).append([p.tolist() for p in points])
        result['poses'][label]=sections
    result['seconds']=time.time()-tick;k.save('b-rendered-ocular-sections.json',result);print('R60_REPAIRED_SECTIONS',time.time()-tick,flush=True)
if __name__=='__main__':main()
