"""Cheap complete-segment/body feasibility on style guides at intended radii.

The deliberately enlarged display-guide radius is not treated as physical hair.
One anatomical first segment per exact same-source skin follicle is reported
separately; no other segment or body region is excluded.
"""
from pathlib import Path
import numpy as np,bpy,json,time,importlib.util,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('groom61contact',Path(__file__).with_name('build-female-next-r0061-surface-flow-groom.py'));g=importlib.util.module_from_spec(sp);sp.loader.exec_module(g)

def main():
    tick=time.time();tag='b-guides' if '--scalp-domain-repair' in sys.argv else 'a-guides';data=np.load(g.E/(tag+'-authoring.npz'));cache=np.load(g.E/'actual-body-render-surface.npz');P=cache['P'];T=cache['T'];tri=P[T]
    tree=BVHTree.FromPolygons(P.tolist(),T.tolist(),all_triangles=True)
    Q=data['positions'];radii=np.minimum(data['radii'],.000035);lineage=P[T[data['rootTriangles']]];roots=np.einsum('ij,ijk->ik',data['rootBarycentric'],lineage)
    rootError=np.linalg.norm(Q[:,0]-roots,axis=1);assert rootError.max()<1e-6
    report=g.k.f.flowcheck.check(Q[:,1:],radii[:,1:],tree,tri,roots=True)
    report['scope']='Feasibility of all256style paths at intended35umfibre radius; excludes only anatomically attached first segment per exact skin triangle/barycentric root. Not18kactualfibre proof, not guide display radius, not self/dynamic proof.'
    report['exactSourceFollicles']=len(Q);report['maximumRootLineageErrorM']=float(rootError.max());report['seconds']=time.time()-tick
    g.save(tag+'-feasibility.json' if tag!='a-guides' else 'guide-feasibility.json',report);print('R61_GUIDE_FEASIBILITY',report['status'],report['unqualifiedSegments'],len(report['rootFailures']),time.time()-tick,flush=True)
if __name__=='__main__':main()
