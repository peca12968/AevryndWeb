"""Locate actual failed rod edges; do not modify saved candidates or tolerances."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sp=importlib.util.spec_from_file_location('diagnose70',Path(__file__).with_name('trial-female-next-r0070-native-motion.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
def main():
    a=m.m.read(m.E/'a-build-summary.json');assert m.m.sha(m.OUT)==a['outputSha256'];bpy.ops.wm.open_mainfile(filepath=str(m.OUT));bpy.context.scene.frame_set(2);bpy.context.view_layer.update();raw=np.load(m.E/'a-native-motion-raw.npz');counts=raw['counts'];starts=np.r_[0,np.cumsum(counts)[:-1]];curve=np.repeat(np.arange(len(counts)),counts);local=np.concatenate([np.arange(n) for n in counts]);P=[];K=[]
    for name in ('AFN68_MAIN_RENDER_CURVES','AFN68_FLYAWAY_RENDER_CURVES'):
        o=bpy.data.objects[name];P.append(m.world(o));o.modifiers['AFN70_NATIVE_FLEXIBLE_TRIAL'].show_viewport=False;bpy.context.view_layer.update();K.append(m.world(o));o.modifiers['AFN70_NATIVE_FLEXIBLE_TRIAL'].show_viewport=True
    P=np.concatenate(P);K=np.concatenate(K);rest=raw['rest'].astype('f8');edges=np.flatnonzero(local<np.repeat(counts,counts)-1);ds=np.linalg.norm(rest[edges+1]-rest[edges],axis=1);strain=np.abs(np.linalg.norm(P[edges+1]-P[edges],axis=1)/ds-1);bad=edges[strain>.10];order=edges[np.argsort(strain)[-24:][::-1]];body=m.m.k.mesh(bpy.data.objects[m.m.native_names()[4]]);tree=BVHTree.FromPolygons(body['V'].tolist(),body['T'].tolist(),all_triangles=True);examples=[]
    for i in order:
        q=[]
        for point in (int(i),int(i+1)):
            near,n,face,d=tree.find_nearest(Vector(K[point]));q.append({'point':point,'rigidWorld':K[point].tolist(),'actualWorld':P[point].tolist(),'rigidNearestBodyUnsignedDistanceM':float(d),'rigidNearestNormalDotM':float(np.dot(K[point]-np.array(near),n))})
        examples.append({'curve':int(curve[i]),'withinCurveEdge':int(local[i]),'restLengthM':float(np.linalg.norm(rest[i+1]-rest[i])),'actualLengthM':float(np.linalg.norm(P[i+1]-P[i])),'points':q})
    result={'source':str(m.OUT),'sha256':a['outputSha256'],'frame':2,'edgesOverTenPercent':len(bad),'byWithinCurveEdge':{str(int(j)):int(np.sum(local[bad]==j)) for j in np.unique(local[bad])},'examples':examples,'noSourceChanged':True,'purpose':'Distinguish source-root interface incompatibility, cached-plane contact error and solver/shape failure before choosing another structure.'};m.save('a-failure-localization.json',result);print('R70_FAILURE_LOCATION',len(bad),result['byWithinCurveEdge'],examples[:4],flush=True)
if __name__=='__main__':main()
