"""One continuous, welded and coherently oriented display skin.
Preserve the fine artist head and complete original body/control sources.
Fit the existing optical assembly to the artist's companion globe dimensions.
This is a source-backed construction change, not a zipper/eye parameter scan.
"""
from pathlib import Path
import bpy,bmesh,numpy as np,json,hashlib,importlib.util,time
from mathutils.kdtree import KDTree
from mathutils import Vector
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0099-continuous-head-neck';OLD=E.parent/'r0098-whole-head-foundation';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0098-b-native-artist-head.blend';OUT=S/'aevrynd-female-next-r0099-a-continuous-head-neck.blend'
def mod(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);return a
v=mod('r99views','render-female-next-r0091-matched.py');v.E=E;m=v.m;q=m.q
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8')
def live_positions(ob,skin,head):
 ng=bpy.data.node_groups.new('AFN99_CONTINUOUS_SKIN_LIVE_SOURCE_VERTICES','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');n=ng.nodes;L=ng.links;inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput');values=[]
 for source,name in [(skin,'AFN99_SkinVertex'),(head,'AFN99_HeadVertex')]:
  info=n.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE';info.inputs['Object'].default_value=source;info.inputs['As Instance'].default_value=False;ids=n.new('GeometryNodeInputNamedAttribute');ids.data_type='INT';ids.inputs['Name'].default_value=name;pos=n.new('GeometryNodeInputPosition');sample=n.new('GeometryNodeSampleIndex');sample.data_type='FLOAT_VECTOR';sample.domain='POINT';sample.clamp=False;L.new(info.outputs['Geometry'],sample.inputs['Geometry']);L.new(ids.outputs['Attribute'],sample.inputs['Index']);L.new(pos.outputs['Position'],sample.inputs['Value']);values.append(sample.outputs['Value'])
 use=n.new('GeometryNodeInputNamedAttribute');use.data_type='BOOLEAN';use.inputs['Name'].default_value='AFN99_UseSkin';switch=n.new('GeometryNodeSwitch');switch.input_type='VECTOR';L.new(use.outputs['Attribute'],switch.inputs['Switch']);L.new(values[1],switch.inputs['False']);L.new(values[0],switch.inputs['True']);setpos=n.new('GeometryNodeSetPosition');L.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);L.new(switch.outputs['Output'],setpos.inputs['Position']);L.new(setpos.outputs['Geometry'],out.inputs['Geometry']);md=ob.modifiers.new('AFN99_LIVE_CONTINUOUS_WELDED_SKIN','NODES');md.node_group=ng
def main():
 tick=time.time();assert not OUT.exists() and sha(SRC)=='05b138b206e9207268f9601752cf3b50ae11516abce9f34181e70e38777dcefb';z=np.load(E/'actual-interface-input.npz');line=np.load(OLD/'b-native-head-lineage.npz');bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects['AFN74_SKIN_AND_EXISTING_OCULAR_LINING'];head=bpy.data.objects['AFN98_ORIGINAL_ARTIST_HEAD_AND_NECK_COLLAR'];A=np.array(head.matrix_world);inv=np.linalg.inv(A[:3,:3]);SV=z['skinV'];HV=z['headV'];ns=len(SV);V=np.vstack((SV,HV));T=np.vstack((z['skinT'],z['headT']+ns));mesh=bpy.data.meshes.new('AFN99_CONTINUOUS_RENDER_SKIN');mesh.from_pydata(((V-A[:3,3])@inv.T).tolist(),[],T.tolist());mesh.update();ob=bpy.data.objects.new(mesh.name,mesh);s.collection.objects.link(ob);ob.matrix_world=head.matrix_world.copy()
 assert [x.name for x in skin.data.materials]==[x.name for x in head.data.materials]
 for mat in skin.data.materials:mesh.materials.append(mat)
 mat=np.r_[z['skinMaterial'],z['headMaterial']];mesh.polygons.foreach_set('material_index',mat);mesh.polygons.foreach_set('use_smooth',np.ones(len(mesh.polygons),bool))
 names=json.loads((E/'actual-interface-input.json').read_text('utf8'))['skin']['uvNames']
 for j,name in enumerate(names):
  uv=np.concatenate((z['skinUV'+str(j)][z['skinLoops']],z['headUV'+str(j)][z['headLoops']])).reshape(-1,2);mesh.uv_layers.new(name=name).data.foreach_set('uv',uv.ravel())
 for name,kind,data in [('AFN99_SkinVertex','INT',np.r_[np.arange(ns,dtype='i4'),np.zeros(len(HV),'i4')]),('AFN99_HeadVertex','INT',np.r_[np.zeros(ns,'i4'),np.arange(len(HV),dtype='i4')]),('AFN99_UseSkin','BOOLEAN',np.r_[np.ones(ns,bool),np.zeros(len(HV),bool)])]:mesh.attributes.new(name,kind,'POINT').data.foreach_set('value',data)
 kd=KDTree(len(SV))
 for i,pt in enumerate(SV):kd.insert(pt,i)
 kd.balance();pairs=[]
 for hi in line['neckHeadVertexIDs']:
  co,si,d=kd.find(Vector(HV[hi]));assert d<1e-8,(int(hi),d);pairs.append((ns+int(hi),si))
 assert len(pairs)==272 and len({b for a,b in pairs})==272
 bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table();weld={bm.verts[a]:bm.verts[b] for a,b in pairs};bmesh.ops.weld_verts(bm,targetmap=weld);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update();bm.to_mesh(mesh);bm.free();mesh.update();assert len(mesh.vertices)==len(V)-272;live_positions(ob,skin,head);skin.hide_render=True;head.hide_render=True;skin.hide_set(True);head.hide_set(True)
 # The scanned source head has its own companion globe. Match equatorial
 # dimensions of the retained optical assembly, keeping its internal ratios.
 # This is anatomical registration; all old contact certificates are invalid.
 ref=json.loads((OLD/'official-female-reference.json').read_text('utf8'));plan=json.loads((OLD/'a-head-envelope-plan.json').read_text('utf8'));eyeRows=[];oldEye=[];newEye=[]
 for side in ['L','R']:
  shell=bpy.data.objects['AFN60_'+side+'_EYE_OUTER_SHELL_APPROX'];_,P=q.geom(shell);centre=(P.min(0)+P.max(0))/2;extent=P.max(0)-P.min(0);source=next(row for name,row in ref['eyes'].items() if name.endswith('.'+side));bounds=np.array(source['bounds']);wanted=(bounds[1]-bounds[0])*plan['sourceScale'];scale=float(np.sqrt(wanted[0]*wanted[2]/(extent[0]*extent[2])));assert .65<scale<1.35
  for name in ['AFN60_'+side+'_EYE_OUTER_SHELL_APPROX','AFN60_'+side+'_IRIS_PUPIL_SURFACE']:
   part=bpy.data.objects[name];B=np.array(part.matrix_world);BI=np.linalg.inv(B[:3,:3]);count=len(part.data.vertices)
   for key in part.data.shape_keys.key_blocks:
    local=q.arr(key.data,'co',count,3).astype('f8');world=local@B[:3,:3].T+B[:3,3];desired=centre+(world-centre)*scale;key.data.foreach_set('co',((desired-B[:3,3])@BI.T).astype('f4').ravel())
    if key==part.data.shape_keys.key_blocks[0]:oldEye.append(world);newEye.append(desired)
  eyeRows.append({'side':side,'sourceGlobeEquatorialExtentM':wanted[[0,2]],'previousShellEquatorialExtentM':extent[[0,2]],'sourceBackedUniformAssemblyScale':scale,'centreUnchangedWorld':centre,'scope':'Companion original CC0 globe dimensions, uniform scale of every retained optical shape key; iris/cornea ratios and drivers retained. Not accepted optics, eyelid motion or contact.'})
 bpy.context.view_layer.update();d,actual=q.geom(ob);assert np.isfinite(actual).all();si=q.arr(mesh.attributes['AFN99_SkinVertex'].data,'value',len(mesh.vertices),dtype='i4');hi=q.arr(mesh.attributes['AFN99_HeadVertex'].data,'value',len(mesh.vertices),dtype='i4');use=q.arr(mesh.attributes['AFN99_UseSkin'].data,'value',len(mesh.vertices),dtype='i4').astype(bool);expected=np.where(use[:,None],SV[si],HV[hi]);err=float(np.linalg.norm(actual-expected,axis=1).max());assert err<3e-6,err
 mesh.calc_loop_triangles();F=q.arr(mesh.loop_triangles,'vertices',len(mesh.loop_triangles),3,dtype='i4');edges=np.concatenate((F[:,[0,1]],F[:,[1,2]],F[:,[2,0]]));sortedEdges=np.sort(edges,axis=1);unique,index,inc=np.unique(sortedEdges,axis=0,return_inverse=True,return_counts=True);orientation=np.bincount(index,weights=np.where(edges[:,0]<edges[:,1],1,-1));conflicts=int(np.count_nonzero((inc==2)&(orientation!=0)));boundary=int(np.count_nonzero(inc==1));assert conflicts==0 and boundary==0,(conflicts,boundary)
 ob['scope']='Single continuous welded display skin:272 explicit exact body/head boundary pairs, coherent global face winding, per-vertex live source mapping. Original fine head/body/UV/materials retained. Edge incidence/orientation is not a self-intersection, finite-contact or continuous-time proof.';ob['sourceCredit']=head.get('sourceCredit','');m.rig.shade.settings();m.rig.k.b.camera('face');s.camera.data.lens=85;s.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
 np.savez_compressed(E/'a-continuous-skin-lineage.npz',weldPairsBefore=np.array(pairs,'i4'),skinSourceVertex=si,headSourceVertex=hi,useSkinSource=use,restWorld=expected,triangles=F,oldOpticalWorld=np.vstack(oldEye),newOpticalWorld=np.vstack(newEye));save('a-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'renderSkin':ob.name,'actualVertices':len(mesh.vertices),'triangles':len(F),'explicitWeldedBoundaryPairs':len(pairs),'boundaryEdges':boundary,'internalOrientationConflictEdges':conflicts,'priorHeadOrientationConflictEdges':183,'bodyAndFineHeadNeutralWorldMaximumErrorM':err,'existingIndependentSourceSkinAndHeadHiddenOnlyAfterJoinedReplacement':True,'sourceBackedOpticalFit':eyeRows,'newCompleteAppearanceOperationContactsNaturalDynamicsRuntimeAccepted':False,'secondsBeforePreview':time.time()-tick});rows=[]
 for view in ['face','profile','oblique','body-face']:rows.append(v.image('a-continuous-skin',view));save('a-view-controls.json',rows)
 print('R99_COMPLETE_CONTINUOUS_SKIN_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
