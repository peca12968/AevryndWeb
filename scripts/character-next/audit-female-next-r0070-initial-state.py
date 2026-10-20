"""Initial-state witnesses and real equal-control baseline; no new solver method."""
from pathlib import Path
import bpy,numpy as np,time,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
def module(n,p):
    s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
m=module('initial70','trial-female-next-r0070-native-motion.py');par=module('initial70parity','probe-female-next-r0067-contacts.py')
def main():
    tick=time.time();assert m.m.sha(m.SRC)==m.SHA;bpy.ops.wm.open_mainfile(filepath=str(m.SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();body=m.m.k.mesh(bpy.data.objects[m.m.native_names()[4]]);tree=BVHTree.FromPolygons(body['V'].tolist(),body['T'].tolist(),all_triangles=True);parts=[];examples=[];dirs=[(1.,.321,.173),(-.137,1.,.297),(.311,-.197,1.)]
    for name in ('AFN68_MAIN_RENDER_CURVES','AFN68_FLYAWAY_RENDER_CURVES'):
        o=bpy.data.objects[name];P=m.world(o);counts=np.array([c.points_length for c in o.data.curves]);starts=np.r_[0,np.cumsum(counts)[:-1]];local=np.concatenate([np.arange(n) for n in counts]);hist={};inside=0;unconfirmed=0;root_inside=0;impossible_first=0;maxdepth=0.;tested=0
        for ci,(start,count) in enumerate(zip(starts,counts)):
            arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P[start:start+count],axis=0),axis=1))]
            for j in range(int(count)):
                q=P[start+j];near,n,face,d=tree.find_nearest(Vector(q));tested+=1
                if np.dot(q-np.array(near),n)>=0 or d<=1e-4:continue
                rays=[par.parity(tree,q,v) for v in dirs]
                if not all(r['inside'] is True for r in rays):unconfirmed+=1;continue
                if j==0:
                    root_inside+=1
                    if d>np.linalg.norm(P[start+1]-P[start])+1e-6:impossible_first+=1
                    continue
                inside+=1;hist[str(j)]=hist.get(str(j),0)+1;maxdepth=max(maxdepth,float(d))
                if len(examples)<24:examples.append({'object':name,'curve':int(ci),'pointWithinCurve':j,'worldPoint':q.tolist(),'rootToKnotArcLowerBoundM':float(arc[j]),'unsignedNearestBodyDistanceM':float(d),'nativeBodyFace':int(body['nativeTriangleFace'][face]),'threeParityRays':rays})
        parts.append({'object':name,'testedAllKnots':tested,'confirmedStrongInsideRoots':root_inside,'confirmedStrongInsideNonRootKnots':inside,'insideNonRootWithinCurveIndexHistogram':hist,'maximumConfirmedNonRootDepthM':maxdepth,'rootInteriorNearestDistanceExceedsFirstSegmentLength':impossible_first,'negativeNormalCandidatesNotConfirmedInside':unconfirmed})
    m.save('initial-state-witnesses.json',{'source':str(m.SRC),'sha256':m.SHA,'frame':1,'parts':parts,'examples':examples,'numericalAllowanceM':1e-6,'strongInsideWitnessThresholdM':1e-4,'scope':'Actual neutral native interpolating knots, including the previously unqualified first20mm. Inside-root geometry is not automatically illegal; no anatomical follicle exemption is created. No-witness points not certified outside. This identifies startup/contact prerequisites, not a new production method or global clearance proof.','seconds':time.time()-tick});print('R70_INITIAL_STATE',parts,time.time()-tick,flush=True)
    s.frame_set(2);m.m.shade.settings();s.render.resolution_x=s.render.resolution_y=640;s.cycles.samples=16;controls=[]
    for view in ('face','body-face'):
        m.m.k.b.camera(view);s.camera.data.lens=85;s.render.filepath=str(m.E/f'baseline-2-{view}.png');bpy.ops.render.render(write_still=True);controls.append({'frame':2,'view':view,'file':s.render.filepath,'resolution':640,'samples':16,'camera':np.array(s.camera.matrix_world).tolist()})
    m.save('baseline-2-controls.json',controls);print('R70_INITIAL_AND_BASELINE_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
