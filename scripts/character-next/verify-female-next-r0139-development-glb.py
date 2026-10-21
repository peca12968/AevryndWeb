"""Check every serialized surface vertex/triangle and 49 baked poses vs Blender."""
from pathlib import Path
import json,hashlib,datetime,importlib.util,time
import numpy as np
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0139-native-lid-follow';sp=importlib.util.spec_from_file_location('aevryndgltf',R/'engine/character/gltf_skinning_reference.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 tick=time.time();export=json.loads((E/'development-export-summary.json').read_text('utf-8'));reference=json.loads((E/'development-native-pose-reference.json').read_text('utf-8'));data=np.load(E/'development-native-pose-reference.npz');path=Path(export['output']);assert sha(path)==export['sha256'];g=m.GLB(path);doc=g.g;assert len(doc.get('animations',[]))==1;meshNodes={n['name']:i for i,n in enumerate(doc['nodes']) if 'mesh' in n};assert set(meshNodes)==set(reference['meshes']);prepared=[];coverage={n:set() for n in meshNodes};triangles={n:[] for n in meshNodes}
 for name,ni in meshNodes.items():
  prefix=reference['meshes'][name]['prefix'];base=data[prefix+'_base'];idsAffected=data[prefix+'_affected']
  for p in doc['meshes'][doc['nodes'][ni]['mesh']]['primitives']:
   assert p.get('mode',4)==4;raw=g.accessor(p['attributes'][reference['sourceVertexAttribute']]).ravel();assert np.array_equal(raw,np.rint(raw));ids=raw.astype('i4');assert ids.min()>=0 and ids.max()<len(base);indices=g.accessor(p['indices']).astype('i4').ravel();coverage[name].update(ids[indices].tolist());triangles[name].append(np.sort(ids[indices.reshape(-1,3)],axis=1));prepared.append((name,ni,p,ids))
 for n,r in reference['meshes'].items():
  T=data[r['prefix']+'_triangles'];actual=np.concatenate(triangles[n]);assert coverage[n]==set(np.unique(T).tolist()) and len(actual)==len(T);expected=np.sort(T,axis=1);assert np.array_equal(actual[np.lexsort(actual.T[::-1])],expected[np.lexsort(expected.T[::-1])]),n
 maximum={n:0. for n in meshNodes};rows=[]
 for frame in reference['frames']:
  world=g.world_matrices((frame-1)/reference['fps']);expected={}
  for n,r in reference['meshes'].items():
   prefix=r['prefix'];P=data[prefix+'_base'].copy();P[data[prefix+'_affected']]=data[prefix+'_poses'][frame-1];expected[n]=P
  err={n:0. for n in meshNodes}
  for name,ni,p,ids in prepared:
   W=g.primitive_world(ni,p,world);zup=np.c_[W[:,0],-W[:,2],W[:,1]];e=float(np.linalg.norm(zup-expected[name][ids],axis=1).max());err[name]=max(err[name],e);maximum[name]=max(maximum[name],e)
  rows.append({'nativeFrame':frame,'GLTFTimeSeconds':(frame-1)/24,'actualGLTFCPUWorldVertexMaxErrorM':err})
 result={'verifiedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source':export['source'],'sourceSHA256':export['sourceSHA256'],'developmentGLB':str(path),'developmentGLBSHA256':export['sha256'],'developmentGLBBytes':export['bytes'],'allActualSurfaceVerticesAndTrianglesCoveredBySourceIDs':True,'all49DiscreteNativePoses':rows,'maxActualWorldVertexErrorM':maximum,'numericExportBoundM':2e-6,'exportNumericalBoundNotContactTolerance':True,'actualNativeLidBonesBakedAsGLTFAnimationNodes':[n['name'] for n in doc['nodes'] if n.get('name','').startswith('AFN139_')],'maximumErrorWithinDeclaredNumericBound':max(maximum.values())<2e-6,'runtimeBlenderDriversRequired':False,'actualEngineRendererMaterialCollisionLODOrPerformanceAccepted':False,'finiteOrContinuousContactAcceptance':False,'materialExportIsUnacceptedApproximationUntilActualAevryndRender':True,'geometryAnimationMethod':'Independent glTF accessor/TRS/slerp/world hierarchy/inverse-bind linear blend reconstruction, every serialized primitive vertex mapped to its original Blender source vertex; all triangle multiplicities and 49 real source evaluated poses checked.','seconds':time.time()-tick};(E/'development-glb-readback.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');assert result['maximumErrorWithinDeclaredNumericBound'],maximum;assert len(result['actualNativeLidBonesBakedAsGLTFAnimationNodes'])>=5;assert sha(export['source'])==export['sourceSHA256'];print('R139_ALL_ACTUAL_GLB_VERTICES_TRIANGLES_AND49_NATIVE_POSES_VERIFIED',max(maximum.values()),time.time()-tick)
if __name__=='__main__':main()
