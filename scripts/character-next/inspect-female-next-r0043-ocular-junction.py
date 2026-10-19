"""Actual neutral ocular aperture and lid/globe apposition measurements.
Source file untouched. Geometry-only rays, not refracted appearance metrics.
"""
import bpy,importlib.util,time,json
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('q42eye43',Path(__file__).with_name('build-female-next-r0042-shadow-quality.py'));q=importlib.util.module_from_spec(sp);sp.loader.exec_module(q)
f=q.f;b=q.b;v=q.v;ch=q.a.i.i.ch
i=f.flowcheck.module('lid35eye43','inspect-female-next-r0035-lid-rest.py')
SRC=q.OUT;E=b.R/'Evidence/character-female-next/r0043-ocular-junction';E.mkdir(exist_ok=True);S=b.S
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def main():
    start=time.time();assert b.sha(SRC)=='d62c180a5af61f6f8d800926b101738c89a8fbe7785fe1054fd655fd018824da';bpy.ops.wm.open_mainfile(filepath=str(SRC));before=f.state();V,T=b.evaluated(bpy.data.objects[b.BODY],True);bt=i.tree(V,T);scans={};rim={};summary={}
    for side in ('L','R'):
        ev,et=i.outer(side);eye=i.tree(ev,et);center=np.array(i.FITS[side]['centerM']);rows=i.aperture(bt,eye,center,np.linspace(-.0108,.0108,101));scans[side]=rows;rim[side]={}
        for part,sgn in [('upper',1),('lower',-1)]:
            points=[];gaps=[];raygaps=[]
            for row in rows:
                if not row.get('visible') or row['visibleSampleRuns']!=1:continue
                z=row[part+'Z']+sgn*2e-5;h,n,ti,dist=bt.ray_cast(Vector((row['x'],-.25,z)),Vector((0,1,0)),.3)
                eh,_,_,_=eye.ray_cast(Vector((row['x'],-.25,z)),Vector((0,1,0)),.3)
                if h is None or eh is None:continue
                p=np.array(h);points.append(p.tolist());gaps.append(eye.find_nearest(h)[3]);raygaps.append(float(eh.y-h.y))
            rim[side][part]={'points':points,'nearestEyeSurfaceGapM':gaps,'frontDepthGapYM':raygaps}
        central=rows[50];summary[side]={'centralAperture':central,'physicalIrisRadiusM':.00565,'centralSuperiorIrisCoverageM':.00565-central['upperAboveEyeCenterM'],'lowerMarginBelowCenterM':center[2]-central['lowerZ'],'upperGapRangeM':[min(rim[side]['upper']['nearestEyeSurfaceGapM']),max(rim[side]['upper']['nearestEyeSurfaceGapM'])],'lowerGapRangeM':[min(rim[side]['lower']['nearestEyeSurfaceGapM']),max(rim[side]['lower']['nearestEyeSurfaceGapM'])]}
    save('source-ocular-measurements.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'summary':summary,'scans':scans,'rim':rim,'bodyVertices':len(V),'bodyTriangles':len(T),'scope':'Geometry-only actual eye exterior rays and nearest-surface distances on source visible body rim. Not refracted apparent coverage, anatomy score or collision qualification.','seconds':time.time()-start})
    f.E=E;f.render('before');ch.review.extras('before',E)
    g=f.g;g.E=E;g.closeup('before');assert f.state()==before
    save('diagnostic-integrity.json',{'source':str(SRC),'sourceSha256':b.sha(SRC),'originalStateExact':True,'seconds':time.time()-start})
    print('R43_MEASUREMENTS',summary,time.time()-start,flush=True)
if __name__=='__main__':main()
