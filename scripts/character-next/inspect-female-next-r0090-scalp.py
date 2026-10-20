"""Bounded actual target scalp extraction for intrinsic-route authoring.
No donor scalp mapping or global hair shape construction, no saved model.
"""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,hashlib
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(r'D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0090-native-scalp-groom';SRC=R/'engine/assets/characters/female-next/source/aevrynd-female-next-r0088-b-supported-lid-aperture.blend'
sp=importlib.util.spec_from_file_location('r90scalp_source',Path(__file__).with_name('build-female-next-r0081-editable-curly.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);assert hashlib.sha256(SRC.read_bytes()).hexdigest()=='72435890a03cab26ff2f3e238060daf2b2cf797f85543d8fd6182583cc1101a7';bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1)
for o in bpy.data.objects:
 if o.type=='CURVES':
  for md in o.modifiers:md.show_viewport=False
body=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING']
for md in body.modifiers:
 if md.type=='SUBSURF':md.levels=md.render_levels
bpy.context.view_layer.update();row=m.rig.k.mesh(body);V=row['V'];T=row['T'];C=V[T].mean(1);keep=(C[:,2]>1.38)&(np.abs(C[:,0])<.14);ix=np.flatnonzero(keep);verts,inv=np.unique(T[ix],return_inverse=True);P=V[verts];F=inv.reshape(-1,3);tree=BVHTree.FromPolygons(P.tolist(),F.tolist(),all_triangles=True);cap=bpy.data.objects['AFN81_NEUTRAL_EDITABLE_GROWTH_SURFACE'];G=m.q.arr(cap.data.vertices,'co',len(cap.data.vertices),3);A=np.array(cap.matrix_world);G=G@A[:3,:3].T+A[:3,3];gaps=[]
for p in G:gaps.append(tree.find_nearest(Vector(p))[3])
profiles=[]
for z in np.arange(1.40,1.611,.01):
 Q=P[abs(P[:,2]-z)<.0015]
 if len(Q):profiles.append({'z':float(z),'count':len(Q),'min':Q.min(0).tolist(),'max':Q.max(0).tolist()})
np.savez_compressed(E/'actual-head-surface.npz',world=P,triangles=F,bodyTriangleIDs=ix,nativeTriangleFace=row['nativeTriangleFace'][ix],materialIndex=row['mi'][ix],bodyVertexIDs=verts)
result={'source':str(SRC),'sourceSha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'bodyObject':body.name,'bodyRenderSubdivisionLevels':[md.levels for md in body.modifiers if md.type=='SUBSURF'],'headSubsetWorldBounds':[P.min(0).tolist(),P.max(0).tolist()],'actualSkinTopWorldM':float(P[:,2].max()),'oldCapTopWorldM':float(G[:,2].max()),'oldCapUnsignedDistanceToHeadQuantilesM':np.quantile(gaps,[0,.5,.9,1]).tolist(),'profiles':profiles,'headSubsetVertices':len(P),'headSubsetTriangles':len(F),'meaning':'Actual render-level closed-body head surface for authoring. Unsigned scalp distances and bounds do not prove follicle attachment, hair occupancy or cause of all gaps. No model output or contact certificate.'};(E/'actual-head-sections.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('R90_TARGET_HEAD',len(P),len(F),float(P[:,2].max()),float(G[:,2].max()),flush=True)
