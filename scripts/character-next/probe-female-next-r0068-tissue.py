"""Actual neutral interpolating-knot/body falsification; never a spline pass."""
from pathlib import Path
import bpy,numpy as np,time,importlib.util,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
def module(n,p):
    s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('guide68contactbuild','build-female-next-r0068-guide-surface.py');old=module('guide68parity','probe-female-next-r0067-contacts.py')
def main():
    tick=time.time();tag='c' if '--candidate-c' in sys.argv else ('b' if '--b' in sys.argv else 'a');ref=m.read(m.E/(tag+'-build-summary.json'));src=Path(ref['output']);assert m.m.sha(src)==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(src));bpy.context.scene.frame_set(1);arrays=np.load(m.E/(tag+'-render-curve-data.npz'));body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING']
    for md in body.modifiers:
        if md.type=='SUBSURF':md.levels=md.render_levels
    bpy.context.view_layer.update();row=m.k.mesh(body);V,T=row['V'],row['T'];edges=np.sort(np.concatenate((T[:,[0,1]],T[:,[1,2]],T[:,[2,0]])),axis=1);_,valence=np.unique(edges,axis=0,return_counts=True);assert np.all(valence==2);tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);dirs=[(1.,.321,.173),(-.137,1.,.297),(.311,-.197,1.)];parts=[];witnesses=[]
    for part,entry in enumerate(ref['visibleComponents']):
        o=bpy.data.objects[entry['object']];d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;P=m.array3(d.position_data,'vector');counts=np.array([c.points_length for c in d.curves],dtype='i4');rr=np.empty(len(P),dtype='f4');d.attributes['radius'].data.foreach_get('value',rr);assert np.array_equal(P,arrays[str(part)+'positions']) and np.array_equal(counts,arrays[str(part)+'counts']) and np.array_equal(rr,arrays[str(part)+'radii']);A=np.array(o.matrix_world);world=P.astype('f8')@A[:3,:3].T+A[:3,3];radius=rr.astype('f8')*np.linalg.norm(A[:3,:3],ord=2);types=np.zeros(len(counts),dtype='i4')
        if d.attributes.get('curve_type'):d.attributes['curve_type'].data.foreach_get('value',types)
        assert set(types.tolist()).issubset({0,1});starts=np.r_[0,np.cumsum(counts)[:-1]];tested=0;rootTested=0;minimumUnsigned=float('inf');minimumSampleBound=float('inf');inside=0;rootInside=0;uncertain=0
        for ci,(start,count) in enumerate(zip(starts,counts)):
            distances=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(world[start:start+count],axis=0),axis=1))]
            for local in range(int(count)):
                isRoot=local==0;arc=distances[local]
                if not isRoot and arc<=.02:continue
                index=int(start+local);q=world[index];near,normal,face,distance=tree.find_nearest(Vector(q));dot=float(np.dot(q-np.array(near),np.array(normal)));minimumUnsigned=min(minimumUnsigned,float(distance));minimumSampleBound=min(minimumSampleBound,float(distance-radius[index]));rootTested+=isRoot;tested+=not isRoot
                if dot>=0 or distance<=1e-4:continue
                rays=[old.parity(tree,q,di) for di in dirs]
                if not all(r['inside'] is True for r in rays):uncertain+=1;continue
                inside+=not isRoot;rootInside+=isRoot
                if not isRoot and len([w for w in witnesses if w['kind']=='freeShaft'])<12:witnesses.append({'kind':'freeShaft','object':o.name,'curve':int(ci),'pointWithinCurve':local,'rootToKnotPolylineArcLowerBoundM':float(arc),'worldPoint':q.tolist(),'unsignedNearestTissueDistanceM':float(distance),'conservativeRadiusBoundM':float(radius[index]),'nearestBodyTriangle':int(face),'nativeBodyFace':int(row['nativeTriangleFace'][face]),'threeIndependentParities':rays})
            if inside>=12:break
        parts.append({'object':o.name,'actualCurves':len(counts),'actualPoints':len(P),'curveTypes':sorted(set(types.tolist())),'testedFreeKnots':tested,'testedRoots':rootTested,'strongInsideFreeKnots':inside,'strongInsideRootsReportedSeparately':rootInside,'unconfirmedNormalCandidates':uncertain,'minimumSampledUnsignedDistanceM':minimumUnsigned,'minimumSampledUnsignedMinusConservativeRadiusM':minimumSampleBound,'allEligibleKnotsVisited':ci==len(counts)-1,'normalPrefilterDoesNotCertifyOutside':True})
    fail=any(x['strongInsideFreeKnots'] for x in parts);result={'status':'FAIL_ACTUAL_FREE_SHAFT_IN_TISSUE' if fail else 'NO_STRONG_INSIDE_KNOT_WITNESS_NOT_FULL_CONTACT_ACCEPTANCE','source':str(src),'sha256':m.m.sha(src),'actualVisibleGeometryMatchesSavedData':True,'parts':parts,'witnesses':witnesses,'bodyRenderVertices':len(V),'bodyRenderTriangles':len(T),'closedBodyManifoldVerified':True,'numericalAllowanceM':1e-6,'strongInsideWitnessThresholdM':1e-4,'freePathLowerBoundM':.02,'rootContainmentNotAutomaticallyClassifiedIllegal':True,'sampledMinimumIsNotGlobalMinimum':True,'exactGlobalSignedMinimumM':None,'fullCurvedSegmentsFiniteThicknessRootsSelfOrContinuousAccepted':False,'scope':'Confirmed interpolating knots only, one neutral pose. Nearest-normal prefilter/three parities falsify strong inside knots; their absence cannot prove outside at every point or finite-tube/spline clearance. Anisotropic matrix spectral norm is a conservative radius bound, not an exact circular world radius.','seconds':time.time()-tick};m.m.save(tag+'-tissue-knot-probe.json',result);print('R68_TISSUE_KNOT_PROBE',tag,result['status'],parts,time.time()-tick,flush=True)
if __name__=='__main__':main()
