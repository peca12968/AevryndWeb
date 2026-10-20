"""Falsify strong free-knot tissue intersections at actual moved rig poses.

No absence-of-witness result is a finite-spline/continuous contact pass.
"""
from pathlib import Path
import bpy,numpy as np,time,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
def module(n,p):
    s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('contact69build','build-female-next-r0069-complete-controls.py');p=module('contact69parity','probe-female-next-r0067-contacts.py')
def main():
    tick=time.time();ref=m.read(m.E/'a-build-summary.json');assert m.sha(m.OUT)==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(m.OUT));results=[];directions=[(1.,.321,.173),(-.137,1.,.297),(.311,-.197,1.)]
    for frame in (13,25,49):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();body=m.k.mesh(bpy.data.objects[m.native_names()[4]]);V,T=body['V'],body['T'];tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);parts=[];witnesses=[]
        for name in ('AFN68_MAIN_RENDER_CURVES','AFN68_FLYAWAY_RENDER_CURVES'):
            o=bpy.data.objects[name];d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;P=m.base.array3(d.position_data,'vector');A=np.array(o.matrix_world);P=P.astype('f8')@A[:3,:3].T+A[:3,3];counts=np.array([c.points_length for c in d.curves]);starts=np.r_[0,np.cumsum(counts)[:-1]];rr=np.empty(len(P),'f4');d.attributes['radius'].data.foreach_get('value',rr);rr=rr*np.linalg.norm(A[:3,:3],ord=2);inside=0;rootinside=0;tested=0;roots=0;unconfirmed=0;minimum=float('inf');bound=float('inf')
            for ci,(start,count) in enumerate(zip(starts,counts)):
                arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P[start:start+count],axis=0),axis=1))]
                for j in range(int(count)):
                    root=j==0
                    if not root and arc[j]<=.02:continue
                    q=P[start+j];near,normal,face,distance=tree.find_nearest(Vector(q));roots+=root;tested+=not root;minimum=min(minimum,float(distance));bound=min(bound,float(distance-rr[start+j]))
                    if np.dot(q-np.array(near),np.array(normal))>=0 or distance<=1e-4:continue
                    rays=[p.parity(tree,q,v) for v in directions]
                    if not all(x['inside'] is True for x in rays):unconfirmed+=1;continue
                    rootinside+=root;inside+=not root
                    if not root and len(witnesses)<12:witnesses.append({'frame':frame,'object':name,'curve':int(ci),'pointWithinCurve':j,'worldPoint':q.tolist(),'rootToKnotArcLowerBoundM':float(arc[j]),'unsignedNearestTissueDistanceM':float(distance),'conservativeRadiusBoundM':float(rr[start+j]),'nearestBodyTriangle':int(face),'nativeBodyFace':int(body['nativeTriangleFace'][face]),'threeIndependentParityRays':rays})
                if inside>=12:break
            parts.append({'object':name,'testedFreeKnots':tested,'testedRoots':roots,'strongInsideFreeKnots':inside,'strongInsideRootsReportedSeparately':rootinside,'unconfirmedNormalCandidates':unconfirmed,'allEligibleKnotsVisited':ci==len(counts)-1,'minimumSampledUnsignedDistanceM':minimum,'minimumSampledUnsignedMinusConservativeRadiusM':bound,'sampledMinimumIsNotGlobal':True})
        row={'frame':frame,'status':'FAIL_STRONG_FREE_KNOT_TISSUE_WITNESSES' if any(x['strongInsideFreeKnots'] for x in parts) else 'NO_STRONG_FREE_KNOT_WITNESS_NOT_CONTACT_ACCEPTANCE','parts':parts,'witnesses':witnesses};results.append(row);print('R69_MOVED_TISSUE',frame,row['status'],parts,time.time()-tick,flush=True)
    m.save('a-moved-tissue-probe.json',{'source':str(m.OUT),'sha256':ref['outputSha256'],'poses':results,'numericalAllowanceM':1e-6,'strongInsideWitnessThresholdM':1e-4,'freePathLowerBoundM':.02,'exactGlobalSignedMinimumM':None,'fullRootsCurvedSegmentsFiniteRadiiSelfClothOrContinuousAccepted':False,'normalPrefilterDoesNotCertifyOutside':True,'scope':'Actual displayed interpolating knots in three moved poses, body only. Strong witnesses are falsifications; no witness never establishes full clearance. Topological body closure inherited unchanged indices, body self contact not certified. Root joining already unaccepted in r68.','seconds':time.time()-tick})
if __name__=='__main__':main()
