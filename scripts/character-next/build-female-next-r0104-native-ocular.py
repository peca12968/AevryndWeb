"""One native artist head/ocular reassembly on the same continuous woman.
Restore actual artist eyelid surface rather than another fitted aperture.
Material/UV transfer samples bounded existing triangle locations, no new shader.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0104-native-artist-ocular-foundation';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0102-a-facet-aware-lining.blend';OUT=S/'aevrynd-female-next-r0104-a-native-artist-ocular.blend';SOURCE=R/'Reference/character/blender-human-base-meshes-v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend'
sp=importlib.util.spec_from_file_location('r104build',Path(__file__).with_name('build-female-next-r0102-facet-lining.py'));b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b);q=b.q;v=b.v;v.E=E
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8',newline='\n')
def bary(p,tri):
 xy=np.linalg.lstsq(np.column_stack((tri[1]-tri[0],tri[2]-tri[0])),p-tri[0],rcond=None)[0];w=np.clip(np.r_[1-xy.sum(),xy],0,1);return w/w.sum()
def main():
 tick=time.time();assert not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects['AFN101_CONTINUOUS_WOMAN_WITH_ARTICULATED_LIDS'];native=bpy.data.objects['AFN99_ORIGINAL_CONTINUOUS_ARTIST_SKIN'];hair=bpy.data.objects['AFN97_TUCKED_ARTIST_BOB_CHILDREN'];lash=bpy.data.objects['AFN59_LASHES_NATIVE_POINT_POSES'];face=bpy.data.objects['AFN59_FACE_CONTROLS'];oral=bpy.data.objects['AFN74_ORAL_CONTROLS'];hair0=q.hair(hair).copy();H0=q.geom(lash)[1].copy();d,W,T=b.geom(skin);original=q.arr(d.attributes['AFN101_OriginalCIndex'].data,'value',len(W),dtype='i4');oldNative,NP,NT=b.geom(native);NP=NP.copy();NT=NT.copy();unchanged=original>=0;assert np.linalg.norm(W[unchanged]-NP[original[unchanged]],axis=1).max()<4e-6
 oldOptics={}
 for side in ['L','R']:
  for part,stem in [('sclera','EYE_OUTER_SHELL_APPROX'),('iris','IRIS_PUPIL_SURFACE')]:
   ob=bpy.data.objects['AFN60_'+side+'_'+stem];dd,PP,TT=b.geom(ob);loops=q.arr(dd.loop_triangles,'loops',len(TT),3,dtype='i4');poly=q.arr(dd.loop_triangles,'polygon_index',len(TT),dtype='i4');oldOptics[(side,part)]={'object':ob,'P':PP.copy(),'T':TT.copy(),'uv':{u.name:q.arr(u.data,'uv',len(u.data),2)[loops].copy() for u in dd.uv_layers},'mat':q.arr(dd.polygons,'material_index',len(dd.polygons),dtype='i4')[poly].copy(),'materials':list(ob.data.materials)}
 names=['GEO-head_animation_realistic.'+part+'.'+side for side in ['L','R'] for part in ['sclera','iris']]
 with bpy.data.libraries.load(str(SOURCE),link=False) as (a,c):c.objects=names
 for ob in c.objects:scene.collection.objects.link(ob);ob.hide_render=False;ob.hide_viewport=False;ob.hide_set(False)
 bpy.context.view_layer.update();worlds={ob.name:ob.matrix_world.copy() for ob in c.objects};centres={side:(b.geom(next(ob for ob in c.objects if ob.name.endswith('sclera.'+side)))[1].min(0)+b.geom(next(ob for ob in c.objects if ob.name.endswith('sclera.'+side)))[1].max(0))/2 for side in ['L','R']};target=json.loads((E.parent/'r0100-native-eyelid-assembly/native-eye-topology.json').read_text('utf8'))['eyes'];targetC={side:np.array(target[side]['posteriorSphereFitCentreWorld']) for side in ['L','R']};scale=np.linalg.norm(targetC['L']-targetC['R'])/np.linalg.norm(centres['L']-centres['R']);M=Matrix.Diagonal((scale,scale,scale,1));M.translation=Vector((targetC['L']+targetC['R'])/2-scale*(centres['L']+centres['R'])/2);rig=bpy.data.objects['AFN69_BODY_CONTROLS'];optics=[]
 for ob in c.objects:
  side=ob.name[-1];part='sclera' if '.sclera.' in ob.name else 'iris';ob.parent=None;ob.matrix_world=M@worlds[ob.name];bpy.context.view_layer.update();dd,PP,TT=b.geom(ob);old=oldOptics[(side,part)];tree=BVHTree.FromPolygons(old['P'].tolist(),old['T'].tolist(),all_triangles=True);kd=KDTree(len(old['T']))
  for i,p in enumerate(old['P'][old['T']].mean(1)):kd.insert(Vector(p),i)
  kd.balance();base=ob.data;positions=q.arr(base.vertices,'co',len(base.vertices),3);A=np.array(ob.matrix_world);world=positions@A[:3,:3].T+A[:3,3];loops=q.arr(base.loops,'vertex_index',len(base.loops),dtype='i4');base.materials.clear()
  for material in old['materials']:base.materials.append(material)
  sourceFaces=[kd.find(Vector(world[list(f.vertices)].mean(0)))[1] for f in base.polygons];base.polygons.foreach_set('material_index',old['mat'][sourceFaces]);uvPerPoint={name:np.zeros((len(positions),2),'f4') for name in old['uv']};distances=[]
  for i,p in enumerate(world):
   hit,no,fi,dist=tree.find_nearest(Vector(p));assert fi is not None;weights=bary(np.array(hit),old['P'][old['T'][fi]]);distances.append(dist)
   for name,uv in old['uv'].items():uvPerPoint[name][i]=weights@uv[fi]
  for name,uv in uvPerPoint.items():
   layer=base.uv_layers.get(name) or base.uv_layers.new(name=name);layer.data.foreach_set('uv',uv[loops].ravel())
  if base.uv_layers.get('VitruvianUV.UDIM'):base.uv_layers.active=base.uv_layers['VitruvianUV.UDIM'];base.uv_layers['VitruvianUV.UDIM'].active_render=True
  for f in base.polygons:f.use_smooth=True
  base.update();ob.name='AFN104_NATIVE_'+side+'_'+part.upper();ob['source']='Dan Ulrich / Head (Animation) - Realistic, CC0; actual native mesh retained, original-source geometry controls kept.';matrix=ob.matrix_world.copy();ob.parent=rig;ob.parent_type='BONE';ob.parent_bone='Head';bpy.context.view_layer.update();ob.matrix_world=matrix;old['object'].hide_render=True;old['object'].hide_set(True);optics.append({'object':ob.name,'part':part,'side':side,'rawVertices':len(positions),'rawFaces':len(base.polygons),'UVAndMaterialTransferMaximumNearestSurfaceDistanceM':max(distances),'transfer':'Existing material IDs and bounded nearest existing surface triangle UV interpolation only; native actual geometry, shader parameters and texture files unchanged. Not a correct-UV/optical-quality certificate.'})
 skin.hide_render=True;skin.hide_set(True);native.hide_render=False;native.hide_set(False)
 for ob in [hair,lash]:
  for md in ob.modifiers:
   if md.type=='NODES':
    md.node_group=md.node_group.copy()
    for node in md.node_group.nodes:
     if node.bl_idname=='GeometryNodeObjectInfo' and node.inputs['Object'].default_value==skin:node.inputs['Object'].default_value=native
 for j in range(3):
  at=hair.data.attributes['AFN97_ScalpVertex'+str(j)];ids=q.arr(at.data,'value',24800,dtype='i4');assert (original[ids]>=0).all();at.data.foreach_set('value',original[ids])
 hair.data.update_tag();hair.update_tag();bpy.context.view_layer.update();hairError=float(np.linalg.norm(q.hair(hair)-hair0,axis=1).max());assert hairError<6e-6
 # Rebind all original lashes to explicit anterior ocular skin regions.
 # Nearest region attachment is reported as unqualified anatomical margin,
 # never as a finite follicle/contact or complete blink certificate.
 normal=np.cross(NP[NT[:,1]]-NP[NT[:,0]],NP[NT[:,2]]-NP[NT[:,0]]);normal/=np.maximum(np.linalg.norm(normal,axis=1),1e-30)[:,None];centroid=NP[NT].mean(1);trees={}
 for side,sign in [('L',1),('R',-1)]:
  cc=targetC[side];selected=np.flatnonzero((abs(centroid[:,0]-cc[0])<.020)&(abs(centroid[:,2]-cc[2])<.017)&(centroid[:,1]<cc[1])&(normal[:,1]<-.1));trees[side]=(BVHTree.FromPolygons(NP.tolist(),NT[selected].tolist(),all_triangles=True),selected)
 bindings=json.loads((E.parent/'r0102-facet-aware-lid-surface/a-retained-lash-bindings.json').read_text('utf8'));LA=np.array(lash.matrix_world);LI=np.linalg.inv(LA[:3,:3]);LV=(NP-LA[:3,3])@LI.T;HL=(H0-LA[:3,3])@LI.T;ids=np.empty((len(H0),3),'i4');barys=np.zeros_like(HL);offset=np.zeros_like(HL)
 for row in bindings:
  start=row['pointStart'];end=start+row['points'];side='L' if H0[start,0]>0 else 'R';tree,selected=trees[side];hit,no,fi,dist=tree.find_nearest(Vector(H0[start]));tri=NT[selected[fi]];weights=bary(np.array(hit),NP[tri]);a=LV[tri];t=a[1]-a[0];t/=np.linalg.norm(t);n=np.cross(a[1]-a[0],a[2]-a[0]);n/=np.linalg.norm(n);bit=np.cross(n,t);offset[start:end]=(HL[start:end]-HL[start])@np.column_stack((t,bit,n));ids[start:end]=tri;barys[start:end]=weights;row.update({'actualSkinTriangle':tri.tolist(),'barycentric':weights.tolist(),'sourceRootToNewMarginDistanceWorldM':dist,'actualAnatomicalMarginAccepted':False})
 for j in range(3):lash.data.attributes['AFN101_LashVertex'+str(j)].data.foreach_set('value',ids[:,j])
 lash.data.attributes['AFN101_LashBarycentric'].data.foreach_set('vector',barys.astype('f4').ravel());lash.data.attributes['AFN101_LashLocalFrameOffset'].data.foreach_set('vector',offset.astype('f4').ravel());lash.data.update_tag();lash.update_tag();bpy.context.view_layer.update();save('a-retained-lash-bindings.json',bindings)
 # Restore only the single inherited C blink input, no overlapping new lids.
 routes=0;legacy=bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'];freeze=bpy.data.objects['AFN101_LEGACY_SKIN_NEUTRAL_BLINK_INPUT']
 for fc in legacy.data.shape_keys.animation_data.drivers:
  for var in fc.driver.variables:
   for t in var.targets:
    if t.id==freeze:t.id=face;routes+=1
 legacy.data.shape_keys.update_tag();legacy.update_tag();bpy.context.view_layer.update();save('a-build-summary.json',{'source':str(SRC),'output':str(OUT),'renderSkin':native.name,'sourceBundle':str(SOURCE),'sourceBundleSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'sameContinuousArtistBodyAndNeckRestored':True,'r102ConstructedLidAndFiniteLiningRetainedHiddenAsRollback':True,'nativePairedOptics':optics,'singleInheritedBlinkRoutesRestored':routes,'allGroomControlsMaximumWorldDifferenceM':hairError,'neutralLashMaximumWorldChangeM':float(np.linalg.norm(q.geom(lash)[1]-H0,axis=1).max()),'completeAppearanceOperationContactRuntimeAccepted':False,'secondsBeforePreview':time.time()-tick});native['AFN104_scope']='Original continuous artist C head/body plus original-artist native paired optics. Restored native ocular shape, no new aperture/fold field. R102 entire alternative topology remains hidden. Native inherited blink, lash anatomical margin, all new contacts/optical UV and runtime unaccepted.'
 b.m.m.rig.shade.settings();b.m.m.rig.k.b.camera('face');scene.camera.data.lens=85;scene.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);views=[]
 for view in ['face','profile','body-face']:views.append(v.image('a-native-ocular',view));save('a-view-controls.json',views)
 print('R104_FIRST_COMPLETE_PREVIEW_DONE',time.time()-tick,flush=True)
 for ob in [face,oral]:
  if ob.animation_data:ob.animation_data.action=None
 for label,value in [('half',.5),('closed',1.)]:b.deliver(value);views.append(v.image('a-native-ocular-'+label,'face'));save('a-view-controls.json',views)
 print('R104_NATIVE_OCULAR_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
