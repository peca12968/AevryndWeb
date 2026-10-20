"""Third and final r89 construction: publisher-authored complete braid groom.
Different native guides, parting geometry and braid program, not bob tuning.
Original source cap correspondence is reused explicitly. Rebuild every actual
generated root binding; no natural-motion, finite-contact or runtime claim.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
R=Path(r'D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0089-posterior-growth'
SRC=S/'aevrynd-female-next-r0088-b-supported-lid-aperture.blend';DEMO=R/'Reference/character/blender-bystedt-hair-cc-by-sa/hair_nodes-female_hair_styles.blend';OUT=S/'aevrynd-female-next-r0089-c-authored-braid-groom.blend'
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=module('r89braid_source','build-female-next-r0081-editable-curly.py');q=m.q;v=module('r89braid_view','render-female-next-r0081-retained-study.py');v.E=E
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def attr(d,n,kind,P):
 a=d.attributes.new(n,kind,'POINT');a.data.foreach_set('vector' if kind=='FLOAT_VECTOR' else 'value',np.asarray(P).ravel())
def main():
 tick=time.time();assert not OUT.exists() and sha(SRC)=='72435890a03cab26ff2f3e238060daf2b2cf797f85543d8fd6182583cc1101a7';assert sha(DEMO)=='1ad6202095c1793678fee7d69a7e9f8b5fdb6e5c293d300eb1062d2d437e8d48';bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();old=bpy.data.objects['AFN81_EDITABLE_CURLY_GUIDES'];oldCap=bpy.data.objects['AFN81_NEUTRAL_EDITABLE_GROWTH_SURFACE'];A=old.matrix_world.copy();AA=np.array(A);mats={x.name:m.rig.k.f.v.v32.material_signature(x) for x in bpy.data.materials if x.use_nodes};lights=m.m.q.lights()
 with bpy.data.libraries.load(str(DEMO),link=False) as (src,dst):dst.objects=['braided hair','Braids growth mesh','long hair growth mesh']
 o,part,longCap=dst.objects;G0=q.arr(longCap.data.vertices,'co',len(longCap.data.vertices),3).astype('f8');stored=q.arr(oldCap.data.attributes['AFN68_OriginalGrowthPosition'].data,'vector',len(G0),3);assert np.array_equal(G0,stored);G1=q.arr(oldCap.data.vertices,'co',len(oldCap.data.vertices),3).astype('f8');oldCap.data.calc_loop_triangles();T=np.array([t.vertices[:] for t in oldCap.data.loop_triangles]);tree=BVHTree.FromPolygons(G0.tolist(),T.tolist(),all_triangles=True)
 def mapping(P):
  Q=P.copy();fids=[];bary=[];gaps=[]
  for i,p in enumerate(P):
   co,_,face,gap=tree.find_nearest(Vector(p));assert co is not None and gap<.06,(i,gap);bc=m.rig.base.bary(np.array(co),G0[T[face]]);rot=m.rig.base.frame(G1[T[face]])@m.rig.base.frame(G0[T[face]]).T;Q[i]=bc@G1[T[face]]+rot@(p-np.array(co));fids.append(face);bary.append(bc);gaps.append(gap)
  return Q,np.array(fids),np.array(bary),np.array(gaps)
 growth=oldCap.copy();growth.data=oldCap.data.copy();growth.name='AFN89_BRAID_ACTUAL_CAP';s.collection.objects.link(growth);growth.hide_render=True;growth.hide_set(True)
 originalPart=q.arr(part.data.vertices,'co',len(part.data.vertices),3).astype('f8');newPart,partFace,partBary,partGap=mapping(originalPart);part.data=part.data.copy();part.data.vertices.foreach_set('co',newPart.astype('f4').ravel());part.matrix_world=A.copy();part.name='AFN89_BRAID_PARTING_EDGES';s.collection.objects.link(part);part.hide_render=True;part.hide_set(True)
 P=q.arr(o.data.position_data,'vector',len(o.data.position_data),3).astype('f8');counts=np.array([c.points_length for c in o.data.curves]);starts=np.r_[0,np.cumsum(counts)[:-1]];Q=P.copy();rootFaces=[];rootBary=[];rootGaps=[]
 for st,n in zip(starts,counts):
  co,_,face,gap=tree.find_nearest(Vector(P[st]));assert gap<.06;bc=m.rig.base.bary(np.array(co),G0[T[face]]);rot=m.rig.base.frame(G1[T[face]])@m.rig.base.frame(G0[T[face]]).T;Q[st:st+n]=(P[st:st+n]-P[st])@rot.T+bc@G1[T[face]];rootFaces.append(face);rootBary.append(bc);rootGaps.append(gap)
 o.data=o.data.copy();o.data.position_data.foreach_set('vector',Q.astype('f4').ravel());o.parent=None;o.matrix_world=A.copy();o.name='AFN89_PUBLISHER_AUTHORED_BRAID_GUIDES';o.data.surface=growth;s.collection.objects.link(o);o.hide_render=False;o.hide_set(False);changes=[]
 for md in o.modifiers:
  if md.type!='NODES' or not md.node_group:continue
  if md.node_group.name.startswith('Surface Deform'):md.show_viewport=md.show_render=False;continue
  md.node_group=md.node_group.copy();md.node_group.name='AFN89_PUBLISHER_COMPLETE_BRAID_PROGRAM'
  for node in md.node_group.nodes:
   for socket in node.inputs:
    if socket.type!='OBJECT':continue
    if socket.default_value==longCap:socket.default_value=growth;changes.append([node.name,socket.name,'actual_cap'])
    elif socket.default_value==part:changes.append([node.name,socket.name,'mapped_parting'])
 o.data.materials.clear();o.data.materials.append(bpy.data.materials['Brown hair']);old.hide_render=True;old.hide_set(True);bpy.context.view_layer.update();raw=q.hair(o).copy();ed=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;rc=np.array([c.points_length for c in ed.curves]);rs=np.r_[0,np.cumsum(rc)[:-1]];radii=q.arr(ed.attributes['radius'].data,'value',len(raw)).copy();assert len(rc)<100000 and len(raw)<5000000 and np.isfinite(raw).all();body=m.rig.k.mesh(bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING']);bt=BVHTree.FromPolygons(body['V'].tolist(),body['T'].tolist(),all_triangles=True);ids=[];BC=[];anchors=[];gap=[]
 for root in raw[rs]:
  co,_,face,distance=bt.find_nearest(Vector(root));ix=body['T'][face];bc=m.rig.base.bary(np.array(co),body['V'][ix]);ids.append(ix);BC.append(bc);anchors.append(bc@body['V'][ix]);gap.append(distance)
 ids=np.array(ids,'i4');BC=np.array(BC,'f4');anchors=np.array(anchors);tt,bb,nn=m.rig.frames(body['V'][ids]);kd=KDTree(len(body['V']))
 for i,p in enumerate(body['V']):kd.insert(Vector(p),i)
 kd.balance();F=np.array([[kd.find(Vector(target))[1] for target in (p-.01*t,p+.01*t,p+.01*b)] for p,t,b in zip(anchors,tt,bb)],'i4');area=np.linalg.norm(np.cross(body['V'][F[:,1]]-body['V'][F[:,0]],body['V'][F[:,2]]-body['V'][F[:,0]]),axis=1);assert area.min()>1e-6
 table=bpy.data.meshes.new('AFN89_BRAID_ACTUAL_ROOT_BINDING_DATA');table.vertices.add(len(rc));table.vertices.foreach_set('co',np.zeros(len(rc)*3,'f4'));table.update()
 for j in range(3):attr(table,'AFN69_BodyVertex'+str(j),'INT',ids[:,j]);attr(table,'AFN81_FrameVertex'+str(j),'INT',F[:,j])
 for name,value in [('Barycentric',BC),('RestAnchor',anchors),('RestTangent',tt),('RestBinormal',bb),('RestNormal',nn)]:attr(table,'AFN69_'+name,'FLOAT_VECTOR',np.asarray(value,'f4'))
 ref=bpy.data.objects.new('AFN89_BRAID_ACTUAL_ROOT_BINDING_TABLE',table);s.collection.objects.link(ref);ref.hide_render=True;ref.hide_set(True);wrapper=old.modifiers['AFN81_ACTUAL_RENDER_ROOT_TABLE'].node_group.copy();wrapper.name='AFN89_ASSIGN_BRAID_ACTUAL_RENDER_ROOTS'
 for node in wrapper.nodes:
  if node.bl_idname=='GeometryNodeObjectInfo':node.inputs['Object'].default_value=ref
 md=o.modifiers.new('AFN89_ACTUAL_BRAID_ROOT_TABLE','NODES');md.node_group=wrapper;md=o.modifiers.new('AFN89_BRAID_SKIN_ROOT_FRAMES','NODES');md.node_group=old.modifiers['AFN81_LIVE_RENDER_SCALP_FRAME'].node_group;bpy.context.view_layer.update();actual=q.hair(o);error=float(np.linalg.norm(actual-raw,axis=1).max());assert actual.shape==raw.shape and error<2e-6;assert {n:m.rig.k.f.v.v32.material_signature(bpy.data.materials[n]) for n in mats}==mats and m.m.q.lights()==lights
 o['AFN89_scope']='Daniel Bystedt137 native braid guides and complete source braid graph; mapped actual cap/parting and newly indexed roots. Same complete woman and original Brown material. No dynamics/contact/runtime qualification. Source braid tie instances, if present, not included in curve readback.';s['AFN89_C_scope']=o['AFN89_scope'];m.rig.shade.settings();m.rig.k.b.camera('face');s.camera.data.lens=85;s.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
 np.savez_compressed(E/'c-authored-braid-lineage.npz',sourceNativeLocal=P,mappedNativeLocal=Q,nativeCounts=counts,sourceCap=G0,targetCap=G1,capTriangles=T,guideRootFaces=np.array(rootFaces),guideRootBarycentric=np.array(rootBary),partSourceLocal=originalPart,partTargetLocal=newPart,actualNeutralWorld=actual,actualCounts=rc,actualRadii=radii,actualRootBodyVertexIDs=ids,actualRootBodyBarycentric=BC,actualFrameBodyVertexIDs=F,matrix=AA)
 save('c-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'publisherSource':str(DEMO),'publisherSha256':sha(DEMO),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'construction':'Replace complete curl/bob path construction with publisher-authored braid guides, parting mesh and braid/clump/displacement graph. Exact long-cap source correspondence reused; all generated actual roots freshly bound.','guideObject':o.name,'nativeGuides':len(counts),'nativeGuidePoints':int(counts.sum()),'actualCurves':len(rc),'actualPoints':len(actual),'sourceGuideRootMaximumCapDistanceLocal':max(rootGaps),'partingMaximumOriginalCapDistanceLocal':float(partGap.max()),'actualRootMaximumBodyDistanceM':max(gap),'minimumDoubleFrameAreaM2':float(area.min()),'neutralFrameMaximumErrorM':error,'objectSocketChanges':changes,'actualRootTable':ref.name,'curveReadbackDoesNotIncludeTieInstances':True,'noFullContactNaturalMotionRuntimeAcceptance':True,'secondsBeforePreview':time.time()-tick})
 rows=[]
 for view in ('back','face','body-face'):rows.append(v.image('c-authored-braids',view));save('c-pilot-controls.json',rows)
 print('R89_AUTHORED_BRAID_PILOT_DONE',len(rc),len(actual),time.time()-tick,flush=True)
if __name__=='__main__':main()
