from pathlib import Path
import bpy,numpy as np,json,importlib.util,datetime
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');R=Path('D:/Download/Aevrynd');E=C/'evidence/character-female-next/r0181-inner-lid-follicle-domain'
sp=importlib.util.spec_from_file_location('r181base',C/'scripts/character-next/build-female-next-r0180-anatomical-lash-rows.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h
def main():
 t=json.loads((E/'before.json').read_text());bpy.ops.wm.open_mainfile(filepath=t['source']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects[a.FIXED[0]];W,T=a.geometry(skin);line=np.load(E.parent/'r0180-anatomical-lash-rows/anatomical-lash-row-lineage.npz');q=json.loads((E.parent/'r0180-anatomical-lash-rows/independent-anatomical-lash-row-readback.json').read_text());faces=sorted({v['actualSkinTriangle'] for x in q['regionalSkinControlChordWitnesses'] for v in x['firstTenLocations']});rids=sorted({v['curveID'] for x in q['regionalSkinControlChordWitnesses'] for v in x['firstTenLocations']});original=R/'engine/assets/characters/female-next/source/r0138-source/aevrynd-female-next-r0138-a-native-current-gaze.blend'
 with bpy.data.libraries.load(str(original),link=False) as (fr,to):to.objects=[a.FIXED[0]]
 old=to.objects[0];ow=h.arr(old.data.vertices,'co',len(old.data.vertices),3);ow=ow@np.array(old.matrix_world)[:3,:3].T+np.array(old.matrix_world.translation);old.data.calc_loop_triangles();ot=np.array([x.vertices[:] for x in old.data.loop_triangles]);tree=BVHTree.FromPolygons(ow.tolist(),ot.tolist(),all_triangles=True);kd=KDTree(len(ow))
 for i,p in enumerate(ow):kd.insert(Vector(p),i)
 kd.balance();originalFaces={tuple(sorted(x)) for x in ot};rows=[]
 for fi in faces:
  vs=W[T[fi]];nearest=[kd.find(Vector(p)) for p in vs];oldIDs=[x[1] for x in nearest];near,normal,oldFi,gap=tree.find_nearest(Vector(vs.mean(0)));no=np.cross(vs[1]-vs[0],vs[2]-vs[0]);no/=np.linalg.norm(no);rows.append({'actualSkinTriangle':fi,'vertices':T[fi].tolist(),'world':vs.tolist(),'nearestOriginalVertexDistancesM':[float(x[2]) for x in nearest],'exactOriginalTriangleByCoordinates':max(x[2] for x in nearest)<1e-6 and tuple(sorted(oldIDs)) in originalFaces,'nearestOriginalFace':int(oldFi),'centroidToOriginalSkinDistanceM':float(gap),'currentNormal':no.tolist(),'nearestOriginalNormal':list(normal)})
 r=[]
 for cid in rids:
  rt=line['rootTriangles'][cid];B=W[rt];p=line['rootWorld'][cid];around=np.flatnonzero(np.any(np.isin(T,rt),axis=1));no=np.cross(B[1]-B[0],B[2]-B[0]);no/=np.linalg.norm(no);nearby=[]
  for fi in around:
   if fi not in faces:continue
   bb=W[T[fi]];nn=np.cross(bb[1]-bb[0],bb[2]-bb[0]);nn/=np.linalg.norm(nn);nearby.append({'face':int(fi),'sharedVertices':sorted(set(rt.tolist())&set(T[fi].tolist())),'faceNormalDot':float(nn@no),'faceRootSignedPlaneDistanceM':float((p-bb[0])@nn)})
  r.append({'curveID':cid,'rootTriangle':rt.tolist(),'rootBC':line['rootBC'][cid].tolist(),'rootWorld':p.tolist(),'rootFaceNormal':no.tolist(),'relatedRecordedSkinFacesSharingRootVertices':nearby})
 record={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':t['source'],'originalPreBooleanSource':str(original),'originalPreBooleanSourceSHA256':a.a.sha(original),'actualSkinTriangleCount':len(T),'originalPreBooleanTriangleCount':len(ot),'recordedFailureFaces':rows,'recordedFailureRootDomains':r,'scope':'Exact old source triangle matching by actual world coordinates identifies retained anterior triangles versus Boolean-modified/new domains; absence is not automatically posterior wall. No classification inferred from face index or normal alone.'};(E/'actual-failed-skin-surface-lineage.json').write_bytes((json.dumps(record,indent=2)+'\n').encode());print('R181_ACTUAL_RECORDED_SURFACE_ROOT_LINEAGE_INSPECTED',flush=True)
if __name__=='__main__':main()
