"""Bounded falsification on real rendered curve knots against closed tissue.

Three ray parities confirm inside points. Free-shaft knots must be >20mm
along the path from the root. Root containment is separately reported and
is not by itself called illegal follicle penetration. No global pass claim.
"""
from pathlib import Path
import bpy,numpy as np,time,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('eve67probe',Path(__file__).with_name('build-female-next-r0067-native-eve.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
def parity(tree,p,d):
    direction=Vector(d).normalized();origin=Vector(p);hits=[]
    for _ in range(96):
        co,normal,index,distance=tree.ray_cast(origin,direction,4.)
        if co is None:return {'count':len(hits),'inside':len(hits)%2==1,'triangleIDs':hits,'terminated':True}
        hits.append(int(index));origin=co+direction*1e-7
    return {'count':len(hits),'inside':None,'triangleIDs':hits,'terminated':False}
def main():
    tick=time.time();ref=m.read(m.E/'b-build-summary.json');src=Path(ref['output']);assert m.m.sha(src)==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(src));bpy.context.scene.frame_set(1)
    hair=bpy.data.objects[ref['completeCurveObject']];P,counts,rr=m.curve_arrays(hair);raw=np.load(m.E/'b-converted-eve-data.npz');assert np.array_equal(P,raw['positions']) and np.array_equal(rr,raw['radii']) and np.array_equal(counts,raw['counts']);matrix=np.array(hair.matrix_world);world=P.astype('f8')@matrix[:3,:3].T+matrix[:3,3];rr=rr.astype('f8')*np.linalg.norm(matrix[:3,:3],ord=2);starts=np.r_[0,np.cumsum(counts)[:-1]]
    types=np.zeros(len(counts),dtype='i4');attr=hair.data.attributes.get('curve_type')
    if attr:attr.data.foreach_get('value',types)
    assert set(types.tolist()).issubset({0,1}),'Only interpolating Catmull-Rom/POLY knot witnesses are supported.'
    body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING']
    for md in body.modifiers:
        if md.type=='SUBSURF':md.levels=md.render_levels
    bpy.context.view_layer.update();row=m.k.mesh(body);V,T=row['V'],row['T'];tri=V[T];edges=np.sort(np.concatenate((T[:,[0,1]],T[:,[1,2]],T[:,[2,0]])),axis=1);_,valence=np.unique(edges,axis=0,return_counts=True);assert np.all(valence==2),'Body parity requires closed manifold surface.'
    tree=BVHTree.FromPolygons(V.tolist(),T.tolist(),all_triangles=True);dirs=[(1.,.321,.173),(-.137,1.,.297),(.311,-.197,1.)];witnesses=[];checked={};maxTests=4096
    for kind in ('freeShaft','root'):
        tested=0;found=0
        for ci in np.linspace(0,len(counts)-1,min(len(counts),maxTests),dtype='i4'):
            n=int(counts[ci]);local=0 if kind=='root' else max(1,n//2);index=int(starts[ci]+local);q=world[index];arc=float(np.linalg.norm(np.diff(world[starts[ci]:index+1],axis=0),axis=1).sum())
            if kind=='freeShaft' and arc<=.02:continue
            tested+=1;closest,normal,face,distance=tree.find_nearest(Vector(q));dot=float(np.dot(q-np.array(closest),np.array(normal)))
            if distance<1e-4 or dot>=0:continue
            rays=[parity(tree,q,d) for d in dirs]
            if not all(r['inside'] is True for r in rays):continue
            witnesses.append({'kind':kind,'curve':int(ci),'pointWithinCurve':local,'flatPoint':index,'worldPoint':q.tolist(),'curveKnotType':int(types[ci]),'rootToKnotPolylineArcLowerBoundM':arc,'unsignedNearestTissueDistanceM':float(distance),'pointRadiusM':float(rr[index]),'sampleSignedTissueClearanceM':-float(distance)-float(rr[index]),'nearestBodyTriangle':int(face),'nativeBodyFace':int(row['nativeTriangleFace'][face]),'nearestBodyPoint':list(closest),'threeIndependentParities':rays,'interpretation':'Actual interpolating free-shaft knot lies inside closed tissue, beyond20mm of path from the root.' if kind=='freeShaft' else 'Inside tissue at root; not alone classified as illegal anatomy. Follicle attachment/containment still requires a declared anatomical model.'});found+=1
            if found>=6:break
        checked[kind]={'testedActualKnots':tested,'retainedInsideWitnesses':found,'globalCountOrPass':False}
    fail=any(w['kind']=='freeShaft' for w in witnesses)
    result={'status':'FAIL_ACTUAL_FREE_SHAFT_IN_TISSUE' if fail else 'BOUNDED_SAMPLE_ONLY_CONTACT_UNACCEPTED','source':str(src),'sha256':m.m.sha(src),'actualCurves':len(counts),'actualPoints':len(P),'curveTypes':sorted(set(types.tolist())),'bodyRenderVertices':len(V),'bodyRenderTriangles':len(T),'bodyClosedManifoldEdgesVerified':True,'bodyBoundaryOrNonmanifoldEdges':int((valence!=2).sum()),'curveDataRadiiMatchActualSavedNativeData':True,'worldMaximumShaftRadiusM':float(rr.max()),'numericalAllowanceM':1e-6,'strongInsideWitnessThresholdM':1e-4,'freePathLowerBoundM':.02,'tested':checked,'witnesses':witnesses,'failureCountIsGlobalTotal':False,'exactGlobalSignedMinimumM':None,'scope':'One neutral frame; actual interpolating knots only. Confirmed free-shaft inside points falsify contact. Roots are reported separately without inventing anatomical exemptions. No all-segment/all-body/optics/self/continuous pass.','selfHairOrDynamicsAccepted':False,'seconds':time.time()-tick};m.m.save('b-contact-falsification.json',result);print('R67_CONTACT_PROBE',result['status'],checked,time.time()-tick,flush=True)
if __name__=='__main__':main()
