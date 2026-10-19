"""Final neutral aperture measurement, control bypass and unaffected contacts.
No rest-file mutation, no dynamic/continuous or whole-character score claim.
"""
import bpy,importlib.util,time,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
sp=importlib.util.spec_from_file_location('build43review',Path(__file__).with_name('build-female-next-r0043-lid-apposition.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
i=a.i;f=a.f;b=a.b;v=a.v;E=a.E
def main():
    start=time.time();assert a.CONSISTENT;gate=json.loads((E/'b-saved-verification.json').read_text());assert gate['status']=='PASS_TESTED_NEUTRAL_JUNCTION_SCOPE';bpy.ops.wm.open_mainfile(filepath=str(a.SRC));V0,T0=b.evaluated(bpy.data.objects[b.BODY],True);bpy.ops.wm.open_mainfile(filepath=str(a.OUT));body=bpy.data.objects[b.BODY];V,T=b.evaluated(body,True);layer=body.modifiers['AFN43_NeutralLidRest'];layer.show_viewport=False;bpy.context.view_layer.update();vb,tb=b.evaluated(body,True);assert np.array_equal(vb,V0) and np.array_equal(tb,T0);layer.show_viewport=True
    multires=next(x for x in body.modifiers if x.type=='MULTIRES');level=multires.levels;multires.levels=0;bpy.context.view_layer.update();low,_=b.evaluated(body,True);assert len(low)==len(body.data.vertices);multires.levels=level;bpy.context.view_layer.update();vr,tr=b.evaluated(body,True);assert np.array_equal(vr,V) and np.array_equal(tr,T)
    bt=i.i.tree(V,T);summary={}
    for side in ('L','R'):
        ev,et=i.i.outer(side);eye=i.i.tree(ev,et);c=np.array(i.i.FITS[side]['centerM']);rows=i.i.aperture(bt,eye,c,np.linspace(-.0108,.0108,101));parts={}
        for part,sign in [('upper',1),('lower',-1)]:
            gaps=[]
            for row in rows:
                if not row.get('visible') or row['visibleSampleRuns']!=1:continue
                hit,_,_,_=bt.ray_cast(Vector((row['x'],-.25,row[part+'Z']+sign*2e-5)),Vector((0,1,0)),.3)
                if hit is not None:gaps.append(eye.find_nearest(hit)[3])
            parts[part]={'minimumSampledGapM':float(min(gaps)),'medianSampledGapM':float(np.median(gaps)),'maximumSampledGapM':float(max(gaps)),'samples':len(gaps)}
        summary[side]={'centralAperture':rows[50],'lidApposition':parts}
    old=json.loads((E/'source-ocular-measurements.json').read_text());apError=max(abs(summary[s]['centralAperture'][k]-old['summary'][s]['centralAperture'][k]) for s in ('L','R') for k in ('upperZ','lowerZ'));assert apError<1e-7
    #All old scalp/brow finite capsules versus each changed tissue. Complete
    #segment AABB exclusion first; any candidate requires finite segment test.
    tissues={}
    for row in json.loads((E/'b-build-summary.json').read_text())['patches']:
        pv,pt=b.evaluated(bpy.data.objects[row['object']],True);tissues[row['object']]=(pv,pt,i.i.tree(pv,pt))
    hairReport={}
    for name in (f.OLD,'AFN36_L_BrowFibres','AFN36_R_BrowFibres'):
        o=bpy.data.objects[name];hp,hr=i.ch.rod.m.eval_arrays(o);mx=np.array(o.matrix_world);hp=hp.astype('f8')@mx[:3,:3].T+mx[:3,3];hr=hr.astype('f8')*np.linalg.norm(mx[:3,:3],ord=2);lo=np.minimum(hp[:,:-1],hp[:,1:])-np.maximum(hr[:,:-1],hr[:,1:])[...,None]-1e-6;hi=np.maximum(hp[:,:-1],hp[:,1:])+np.maximum(hr[:,:-1],hr[:,1:])[...,None]+1e-6;hairReport[name]={}
        for n,(pv,pt,tree) in tissues.items():
            cand=np.argwhere(np.all(hi>=pv.min(0),axis=2)&np.all(lo<=pv.max(0),axis=2));bad=[]
            for ci,j in cand:
                aa,bb=hp[ci,j:j+2];da=tree.find_nearest(Vector(aa))[3];db=tree.find_nearest(Vector(bb))[3];gap,method=f.flowcheck.cap.segment_test(aa,bb,da,db,float(max(hr[ci,j:j+2])),tree,pv[pt])
                if gap<=0:bad.append({'curve':int(ci),'segment':int(j),'gapM':gap})
            hairReport[name][n]={'totalSegments':int(lo.shape[0]*lo.shape[1]),'directSegments':len(cand),'excludedSegments':int(lo.shape[0]*lo.shape[1]-len(cand)),'unqualifiedSegments':len(bad),'failureSamples':bad[:10]}
    edges,counts=v.v30.edges(T);closed={'boundaryEdges':int((counts==1).sum()),'nonManifoldEdges':int((counts>2).sum())};good=closed['boundaryEdges']==closed['nonManifoldEdges']==0 and all(x['unqualifiedSegments']==0 for row in hairReport.values() for x in row.values())
    a.save('a-final-review-checks.json',{'status':'PASS_TESTED_NEUTRAL_ADDITIONAL_SCOPE' if good else 'FAIL_OR_UNRESOLVED','source':str(a.OUT),'sourceSha256':b.sha(a.OUT),'layerDisabledReturnsExactSourceGeometry':True,'sourceNativeCageVertexCount':len(low),'nativeLevelGuardBypassesCorrectly':True,'fullRestRoundTripExact':True,'actualBodyClosedManifold':closed,'centralApertureMaximumChangeM':apError,'afterMeasurements':summary,'oldScalpBrowAgainstChangedTissues':hairReport,'scope':'All measurements are sampled actual surface distances, not global minimum clearances. No motion/continuous,full scalp self or runtime proof.','seconds':time.time()-start});print('R43_FINAL_REVIEW_CHECKS',good,time.time()-start,flush=True)
if __name__=='__main__':main()
