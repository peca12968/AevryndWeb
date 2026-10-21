"""Actual existing artist heads/paired optics, not a new woman or adoption."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Matrix,Vector
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0104-native-artist-ocular-foundation';S=R/'engine/assets/characters/female-next/source';P=R/'Reference/character/blender-human-base-meshes-v1.4.1/human-base-meshes-bundle-v1.4.1/human_base_meshes_bundle.blend'
sp=importlib.util.spec_from_file_location('r104source',Path(__file__).with_name('render-female-next-r0091-matched.py'));v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v);v.E=E;q=v.m.q
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8',newline='\n')
def geom(o):
 d,W=q.geom(o);d.calc_loop_triangles();return d,W,q.arr(d.loop_triangles,'vertices',len(d.loop_triangles),3,dtype='i4')
def main():
 tick=time.time();reports={};target=np.mean([row['posteriorSphereFitCentreWorld'] for row in json.loads((E.parent/'r0100-native-eyelid-assembly/native-eye-topology.json').read_text('utf8'))['eyes'].values()],axis=0)
 for tag,colname,stem in [('animation','Head (Animation) - Realistic','GEO-head_animation_realistic'),('sculpting','Head (Sculpting) - Realistic','GEO-head_sculpting_realistic')]:
  bpy.ops.wm.open_mainfile(filepath=str(S/'aevrynd-female-next-r0102-a-facet-aware-lining.blend'));scene=bpy.context.scene
  for ob in list(bpy.data.objects):
   if ob.type not in ['LIGHT','CAMERA'] and ob.name!='AFN74_ORAL_CONTROLS':bpy.data.objects.remove(ob,do_unlink=True)
  with bpy.data.libraries.load(str(P),link=False) as (a,b):assert colname in a.collections;b.collections=[colname]
  col=b.collections[0];scene.collection.children.link(col);metadata={};original={ob.name:ob.matrix_world.copy() for ob in col.all_objects};mesh=next(ob for ob in col.all_objects if ob.name==stem);eyes=[ob for ob in col.all_objects if ob.name.startswith(stem+'.sclera.')];assert len(eyes)==2
  for owner in [col]+list(col.all_objects):
   if owner.asset_data:metadata[owner.name]={k:getattr(owner.asset_data,k,'') for k in ['author','description','copyright','license']}
  for ob in col.all_objects:
   ob.hide_render=False;ob.hide_viewport=False;ob.hide_set(False)
   for md in ob.modifiers:
    if md.type=='MULTIRES':md.levels=md.render_levels=min(md.total_levels,2)
  bpy.context.view_layer.update();centres=[(geom(ob)[1].min(0)+geom(ob)[1].max(0))/2 for ob in eyes];mean=np.mean(centres,axis=0);scale=.060/np.linalg.norm(centres[0]-centres[1]);stage=Matrix.Diagonal((scale,scale,scale,1));stage.translation=Vector(target-mean*scale)
  for ob in col.all_objects:ob.parent=None;ob.matrix_world=stage@original[ob.name]
  clay=bpy.data.materials.new('AFN104_SOURCE_REFERENCE_CLAY');clay.use_nodes=True;clay.node_tree.nodes.clear();bs=clay.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=clay.node_tree.nodes.new('ShaderNodeOutputMaterial');clay.node_tree.links.new(bs.outputs['BSDF'],out.inputs['Surface']);bs.inputs['Base Color'].default_value=(.28,.28,.28,1);bs.inputs['Roughness'].default_value=.6
  for ob in col.all_objects:
   if ob.type=='MESH':
    ob.data.materials.clear();ob.data.materials.append(clay)
    for f in ob.data.polygons:f.material_index=0;f.use_smooth=True
  bpy.context.view_layer.update();d,W,T=geom(mesh);raw=q.arr(mesh.data.vertices,'co',len(mesh.data.vertices),3);mesh.data.calc_loop_triangles();rawT=q.arr(mesh.data.loop_triangles,'vertices',len(mesh.data.loop_triangles),3,dtype='i4');arrays={'world':W,'triangles':T,'rawLocal':raw,'rawTriangles':rawT};parts={}
  for ob in col.all_objects:
   if ob.type=='MESH' and ob!=mesh:
    _,PP,TT=geom(ob);arrays[ob.name+'-world']=PP;arrays[ob.name+'-triangles']=TT;parts[ob.name]={'vertices':len(PP),'triangles':len(TT),'bounds':[PP.min(0),PP.max(0)]}
  np.savez_compressed(E/(tag+'-actual-source-geometry.npz'),**arrays);reports[tag]={'source':str(P),'sourceSha256':hashlib.sha256(P.read_bytes()).hexdigest(),'collection':colname,'object':mesh.name,'metadata':metadata,'rawVertices':len(raw),'evaluatedVertices':len(W),'evaluatedTriangles':len(T),'bounds':[W.min(0),W.max(0)],'originalWorldMatrix':np.array(original[mesh.name]),'stageWorldMatrix':np.array(stage),'evaluatedWorldMatrix':np.array(mesh.matrix_world),'stageUniformScale':scale,'pairedParts':parts,'referenceOnlyNotNewWomanOrAppearanceGain':True};save('native-head-references.json',reports)
  views=[]
  for view in ['face','profile']:views.append(v.image('native-'+tag+'-reference',view));save(tag+'-reference-view-controls.json',views)
  print('R104_ACTUAL_SOURCE_HEAD_INSPECT',tag,flush=True)
 print('R104_NATIVE_HEAD_REFERENCE_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
