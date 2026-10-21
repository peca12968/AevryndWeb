"""Actual native Add/Comb scalp hair authoring on the retained complete woman."""
from pathlib import Path
import bpy,numpy as np,json,time,datetime,importlib.util,traceback
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
from bpy_extras.view3d_utils import location_3d_to_region_2d
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0136-native-curve-combing';S=R/'engine/assets/characters/female-next/source';SRC=S/'r0126-source/aevrynd-female-next-r0126-b-source-section-neck.blend';OUT=S/'r0136-source/aevrynd-female-next-r0136-a-native-combed-bob.blend'
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
a=module('r136base','build-female-next-r0116-native-eye-character.py');b=a.b;q=a.q;b.u.v.E=E
caphelper=module('r136cap','build-female-next-r0130-native-emitter-field.py');b.u.v.E=E
def save(n,x):
 if n in ['native-authoring-start.json','native-authoring-terminal-error.json'] and (E/n).exists():n=n.replace('.json','-'+str(time.time_ns())+'.json')
 (E/n).write_text(json.dumps(x,indent=2,default=lambda v:v.tolist() if isinstance(v,np.ndarray) else v.item() if isinstance(v,np.generic) else str(v))+'\n',encoding='utf-8')
def raw(d):
 P=np.empty((len(d.position_data),3),'f4');d.position_data.foreach_get('vector',P.ravel());return P
def attr(d,n,t,v,domain='CURVE'):
 x=d.attributes.new(n,t,domain);x.data.foreach_set('vector' if t=='FLOAT_VECTOR' else 'value',np.asarray(v,'i4' if t=='INT' else 'f4').ravel())
def attach(h,skin,ids,bc,roots):
 for j in range(3):attr(h.data,'AFN136_SkinVertex'+str(j),'INT',ids[:,j]);attr(h.data,'AFN136_SkinWeight'+str(j),'FLOAT',bc[:,j])
 attr(h.data,'AFN136_RestFollicle','FLOAT_VECTOR',roots)
 ng,n,L=b.u.m.interface('AFN136_ACTUAL_NATIVE_FOLLICLE_SKIN_ATTACHMENT');i=n.new('NodeGroupInput');o=n.new('NodeGroupOutput');info=n.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE';info.inputs['Object'].default_value=skin;pos=n.new('GeometryNodeInputPosition')
 def named(k,t):x=n.new('GeometryNodeInputNamedAttribute');x.data_type=t;x.inputs['Name'].default_value=k;return x.outputs['Attribute']
 def vec(op,A,B):x=n.new('ShaderNodeVectorMath');x.operation=op;L.new(A,x.inputs[0]);L.new(B,x.inputs['Scale'] if op=='SCALE' else x.inputs[1]);return x.outputs['Vector']
 terms=[]
 for j in range(3):
  v=n.new('GeometryNodeSampleIndex');v.data_type='FLOAT_VECTOR';v.domain='POINT';v.clamp=False;L.new(info.outputs['Geometry'],v.inputs['Geometry']);L.new(pos.outputs['Position'],v.inputs['Value']);L.new(named('AFN136_SkinVertex'+str(j),'INT'),v.inputs['Index']);terms.append(vec('SCALE',v.outputs['Value'],named('AFN136_SkinWeight'+str(j),'FLOAT')))
 anchor=vec('ADD',vec('ADD',terms[0],terms[1]),terms[2]);delta=vec('SUBTRACT',anchor,named('AFN136_RestFollicle','FLOAT_VECTOR'));setp=n.new('GeometryNodeSetPosition');L.new(i.outputs['Geometry'],setp.inputs['Geometry']);L.new(delta,setp.inputs['Offset']);L.new(setp.outputs['Geometry'],o.inputs['Geometry']);h.modifiers.new('AFN136_LIVE_NATIVE_ROOT_TRANSLATION_ONLY','NODES').node_group=ng
def main():
 tick=time.time();assert not OUT.exists();save('native-authoring-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originalRoundStartedUTC':'2026-10-21T20:05:00+00:00','action':'Native Add on actual current scalp with source UV followed by actual native Comb strokes; one authored full hair candidate.','supportDeadlinePreservedUTC':'2026-10-21T20:15:00+00:00'});protected=a.protected();skin=bpy.data.objects['AFN126_COMPLETE_WOMAN_BODY_AND_ARTIST_HEAD'];_,W,T=b.u.b.geom(skin);W=W.copy();T=T.copy();skinHash=[a.hasharray(W),a.hasharray(T)];D=np.load(E.parent/'r0133-anatomical-scalp-chart/target-scalp-chart.npz');V=D['world'];F=D['triangles'];UV=D['uv'];kd=KDTree(len(W))
 for j,p in enumerate(W):kd.insert(Vector(p),j)
 kd.balance();hits=[kd.find(Vector(p)) for p in V];skinIDs=np.array([h[1] for h in hits],'i4');assert max(h[2] for h in hits)<2e-6;V=W[skinIDs]
 mesh=bpy.data.meshes.new('AFN136_CurrentNativeScalpSurface');mesh.from_pydata(V.tolist(),[],F.tolist());mesh.update();scalp=bpy.data.objects.new('AFN136_ACTUAL_CURRENT_SCALP',mesh);bpy.context.scene.collection.objects.link(scalp);scalp.hide_render=True
 uv=mesh.uv_layers.new(name='AFN136_NativeScalpUV');uv.data.foreach_set('uv',UV[F.ravel()].astype('f4').ravel());caphelper.point_bound_cap(scalp,skin,np.repeat(skinIDs[:,None],3,axis=1),np.tile([1.,0.,0.],(len(V),1)),V)
 d=bpy.data.hair_curves.new('AFN136_NATIVE_COMBED_ROOT_TIP_CURVES');h=bpy.data.objects.new('AFN136_NATIVE_COMBED_ROOT_TIP_CURVES',d);bpy.context.scene.collection.objects.link(h);d.surface=scalp;d.surface_uv_map=uv.name
 collisionProperty=[p.identifier for p in d.bl_rna.properties if 'collision' in p.identifier]
 if hasattr(d,'use_sculpt_collision'):d.use_sculpt_collision=True
 bpy.ops.object.select_all(action='DESELECT');h.select_set(True);bpy.context.view_layer.objects.active=h;bpy.context.view_layer.update()
 with bpy.context.temp_override(active_object=h,object=h,selected_objects=[h],selected_editable_objects=[h]):bpy.ops.object.mode_set(mode='SCULPT_CURVES')
 area=next(x for x in bpy.context.screen.areas if x.type=='VIEW_3D');reg=next(x for x in area.regions if x.type=='WINDOW');rv=area.spaces.active.region_3d;st=bpy.context.tool_settings.curves_sculpt;st.unified_paint_settings.use_unified_size=False;st.unified_paint_settings.use_unified_strength=False;ops=[];center=Vector((0,-.015,1.50))
 def view(direction):
  rv.view_rotation=Vector(direction).to_track_quat('Z','Y');rv.view_location=center;rv.view_distance=.55;rv.view_perspective='ORTHO';rv.update();bpy.context.view_layer.update()
 def brush(name,size,strength):
  bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS',relative_asset_identifier='brushes/essentials_brushes-curve_sculpt.blend/Brush/'+name);br=st.brush;br.size=int(size);br.strength=strength
  if hasattr(br,'falloff_shape'):br.falloff_shape='PROJECTED'
  return br
 def stroke(name,P,Q=None,steps=8):
  Q=P if Q is None else Q;A=location_3d_to_region_2d(reg,rv,Vector(P));B=location_3d_to_region_2d(reg,rv,Vector(Q));before=raw(d);events=[]
  for j,t in enumerate(np.linspace(0,1,steps)):
   xy=tuple(A.lerp(B,float(t)));events.append({'name':name+str(j),'mouse':xy,'mouse_event':xy,'pressure':1.,'size':st.brush.size,'time':j*.04,'is_start':j==0,'location':tuple(Vector(P).lerp(Vector(Q),float(t))),'x_tilt':0.,'y_tilt':0.})
  r=bpy.ops.sculpt_curves.brush_stroke(stroke=events);after=raw(d);row={'brush':st.brush.name,'name':name,'worldStroke':[list(P),list(Q)],'sizePixels':st.brush.size,'strength':st.brush.strength,'beforePoints':len(before),'afterPoints':len(after),'curves':len(d.curves),'result':sorted(r),'maxActualPointDeltaM':float(np.linalg.norm(after-before,axis=1).max()) if len(before)==len(after) and len(after) else None};ops.append(row);save('native-brush-operations.json',ops);print('R136_NATIVE_OPERATION',name,len(d.curves),row['maxActualPointDeltaM'],flush=True)
 with bpy.context.temp_override(area=area,region=reg,active_object=h,object=h,selected_objects=[h],selected_editable_objects=[h]):
  br=brush('Add',110,1.);cs=br.curves_sculpt_settings;cs.add_amount=180;cs.points_per_curve=41;cs.curve_length=.22;cs.curve_radius=.000045;cs.minimum_distance=.0008;cs.use_shape_interpolate=False;cs.use_length_interpolate=False;cs.use_point_count_interpolate=False;cs.use_radius_interpolate=False
  centers=V[F].mean(1);normal=np.cross(V[F[:,1]]-V[F[:,0]],V[F[:,2]]-V[F[:,0]]);normal/=np.maximum(np.linalg.norm(normal,axis=1),1e-12)[:,None];rng=np.random.default_rng(136041)
  for vi,direction in enumerate([(0,-1,.5),(1,0,.25),(-1,0,.25),(0,1,.3),(0,0,1)]):
   view(direction);direction=np.array(direction,dtype=float);direction/=np.linalg.norm(direction);indices=np.flatnonzero(normal@direction>.65);chosen=[]
   for ix in rng.permutation(indices):
    if all(np.linalg.norm(centers[ix]-centers[j])>.018 for j in chosen):chosen.append(int(ix))
    if len(chosen)==12:break
   for j,ix in enumerate(chosen):stroke('native-add-%s-%s'%(vi,j),centers[ix],steps=2)
  assert len(d.curves)>1000,'Native Add did not produce a usable full scalp authoring layer';initial=raw(d);save('native-add-geometry.json',{'curves':len(d.curves),'points':len(initial),'hash':a.hasharray(initial),'collisionProperties':collisionProperty,'surface':scalp.name,'UV':uv.name,'allCurvesCreatedByNativeAddNotScriptedPaths':True})
  br=brush('Comb',2400,.9)
  for vi,direction in enumerate([(1,0,.1),(-1,0,.1),(0,1,.1)]):
   view(direction);stroke('native-comb-gravity-'+str(vi),(0,0,1.57),(0,0,1.34),steps=18)
  view((0,-1,.2));brush('Comb',480,.65)
  stroke('native-part-right',(.014,-.035,1.575),(.082,-.050,1.51),steps=14);stroke('native-part-left',(-.014,-.035,1.575),(-.082,-.050,1.51),steps=14)
  for sign in [-1,1]:
   view((sign,0,.05));brush('Comb',600,.65);stroke('native-temple-ear-sweep-'+str(sign),(sign*.078,-.045,1.52),(sign*.083,.028,1.40),steps=16);stroke('native-nape-inward-'+str(sign),(sign*.08,.035,1.36),(sign*.058,.010,1.33),steps=10)
  final=raw(d);assert np.linalg.norm(final-initial,axis=1).max()>1e-4,'Actual native Comb did not change actual curves'
 bpy.ops.object.mode_set(mode='OBJECT');counts=np.array([len(c.points) for c in d.curves],'i4');starts=np.r_[0,np.cumsum(counts)[:-1]];roots=final[starts].astype('f8');rootMove=np.linalg.norm(roots-initial[starts],axis=1);tree=BVHTree.FromPolygons(V.tolist(),F.tolist(),all_triangles=True);fi=[];bc=[];dist=[]
 for p in roots:
  co,no,i,ds=tree.find_nearest(Vector(p));tri=V[F[i]];ab=tri[1]-tri[0];ac=tri[2]-tri[0];uv2=np.linalg.lstsq(np.stack([ab,ac],axis=1),np.array(co)-tri[0],rcond=None)[0];fi.append(i);bc.append([1-uv2.sum(),*uv2]);dist.append(ds)
 fi=np.array(fi,'i4');bc=np.array(bc);attach(h,skin,skinIDs[F[fi]],bc,np.einsum('ij,ijk->ik',bc,W[skinIDs[F[fi]]]))
 # Native Add roots are on the surface, not a finite-thickness contact proof.
 radius=np.repeat(.000045*np.maximum(.06,(1-np.linspace(0,1,41))**.45)[None,:],len(counts),axis=0).ravel();assert np.all(counts==41)
 rr=d.attributes.get('radius') or d.attributes.new('radius','FLOAT','POINT');rr.data.foreach_set('value',radius.astype('f4'));mat=bpy.data.materials.new('AFN136_InitialBrownNativeHair');mat.use_nodes=True;nd=mat.node_tree.nodes;nd.clear();out=nd.new('ShaderNodeOutputMaterial');ha=nd.new('ShaderNodeBsdfHairPrincipled');ha.parametrization='MELANIN';ha.inputs['Melanin'].default_value=.7;ha.inputs['Melanin Redness'].default_value=.4;ha.inputs['Roughness'].default_value=.3;ha.inputs['Radial Roughness'].default_value=.3;mat.node_tree.links.new(ha.outputs[0],out.inputs['Surface']);d.materials.append(mat);bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'].hide_render=True;bpy.data.objects['AFN126_ORIGINAL_Hair_Hair_0'].hide_set(True)
 h['authoring']='Actual installed Blender native Add/Comb brush strokes and native scalp UV, no analytic guide-field/cache transplant or surface-isocontour paths. Fixed initial radius45um, melanin.7/redness.4/roughness.3. No scalar variants.';h['scope']='Appearance candidate only. Root translation follows current actual skin; no rotation/rigid head deformation, biological dynamic/finite/self/continuous contact, engine or acceptance claim.';h['sourceCredit']='Original scalp/head/skin and reference bob: Angelica / DarkNik original NikZava284, CC-BY4.0; body MakeHuman/Vitruvian CC0. New native comb authoring Aevrynd; attribution/legal retained.'
 assert protected==a.protected();_,WW,TT=b.u.b.geom(skin);assert skinHash==[a.hasharray(WW),a.hasharray(TT)];bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False)
 np.savez_compressed(E/'native-follicle-lineage.npz',counts=counts,rootSkinVertexIds=skinIDs[F[fi]],rootBarycentric=bc,rootRestWorld=roots)
 save('a-build-summary.json',{'source':str(SRC),'sourceSha256':a.sha(SRC),'output':str(OUT),'sha256':a.sha(OUT),'bytes':OUT.stat().st_size,'hairObject':h.name,'scalpObject':scalp.name,'curves':len(counts),'points':len(final),'allCurvesNativeAddAuthored':True,'nativeCombMaxPointDeltaM':float(np.linalg.norm(final-initial,axis=1).max()),'nativeCombRootDeltaMaxM':float(rootMove.max()),'nativeRootsDistanceToOwnActualScalpMaxM':max(dist),'actualNativeOperations':len(ops),'currentSkinHashes':skinHash,'protectedRollbackUnchanged':True,'currentSkinExact':True,'naturalMotionAndFiniteSelfContinuousContactRuntimeUnaccepted':True,'secondsBeforePreview':time.time()-tick});rows=[]
 for v in ['face','body-face','profile','oblique','back']:rows.append(b.u.v.image('a-native-combed-bob',v));save('a-view-controls.json',rows)
 print('R136_ACTUAL_COMPLETE_NATIVE_COMBED_CHARACTER_PREVIEW_DONE',time.time()-tick,flush=True)
def run():
 try:main()
 except:traceback.print_exc();save('native-authoring-terminal-error.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'traceback':traceback.format_exc()})
 finally:bpy.ops.wm.quit_blender()
def load_then_run():
 bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.app.timers.register(run,first_interval=.5)
if __name__=='__main__':bpy.app.timers.register(load_then_run,first_interval=.5)
