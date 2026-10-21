"""Retain full artist shape and repair neck tangents from actual source normals.
One fixed G1 construction; no free tangent weights, plane/radius/step sweep.
"""
from pathlib import Path
import bpy,bmesh,numpy as np,json,time,importlib.util
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0126-individual-head-foundation';SRC=S/'r0126-source/aevrynd-female-next-r0126-a2-source-material-neck.blend';OUT=S/'r0126-source/aevrynd-female-next-r0126-a3-native-neck-tangents.blend'
sp=importlib.util.spec_from_file_location('r126g1',Path(__file__).with_name('build-female-next-r0126-individual-head.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;b.u.v.E=E
def main():
 tick=time.time();assert not OUT.exists();build=json.loads((E/'a2-build-summary.json').read_text('utf-8'));assert a.a.sha(SRC)==build['sha256'];bpy.ops.wm.open_mainfile(filepath=str(SRC));ob=bpy.data.objects[build['actualSkinObject']];_,original,T=b.u.b.geom(ob);original=original.copy();T=T.copy();patchIndex=next(i for i,m in enumerate(ob.data.materials) if m and m.name=='AFN126_EXACT_DUAL_SOURCE_NECK_MATERIAL');z0=build['bodyCutWorldZ'];z1=build['headCutWorldZ'];dz=z1-z0;lineage=np.load(E/'individual-head-neck-lineage.npz');rings=lineage['bridgePoints'].reshape(5,-1,3);bm=bmesh.new();bm.from_mesh(ob.data);bm.normal_update();verts=list(bm.verts);coordinates=np.array([v.co[:] for v in verts]);mapped=[]
 for row in rings:
  indices=[]
  for point in row:
   dist=np.linalg.norm(coordinates-point,axis=1);i=int(np.argmin(dist));assert dist[i]<3e-7;indices.append(i)
  mapped.append(indices)
 tangents=[];normals=[]
 for row in [mapped[0],mapped[-1]]:
  ns=[];ts=[]
  for i in row:
   faces=[f for f in verts[i].link_faces if f.material_index!=patchIndex];assert faces;n=np.sum([np.array(f.normal)*f.calc_area() for f in faces],axis=0);n/=np.linalg.norm(n);den=np.dot(n[:2],n[:2]);assert den>1e-4;t=np.r_[-n[2]*n[:2]/den,1.];ns.append(n);ts.append(t)
  normals.append(np.array(ns));tangents.append(np.array(ts))
 P0=rings[0];P1=rings[-1];before=rings.copy();after=rings.copy()
 for j,t in enumerate([.25,.5,.75],1):
  points=(2*t**3-3*t*t+1)*P0+(t**3-2*t*t+t)*dz*tangents[0]+(-2*t**3+3*t*t)*P1+(t**3-t*t)*dz*tangents[1];assert np.isfinite(points).all() and abs(points[:,2]-(z0+dz*t)).max()<2e-7;after[j]=points
  for i,p in zip(mapped[j],points):verts[i].co=p
 bm.to_mesh(ob.data);bm.free();ob.data.update();bpy.context.view_layer.update();_,W,TT=b.u.b.geom(ob);W=W.copy();assert np.array_equal(T,TT);changed=np.linalg.norm(W-original,axis=1);ids=np.flatnonzero(changed>1e-7);assert len(ids)>0 and changed.max()<.025;assert np.all((W[ids,2]>z0)&(W[ids,2]<z1));np.savez_compressed(E/'native-neck-tangent-lineage.npz',originalRuledRings=before,reconstructedRings=after,actualSourceBoundaryNormals=np.array(normals),actualSourceDzTangents=np.array(tangents),skinChangedVertexIDs=ids,skinDeltaWorld=(W-original).astype('f4'));bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False);a.save('a3-build-summary.json',build|{'source':str(SRC),'sourceSha256':a.a.sha(SRC),'output':str(OUT),'sha256':a.a.sha(OUT),'bytes':OUT.stat().st_size,'repair':'One neck-only cubic reconstruction from actual native-body and artist-neck source boundary face normals. Fixed endpoint positions and dz-normal tangents, no fitting/sweep. All head/body outside the junction, all triangles/UV/materials/source parts unchanged.','sourceBoundaryNormalTangencyResidual':float(max(np.abs((normals[i]*tangents[i]).sum(1)).max() for i in [0,1])),'maximumNeckInteriorMovementM':float(changed.max()),'neckInteriorVerticesChanged':len(ids),'allOutsideJunctionPositionsAndAllTrianglesExact':True,'finiteSelfAndContinuousContactStillUnaccepted':True,'secondsBeforePreview':time.time()-tick});rows=[]
 for view in ['face','body-face','profile','oblique','back']:
  rows.append(b.u.v.image('a3-native-neck-tangents',view));a.save('a3-view-controls.json',rows)
 print('R126_COMPLETE_NATIVE_NECK_TANGENT_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
