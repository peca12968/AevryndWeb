"""Export self-contained authoring bindings for the later Aevrynd guide solver."""
import bpy,json,shutil,importlib.util
import numpy as np
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('flow',Path(__file__).with_name('build-female-next-r0014-scalp-flow.py'));flow=importlib.util.module_from_spec(spec);spec.loader.exec_module(flow)
S,E,solid=flow.S,flow.E,flow.solid
src=S/'aevrynd-female-next-r0014-c-clump-volume-study.blend';proof=json.loads((E/'c-saved-scalp-flow-verification.json').read_text());assert proof['status']=='PASS_TESTED_STATIC_SURFACE_SCOPE' and len(proof['poses'])==5 and flow.route.sha(src)==proof['candidateSha256']
bpy.ops.wm.open_mainfile(filepath=str(src));rig=bpy.data.objects['AFN_R0005_Rig'];solid.stage.set_pose(rig,'neutral');body=bpy.data.objects['AFN_R0008_Body'];body.data.calc_loop_triangles();V,T,tree=solid.data(body);V=np.array(V,dtype=np.float64);T=np.array(T,dtype=np.int32)
assert np.array_equal(T,np.array([t.vertices for t in body.data.loop_triangles],dtype=np.int32))
gpath=S/'aevrynd-female-next-r0014-c-clump-guides.npz';guides=np.load(gpath)['guides'];bindings=[];errors=[]
for i,g in enumerate(guides):
    root=np.array(g[0],dtype=np.float64);hit,n,ti,d=tree.find_nearest(Vector(root));P=V[T[ti]];bc=np.linalg.lstsq(np.column_stack((P[1]-P[0],P[2]-P[0])),np.array(hit)-P[0],rcond=None)[0];w=np.array((1-bc.sum(),*bc));reconstructed=w@P+np.array(n)*.00020;errors.append(float(np.linalg.norm(reconstructed-root)));bindings.append({'guide':i,'bodyVertices':T[ti].tolist(),'barycentric':w.tolist(),'restNormalWorld':list(n),'normalOffsetM':.00020})
assert max(errors)<.000001
gb=S/'aevrynd-female-next-r0014-guide-bindings.json';gb.write_text(json.dumps(bindings,separators=(',',':'))+'\n')
child=S/'aevrynd-female-next-r0014-root-bindings.json';shutil.copy2(E/'root-bindings.json',child);rows=json.loads(child.read_text());cachePath=S/'aevrynd-female-next-r0014-c-hair-data.npz';cache=np.load(cachePath);roots=cache['positions'][cache['offsets'][:-1]];child_errors=[]
assert len(rows)==len(roots)==21086
for root,row in zip(roots,rows):
    ids=np.array(row['bodyVertices']);w=np.array(row['barycentric']);normal=np.array(row['rootNormal']);q=w@V[ids]+normal*.00020;child_errors.append(float(np.linalg.norm(q-root)));assert abs(sum(row['weights'])-1)<1e-10 and all(0<=g<len(guides) for g in row['guides'])
assert max(child_errors)<.000001
head=rig.matrix_world@rig.pose.bones['head'].matrix
files=[src,cachePath,gpath,gb,child]
descriptor={'schema':'aevrynd.groom.authoring.v1','releaseState':'OFFLINE_RESEARCH_SOURCE_ONLY','units':'metres','coordinateSpace':'Neutral model world space; explicit inverse head-bind matrix maps into head-local coordinates.','sourceBlender':src.name,'bodyObject':body.name,'bodyGeometrySha256':solid.geom(body),'bodyTriangleVertexIdsStableAtBind':True,'bodyWorldMatrix':[list(row) for row in body.matrix_world],'headBone':'head','headBindWorldMatrix':[list(row) for row in head],'worldRestToHeadBindLocalMatrix':[list(row) for row in head.inverted()],'guideData':gpath.name,'guideBindings':gb.name,'renderHairData':cachePath.name,'renderHairBindings':child.name,'guideCount':len(guides),'guideCVs':64,'renderFibres':len(roots),'renderPoints':len(cache['positions']),'collisionEnvelopeScope':'Support planes in guide cache use n dot (worldPosition - [0,-0.036,1.475]) <= offset, fitted to neutral body vertices above z 1.30 m; static proxy only. Final acceptance used actual-body capsule tests.','sourceFiles':[{'file':p.name,'sha256':flow.route.sha(p),'bytes':p.stat().st_size} for p in files],'validation':{'guideRootReconstructionMaximumErrorM':max(errors),'childRootReconstructionMaximumErrorM':max(child_errors),'guideIndexWeightChecks':'PASS'},'notImplemented':['Runtime importer/renderer/LOD/performance qualification.','Guide dynamics, deformation-aware root update, continuous collision, self collision and friction.'],'runtimePromotionApproved':False}
dest=S/'aevrynd-female-next-r0014-c-groom.authoring.json';dest.write_text(json.dumps(descriptor,indent=2)+'\n');(E/'engine-authoring-bindings-verification.json').write_text(json.dumps({'descriptor':str(dest),'descriptorSha256':flow.route.sha(dest),'guideRoots':len(guides),'childRoots':len(roots),'maxGuideRootErrorM':max(errors),'maxChildRootErrorM':max(child_errors),'status':'PASS_BIND_POSE_DATA_ONLY','runtimeStatus':'NOT_IMPLEMENTED'},indent=2)+'\n');print('AFN14_GROOM_BINDINGS_PASS',flush=True)
