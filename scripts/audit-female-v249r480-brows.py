import json, math, os
from pathlib import Path
import bpy
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];SOURCE=Path(os.environ.get('AEVRYND_BROW_SOURCE',ROOT/'assets-source/aevrynd-character/aevrynd-female-authoring-v249-mainline-runtime-brows-r480.blend'));REPORT=Path(os.environ.get('AEVRYND_BROW_REPORT',ROOT/'assets-source/aevrynd-character/female-v249-mainline-runtime-brows-r480.collision-audit.json'))
BODY='AevryndFemaleBodyBaseV118';RIG='AevryndFemaleRig';BROWS=('AevryndFemaleBrow_L_R480','AevryndFemaleBrow_R_R480');FRAMES=(1,20,33,61)
def mesh_bvh(obj,dg):
 ev=obj.evaluated_get(dg);mesh=ev.to_mesh();verts=[ev.matrix_world@v.co for v in mesh.vertices];polys=[tuple(p.vertices) for p in mesh.polygons];return ev,mesh,BVHTree.FromPolygons(verts,polys,all_triangles=False),len(verts),len(polys)
def points_world(obj):return [obj.matrix_world@p.co.xyz for s in obj.data.splines for p in s.points]
def roots_world(obj):return [obj.matrix_world@s.points[0].co.xyz for s in obj.data.splines]
def bone_world(rig):return rig.matrix_world@rig.pose.bones['head'].matrix
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;body=bpy.data.objects[BODY];rig=bpy.data.objects[RIG];viol=[];frames={};reference=None
for name in BROWS:
 o=bpy.data.objects.get(name)
 if not o:viol.append({'type':'missing_brow','object':name})
 elif o.parent!=rig or o.parent_type!='BONE' or o.parent_bone!='head':viol.append({'type':'invalid_binding','object':name})
for frame in FRAMES:
 scene.frame_set(frame);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();bev,bmesh,body_bvh,bv,bp=mesh_bvh(body,dg);inv=bone_world(rig).inverted();frame_data={};current={}
 for name in BROWS:
  obj=bpy.data.objects.get(name)
  if not obj:continue
  vals=[]
  for root in roots_world(obj):
   nearest,normal,_idx,_distance=body_bvh.find_nearest(root);vals.append((root-nearest).dot(normal))
  e,m,brow_bvh,vcount,pcount=mesh_bvh(obj,dg);overlaps=len(body_bvh.overlap(brow_bvh));e.to_mesh_clear();current[name]=[tuple(inv@p) for p in points_world(obj)]
  nonfinite=sum(not all(math.isfinite(c) for c in p) for p in current[name]);penetrating=sum(v<0.00005 for v in vals)
  frame_data[name]={'roots':len(vals),'minimumSignedRootClearanceMm':min(vals)*1000,'maximumSignedRootClearanceMm':max(vals)*1000,'rootsBelow0p05mm':penetrating,'bodyBrowTriangleOverlapPairs':overlaps,'evaluatedVertices':vcount,'evaluatedPolygons':pcount,'nonFiniteControlPoints':nonfinite}
  if penetrating:viol.append({'frame':frame,'object':name,'type':'root_clearance_below_0p05mm','count':penetrating})
  if overlaps:viol.append({'frame':frame,'object':name,'type':'body_brow_overlap','pairs':overlaps})
  if nonfinite:viol.append({'frame':frame,'object':name,'type':'nonfinite','count':nonfinite})
 if reference is None:reference=current;drift={n:0 for n in current}
 else:
  drift={n:max((math.dist(a,b) for a,b in zip(reference[n],pts)),default=0) for n,pts in current.items()}
  for n,d in drift.items():
   if d>1e-6:viol.append({'frame':frame,'object':n,'type':'head_space_drift','maximumMm':d*1000})
 frames[str(frame)]={'brows':frame_data,'maximumHeadSpaceDriftMm':{n:d*1000 for n,d in drift.items()}};bev.to_mesh_clear()
scene.frame_set(1);report={'source':str(SOURCE),'frames':frames,'testedFrames':list(FRAMES),'violations':viol,'status':'PASS' if not viol else 'FAIL'};REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8');print('AEVRYND_R480_BROW_AUDIT='+json.dumps(report,sort_keys=True))
