"""Private read-only source-guide versus generated-child body diagnostics."""
import bpy,importlib.util,json,time
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('c39rawdiag',Path(__file__).with_name('study-female-next-r0039-artist-transfer.py'));c=importlib.util.module_from_spec(sp);sp.loader.exec_module(c)
a=c.a;f=c.f;b=c.b;PVT=c.PRIVATE
def raw():
    bpy.ops.wm.open_mainfile(filepath=str(c.REF))
    def enable(lc):
        lc.exclude=False;lc.hide_viewport=False
        for q in lc.children:enable(q)
    enable(bpy.context.view_layer.layer_collection)
    for o in bpy.context.scene.objects:
        if o.name!='head':
            for mm in o.modifiers:mm.show_viewport=False;mm.show_render=False
    for name in ('long hair main','long hair strands'):
        o=bpy.data.objects[name];o.hide_set(False)
        ng=bpy.data.node_groups.new('PRIVATE_RAW_RESAMPLE_'+name,'GeometryNodeTree')
        ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
        i=ng.nodes.new('NodeGroupInput');r=ng.nodes.new('GeometryNodeResampleCurve');r.inputs['Mode'].default_value='Count';r.inputs['Count'].default_value=128;o1=ng.nodes.new('NodeGroupOutput')
        ng.links.new(i.outputs[0],r.inputs[0]);ng.links.new(r.outputs[0],o1.inputs[0]);m=o.modifiers.new('PRIVATE_RAW_NATIVE_CURVE_EVALUATION','NODES');m.node_group=ng
    bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();groups=[];out=[]
    for name in ('long hair main','long hair strands'):
        d=bpy.data.objects[name].evaluated_get(dg).data;p=np.empty(len(d.points)*3,dtype='f4');d.position_data.foreach_get('vector',p);p=p.reshape(-1,128,3);groups.extend([name]*len(p));out.extend(p)
    V,T=b.evaluated(bpy.data.objects['head'],True)
    return np.array(out,dtype='f8'),groups,V,T
def analyze(P,R,tree,tri):
    fail=[];curvefails=set();inside_diagnostic=0.;near=[]
    for ci,(q,r) in enumerate(zip(P,R)):
        ds=[tree.find_nearest(Vector(v))[3] for v in q];arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(q,axis=0),axis=1))]
        for j in range(127):
            gap,method=f.flowcheck.cap.segment_test(q[j],q[j+1],ds[j],ds[j+1],float(max(r[j],r[j+1])),tree,tri)
            if gap<=0:fail.append((ci,j,float(arc[j]),method));curvefails.add(ci)
        for j in range(128):
            h,n,ti,d=tree.find_nearest(Vector(q[j]))
            if (Vector(q[j])-h).dot(n)<0:inside_diagnostic=max(inside_diagnostic,d)
    bins={'withinFirst1mm':0,'1to5mm':0,'5to20mm':0,'after20mm':0};centerline={}
    for ci,j,arc,method in fail:
        key='withinFirst1mm' if arc<.001 else ('1to5mm' if arc<.005 else ('5to20mm' if arc<.020 else 'after20mm'));bins[key]+=1
        if method=='centreline_cross':centerline[key]=centerline.get(key,0)+1
    return {'curves':len(P),'segments':len(P)*127,'curvesWithAnyUnqualifiedSegment':len(curvefails),'unqualifiedSegments':len(fail),'arcBins':bins,'centerlineCrossArcBins':centerline,
      'maximumNegativeNearestNormalUnsignedDistanceM':float(inside_diagnostic),'distanceScope':'Nearest-normal sign diagnostic only on open donor head; not certified signed depth or a source volume qualification. No region excluded.'}
def main():
    start=time.time();P,groups,V,T=raw();scale=np.array((.094,.085,.081));off=np.array((0,.005,.234));P=P*scale+off;V=V*scale+off
    tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);tri=V[T]
    radii=np.load(c.a.S/'aevrynd-female-next-r0033-c-bob-fibres.npz')['radii']
    result=analyze(P,radii[:len(P)],tree,tri)
    c.write('raw-guide-contact-cause.json',{'source':str(c.REF),'sourceSha256':b.sha(c.REF),'rawGuideAssessment':result,
      'rawCurveNativeEvaluation':'Original hair modifiers disabled; own native ResampleCurve128 only, preserves source spline shape rather than control polygons',
      'generatedChildSampleAssessment':'c1-donor-original-contact-diagnostic.json:256representatives,441unqualifiedsegments; not same-count comparison or full child qualification',
      'scope':'Private cause diagnosis, no asset adoption or arbitrary root exclusions','seconds':time.time()-start})
    print('RAW_SOURCE_GUIDE_CONTACT',result,time.time()-start,flush=True)
if __name__=='__main__':main()
