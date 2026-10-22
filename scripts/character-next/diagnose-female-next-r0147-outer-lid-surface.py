"""One actual surface attribution and normal/base-colour isolation, no saved candidate."""
from pathlib import Path
import bpy,numpy as np,json,time,importlib.util
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0147-outer-lid-surface';SRC=R/'engine/assets/characters/female-next/source/r0146-source/aevrynd-female-next-r0146-a-connected-palpebral-lining.blend'
sp=importlib.util.spec_from_file_location('r147diagnosticbase',Path(__file__).with_name('build-female-next-r0146-connected-lining.py'));h=importlib.util.module_from_spec(sp);sp.loader.exec_module(h);a=h.a;a.b.u.v.E=E
def save(n,x):h.E=E;h.save(n,x)
def main():
 tick=time.time();digest=a.a.sha(SRC);bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(9);bpy.context.view_layer.update();skin=bpy.data.objects[h.c.h.SKIN];rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];protected=a.a.protected();W,T=a.geometry(skin);dg=bpy.context.evaluated_depsgraph_get();ob=skin.evaluated_get(dg);mesh=ob.to_mesh();mesh.calc_loop_triangles();norm=h.values(mesh.corner_normals,'vector',len(mesh.loops),3);triLoop=h.values(mesh.loop_triangles,'loops',len(mesh.loop_triangles),3,'i4');triPoly=h.values(mesh.loop_triangles,'polygon_index',len(mesh.loop_triangles),dtype='i4');uv=h.values(mesh.uv_layers.active.data,'uv',len(mesh.loops),2);roles=h.values(mesh.attributes['AFN146_POSTERIOR_LINING_SIDE'].data,'value',len(mesh.polygons),dtype='i4')
 control=json.loads((E.parent/'r0146-connected-palpebral-lining/a-view-controls.json').read_text('utf-8'))[0];cam=scene.camera;cam.matrix_world=Matrix(control['camera']);cam.data.lens=control['lensMM'];scene.render.resolution_x=scene.render.resolution_y=640;scene.render.resolution_percentage=100;corners=cam.data.view_frame(scene=scene);xs=[v.x for v in corners];ys=[v.y for v in corners];z=corners[0].z;origin=cam.matrix_world.translation;rot=cam.matrix_world.to_3x3();tree=BVHTree.FromPolygons([Vector(p) for p in W],T.tolist(),all_triangles=True);samples=[]
 for x in [237,247,257,368,378,388,398]:
  for y in [238,242,246,250,254]:
   local=Vector((min(xs)+(x+.5)/640*(max(xs)-min(xs)),max(ys)-(y+.5)/640*(max(ys)-min(ys)),z));direction=(rot@local).normalized();hit=tree.ray_cast(origin,direction)
   if hit[0] is None:continue
   fi=hit[2];p=np.array(hit[0]);closest,bc=h.c.h.actual_triangle_anchor(p,W[T[fi]]);n=bc@norm[triLoop[fi]];n/=np.linalg.norm(n);gn=np.array(hit[1]);poly=mesh.polygons[int(triPoly[fi])];material=mesh.materials[poly.material_index];samples.append({'pixel':[x,y],'triangle':int(fi),'polygon':int(triPoly[fi]),'role':int(roles[triPoly[fi]]),'material':material.name,'uv':bc@uv[triLoop[fi]],'customInterpolatedNormal':n,'geometricNormal':gn,'normalDotGeometric':float(n@gn),'normalDotCamera':float(n@(-np.array(direction))),'world':p})
 graphs=[]
 for mat in mesh.materials:
  if mat and mat.use_nodes:graphs.append({'name':mat.name,'nodes':[{'name':n.name,'type':n.bl_idname,'image':n.image.filepath if n.type=='TEX_IMAGE' and n.image else None} for n in mat.node_tree.nodes],'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in mat.node_tree.links]})
 save('actual-closed-lid-surface-attribution.json',{'source':str(SRC),'sourceSha256':digest,'actualBlink':{s:float(rig[p]) for s,p in h.PROPS.items()},'sampledActualSkinSurfacePixels':samples,'materialGraphs':graphs,'normalSetterDoc':skin.data.normals_split_custom_set.__doc__,'diagnosticOnlyNotAppearanceAdoption':True})
 ob.to_mesh_clear();rawNormals=h.values(skin.data.corner_normals,'vector',len(skin.data.loops),3);skin.data.normals_split_custom_set(np.zeros((len(skin.data.loops),3)).tolist());skin.data.update();bpy.context.view_layer.update();auto=a.b.u.v.image('diagnostic-auto-normals-closed','face');save('diagnostic-auto-normals-view.json',auto);skin.data.normals_split_custom_set(rawNormals.tolist());skin.data.update();bpy.context.view_layer.update()
 changes=[]
 for mat in skin.data.materials:
  if not mat or not mat.use_nodes:continue
  nt=mat.node_tree;out=next((n for n in nt.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output),None);bs=next((n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'),None)
  if out is None or bs is None:continue
  old=[(l.from_socket,l.to_socket) for l in out.inputs['Surface'].links];em=nt.nodes.new('ShaderNodeEmission');color=bs.inputs['Base Color'];em.inputs['Color'].default_value=color.default_value
  if color.is_linked:nt.links.new(color.links[0].from_socket,em.inputs['Color'])
  nt.links.new(em.outputs[0],out.inputs['Surface']);changes.append((nt,out,em,old))
 base=a.b.u.v.image('diagnostic-basecolor-closed','face');save('diagnostic-basecolor-view.json',base)
 for nt,out,em,old in changes:
  nt.nodes.remove(em)
  for fr,to in old:nt.links.new(fr,to)
 scene.frame_set(1);bpy.context.view_layer.update();assert a.a.protected()==protected and a.a.sha(SRC)==digest
 print('R147_ACTUAL_CLOSED_LID_ATTRIBUTION_NORMAL_AND_BASECOLOR_DIAGNOSTIC_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
