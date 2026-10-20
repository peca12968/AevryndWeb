"""Actual complete official female source views before selecting a head basis.
Neutral clay and uniform stage placement only; source geometry remains artist
data. Not the target woman or a new character gain. No source script executed.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Matrix,Vector
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0098-whole-head-foundation';S=R/'engine/assets/characters/female-next/source';P=R/'Reference/character/blender-human-base-meshes-v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend'
sp=importlib.util.spec_from_file_location('r98sourceviews',Path(__file__).with_name('render-female-next-r0091-matched.py'));v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v);v.E=E;m=v.m;q=m.q
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8')
tick=time.time();bpy.ops.wm.open_mainfile(filepath=str(S/'aevrynd-female-next-r0097-neutral-scalp-control-reference.blend'));s=bpy.context.scene;s.frame_set(1)
for o in list(bpy.data.objects):
 if o.type not in ['LIGHT','CAMERA'] and o.name!='AFN74_ORAL_CONTROLS':bpy.data.objects.remove(o,do_unlink=True)
with bpy.data.libraries.load(str(P),link=False) as (a,b):b.collections=['Body Female - Realistic']
col=b.collections[0];s.collection.children.link(col);metadata={}
for owner in [col]+list(col.all_objects):
 asset=owner.asset_data
 if asset:metadata[owner.name]={k:getattr(asset,k,'') for k in ['author','description','copyright','license']}
for ob in col.all_objects:
 ob.hide_render=False;ob.hide_viewport=False;ob.hide_set(False)
 for md in ob.modifiers:
  if md.type=='MULTIRES':md.levels=md.render_levels=min(md.total_levels,2)
bpy.context.view_layer.update();body=next(o for o in col.all_objects if o.name.startswith('GEO-body_female_realistic') and '.eye.' not in o.name);mesh,world=q.geom(body);height=world[:,2].max()-world[:,2].min();scale=1.56/height;centre=(world.min(0)+world.max(0))/2;M=Matrix.Diagonal((scale,scale,scale,1));M.translation=Vector((-centre[0]*scale,-centre[1]*scale-.025,-world[:,2].min()*scale))
for ob in col.all_objects:ob.matrix_world=M@ob.matrix_world
mat=bpy.data.materials.new('AFN98_SOURCE_REFERENCE_CLAY');mat.use_nodes=True;bs=mat.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=mat.node_tree.nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(bs.outputs['BSDF'],out.inputs['Surface']);bs.inputs['Base Color'].default_value=(.28,.28,.28,1);bs.inputs['Roughness'].default_value=.6
for ob in col.all_objects:
 if ob.type=='MESH':
  ob.data.materials.clear();ob.data.materials.append(mat)
  for poly in ob.data.polygons:poly.material_index=0;poly.use_smooth=True
bpy.context.view_layer.update();d,world=q.geom(body);d.calc_loop_triangles();tri=q.arr(d.loop_triangles,'vertices',len(d.loop_triangles),3,dtype='i4');uv={layer.name:q.arr(layer.data,'uv',len(d.loops),2) for layer in d.uv_layers};eyes={ob.name:{'matrix':np.array(ob.matrix_world),'bounds':[q.geom(ob)[1].min(0),q.geom(ob)[1].max(0)]} for ob in col.all_objects if '.eye.' in ob.name};np.savez_compressed(E/'official-female-reference-geometry.npz',world=world,triangles=tri,**{'uv_'+k:val for k,val in uv.items()});save('official-female-reference.json',{'source':str(P),'sourceSha256':hashlib.sha256(P.read_bytes()).hexdigest(),'collection':col.name,'bodyObject':body.name,'metadata':metadata,'objects':[o.name for o in col.all_objects],'sourceModifiers':[(md.name,md.type,getattr(md,'total_levels',None),getattr(md,'levels',None)) for md in body.modifiers],'stageUniformScale':scale,'stageWorldTransform':np.array(M),'evaluatedVertices':len(world),'evaluatedTriangles':len(tri),'worldBounds':[world.min(0),world.max(0)],'eyes':eyes,'licenseScope':'Bundle README explicitly CC0; asset metadata retained. Orphan text named License refers to Rain Rig CC-BY4; preserve both texts and do not blanket-relabel unrelated rig data. Only selected female mesh data used; no source rig code executed.','referenceOnlyNotNewWomanOrAdoption':True,'fixtureRepair':'All prior actor/reference objects removed from this temporary source-view scene; first contaminated images retained separately and not used as inspected donor evidence.','secondsBeforeViews':time.time()-tick});rows=[]
for view in ['face','profile','oblique','body-face']:rows.append(v.image('official-female-source',view));save('official-source-view-controls.json',rows)
print('R98_ACTUAL_OFFICIAL_FEMALE_REFERENCE_DONE',time.time()-tick,flush=True)
