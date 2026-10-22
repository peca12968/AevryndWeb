from pathlib import Path
import bpy,numpy as np,json,importlib.util
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0156-anatomical-blink'
sp=importlib.util.spec_from_file_location('r156visible',Path(__file__).with_name('build-female-next-r0155-margin-blink.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a
b=json.loads((E.parent/'r0155-native-blink/b-build-summary.json').read_text());bpy.ops.wm.open_mainfile(filepath=b['output']);s=bpy.context.scene;s.frame_set(11);bpy.context.view_layer.update();a.b.u.v.m.rig.k.b.camera('face');s.camera.data.lens=85;s.render.resolution_x=s.render.resolution_y=640;bpy.context.view_layer.update();skin=bpy.data.objects[b['actualSkin']];V,T=a.geometry(skin);tree=BVHTree.FromPolygons([Vector(p) for p in V],T.tolist(),all_triangles=True);skin.data.calc_loop_triangles();origin=s.camera.matrix_world.translation;rot=s.camera.matrix_world.to_quaternion();trees={n:BVHTree.FromPolygons([Vector(x) for x in a.geometry(bpy.data.objects[n])[0]],a.geometry(bpy.data.objects[n])[1].tolist(),all_triangles=True) for n in a.FIXED[2:4]+a.MOVING};rows=[];groups={}
for x0,x1 in [(200,300),(340,440)]:
 for y in range(224,268,4):
  for x in range(x0,x1,4):
   direction=rot@Vector(((2*(x+.5)/640-1)*.036/(2*.085),(1-2*(y+.5)/640)*.036/(2*.085),-1));direction.normalize();hit=tree.ray_cast(origin,direction,2.)
   if hit[0] is None:continue
   fi=int(hit[2]);poly=skin.data.polygons[skin.data.loop_triangles[fi].polygon_index];mat=skin.material_slots[poly.material_index].name;groups[mat]=groups.get(mat,0)+1;other=[]
   for n,t in trees.items():
    q=t.ray_cast(origin,direction,2.)
    if q[0] is not None and q[3]<hit[3]:other.append({'name':n,'beforeSkinM':float(hit[3]-q[3])})
   if mat=='AFN57_CANONICAL_IRIS' or (x in [240,260,360,380] and y in [236,240,244,248,252]):rows.append({'pixel':[x,y],'skinTriangle':fi,'skinPolygon':poly.index,'polygonVertices':len(poly.vertices),'material':mat,'world':list(hit[0]),'otherRawLayersBeforeSkin':other})
out={'groupsOfFirstSkinRayHit':groups,'selectedPixelWitnesses':rows,'rayScope':'Actual opaque Skin surface hit correspondence only. Raw lash/wet/eye triangles before Skin recorded, never inferred as opaque. No alpha occupancy/render-depsgraph or final visible-pixel causality proof.','allSourceUnmodified':True}
(E/'actual-closed-lid-surface-correspondence.json').write_bytes((json.dumps(out,indent=2)+'\n').encode());print('R156_ACTUAL_LID_RAY_CORRESPONDENCE_DONE',json.dumps(groups),flush=True)
