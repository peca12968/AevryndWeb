"""One bounded actual-face localization; no repair, sweep or new save."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
C=Path('C:/Users/USER/AevryndCharacterWorkspace-r0158');E=C/'evidence/character-female-next/r0160-ocular-surface-wall';sp=importlib.util.spec_from_file_location('r160face',C/'scripts/character-next/build-female-next-r0160-ocular-surface-wall.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);a=m.a;h=m.h;b=json.loads((E/'a-build-summary.json').read_text());q=json.loads((E/'closed-actual-ocular-contact.json').read_text());bpy.ops.wm.open_mainfile(filepath=b['output']);bpy.context.scene.frame_set(11);bpy.context.view_layer.update();ob=bpy.data.objects[b['actualSkin']];V,T=a.geometry(ob);reports=[]
for case in q['cases']:
 W,F=a.geometry(bpy.data.objects[case['object']]);tree=BVHTree.FromPolygons([Vector(v) for v in W],F.tolist(),all_triangles=True)
 for rec in case['firstIndependentWitnesses']:
  ids=T[rec['actualSkinTriangle']];P=V[ids];edges=np.linalg.norm(P[[1,2,0]]-P,axis=1);nearest=[]
  for p in P:
   hit=tree.find_nearest(Vector(p));nearest.append({'distanceM':float(hit[3]),'nearestSurfacePoint':tuple(hit[0]),'normalDotOffsetM':float((Vector(p)-hit[0]).dot(hit[1])),'normalSignNotCertifiedContainment':True})
  reports.append({'pair':case['object'],'actualTriangle':rec['actualSkinTriangle'],'actualPolygon':rec['actualPolygon'],'vertices':ids,'worldTriangle':P,'edgeLengthsM':edges,'vertexNearestUnsigned':nearest,'properInteriorCrossingAlreadyProven':True})
h.save('actual-failed-face-localization.json',{'frame':11,'sourceSha256':b['sha256'],'reports':reports,'interpretation':'This is actual failed face geometry and nearest unsigned point data. Per-vertex ray hit/nearest distance cannot certify entire triangles, signed containment or finite thickness. No cause invented from this sample.','newSourceOrRepairPerformed':False});print('R160_ACTUAL_FAILED_TRIANGLE_LOCALIZATION_DONE',flush=True)
