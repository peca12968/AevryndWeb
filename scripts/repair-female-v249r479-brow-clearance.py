import json
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1];ASSETS=ROOT/'assets-source/aevrynd-character';SOURCE=ASSETS/'aevrynd-female-authoring-v249-mainline-refined-anatomical-brows-r478.blend';OUTPUT=ASSETS/'aevrynd-female-authoring-v249-mainline-clearance-fitted-brows-r479.blend';REPORT=ASSETS/'female-v249-mainline-clearance-fitted-brows-r479.build-report.json';REVIEW=ASSETS/'reviews/v249r479-clearance-fitted-brows';BODY='AevryndFemaleBodyBaseV118';OLD=('AevryndFemaleBrow_L_R478','AevryndFemaleBrow_R_R478')
def look_at(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
def body_bvh(body):
 dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);mesh=ev.to_mesh();verts=[ev.matrix_world@v.co for v in mesh.vertices];polys=[tuple(p.vertices) for p in mesh.polygons];return ev,mesh,BVHTree.FromPolygons(verts,polys,all_triangles=False)
def render(scene,cam,frame,name,location,target,lens,size):
 scene.frame_set(frame);bpy.context.view_layer.update();cam.location=location;cam.data.lens=lens;look_at(cam,target);scene.render.resolution_x,scene.render.resolution_y=size;scene.render.filepath=str(REVIEW/f'{name}.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.preferences.filepaths.save_version=0;scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();body=bpy.data.objects[BODY];ev,mesh,bvh=body_bvh(body);target=.00013;repairs={}
for old_name in OLD:
 obj=bpy.data.objects[old_name];moved=0;max_move=0;before=[];after=[];inv=obj.matrix_world.inverted()
 for spline in obj.data.splines:
  for point in spline.points:
   world=obj.matrix_world@point.co.xyz;nearest,normal,_idx,_dist=bvh.find_nearest(world);signed=(world-nearest).dot(normal);before.append(signed)
   if signed<target:
    delta=target-signed;world=world+normal*delta;point.co=(*(inv@world),1);moved+=1;max_move=max(max_move,delta)
   nearest2,normal2,_idx2,_dist2=bvh.find_nearest(obj.matrix_world@point.co.xyz);after.append(((obj.matrix_world@point.co.xyz)-nearest2).dot(normal2))
 side='L' if '_L_' in old_name else 'R';obj.name=f'AevryndFemaleBrow_{side}_R479';obj.data.name=f'AevryndFemaleBrow_{side}_R479_Geometry';obj['aevrynd_revision']='v249r479';obj['aevrynd_clearance_method']='all curve controls projected to evaluated body normal at frame 1';repairs[obj.name]={'controlPoints':len(before),'movedControlPoints':moved,'minimumSignedBeforeMm':min(before)*1000,'minimumSignedAfterMm':min(after)*1000,'maximumMoveMm':max_move*1000}
ev.to_mesh_clear();scene['aevrynd_mainline_revision']='v249r479-clearance-fitted-brows';scene['aevrynd_mainline_parent']=SOURCE.name;scene['aevrynd_release_state']='BROW_CLEARANCE_VISUAL_AND_COLLISION_REVIEW_PENDING';REVIEW.mkdir(parents=True,exist_ok=True);scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';cam=bpy.data.objects.get('Aevrynd R249 Review Camera') or bpy.data.objects['Aevrynd Review Camera'];scene.camera=cam
views=((1,'01-face-front-f01',(0,-.56,1.585),(0,-.06,1.585),108,(1100,1100)),(1,'02-eyes-f01',(0,-.45,1.615),(0,-.125,1.615),118,(1300,750)),(1,'03-three-quarter-f01',(.40,-.57,1.58),(0,-.03,1.56),92,(1000,1000)),(20,'04-face-front-f20',(0,-.56,1.585),(0,-.06,1.585),108,(1100,1100)),(20,'05-three-quarter-f20',(.40,-.57,1.58),(0,-.03,1.56),92,(1000,1000)))
for v in views:render(scene,cam,*v)
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT));report={'source':str(SOURCE),'output':str(OUTPUT),'targetControlPointClearanceMm':target*1000,'repairs':repairs,'geometryChangedOutsideBrows':False,'reviewDirectory':str(REVIEW),'status':'STRICT_VISUAL_AND_COLLISION_REVIEW_REQUIRED'};REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8');print('AEVRYND_R479_BROW_CLEARANCE='+json.dumps(report,sort_keys=True))
