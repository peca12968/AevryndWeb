"""Replace incompatible UDIM surface branches on the same native whole woman.
Keep exact original diffuse branch, geometry, fibres, optics, lights and exposure.
Own rest-coordinate pore/roughness authoring, not an addon or a parameter sweep.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,time,datetime,importlib.util
R=Path('D:/Download/Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0121-native-skin-surface';SRC=S/'r0117-source/aevrynd-female-next-r0117-a-native-fibre-brows.blend';OUT=S/'r0121-source/aevrynd-female-next-r0121-a-native-skin-surface.blend'
sp=importlib.util.spec_from_file_location('r121base',Path(__file__).with_name('build-female-next-r0116-native-eye-character.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;q=a.q;b.u.v.E=E
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,ensure_ascii=False,default=lambda z:z.tolist() if isinstance(z,np.ndarray) else z.item())+'\n',encoding='utf-8',newline='\n')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def UVs(ob):return {u.name:a.hasharray(q.arr(u.data,'uv',len(ob.data.loops),2)) for u in ob.data.uv_layers}
def field(ob,name,kind,values):
 at=ob.data.attributes.new(name=name,type=kind,domain='POINT');at.data.foreach_set('vector' if kind=='FLOAT_VECTOR' else 'value',np.asarray(values,dtype='f4').ravel());return at
def main():
 tick=time.time();assert not OUT.exists();bpy.ops.wm.open_mainfile(filepath=str(SRC));b.deliver(0.);before=a.protected();skin=bpy.data.objects['AFN113_COMPLETE_WOMAN_COHERENT_HEAD'];oldUV=UVs(skin);old=skin.data.materials[8];A=np.array(skin.matrix_world);co=q.arr(skin.data.vertices,'co',len(skin.data.vertices),3);world=co@A[:3,:3].T+A[:3,3];existingNames=sorted(m.name for m in bpy.data.materials);sourceHash=sha(SRC)
 # The r115 native UV chart was copied into the old Vitruvian-named layer.
 native=q.arr(skin.data.uv_layers['MakeHumanOriginalUV'].data,'uv',len(skin.data.loops),2);stale=q.arr(skin.data.uv_layers['VitruvianUV.UDIM'].data,'uv',len(skin.data.loops),2);assert np.array_equal(native,stale)
 # Full stable rest coordinate on the actual displayed skin, no UV seam or
 # projected old-body lookup. It interpolates with the same surface under keys.
 field(skin,'AFN121_SkinRestMetres','FLOAT_VECTOR',world)
 x,y,z=world.T
 front=np.clip((-y-.065)/.045,0,1)
 head=np.clip((z-1.29)/.06,0,1)
 forehead=np.exp(-((x/.050)**4)-((z-1.535)/.036)**4)*front
 nose=np.exp(-((x/.014)**4)-((z-1.437)/.045)**4)*front
 lips=np.exp(-((x/.027)**6)-((z-1.381)/.0085)**4)*front
 region=np.maximum(forehead,nose)
 rough=np.clip(.48-.11*region-.16*lips,.28,.52)
 field(skin,'AFN121_RegionalRoughness','FLOAT',rough)
 # Approximate authored skin microstructure, all lengths in rest metres.
 # Neither pore dimensions nor regional roughness claim subject measurement.
 mat=old.copy();mat.name='AFN121_NATIVE_REST_SKIN_SURFACE';skin.data.materials[8]=mat;N=mat.node_tree.nodes;L=mat.node_tree.links;p=next(n for n in N if n.bl_idname=='ShaderNodeBsdfPrincipled')
 priorBase=[(l.from_node.name,l.from_socket.name) for l in p.inputs['Base Color'].links]
 priorInputs={name:[(l.from_node.name,l.from_socket.name) for l in p.inputs[name].links] for name in ['Roughness','Normal']}
 for name in ['Roughness','Normal']:
  for link in list(p.inputs[name].links):L.remove(link)
 coord=N.new('ShaderNodeAttribute');coord.name='AFN121_STABLE_SURFACE_COORDINATE';coord.attribute_name='AFN121_SkinRestMetres';coord.location=(-900,-600)
 reg=N.new('ShaderNodeAttribute');reg.name='AFN121_AUTHORED_REGIONAL_ROUGHNESS';reg.attribute_name='AFN121_RegionalRoughness';reg.location=(-650,-300)
 pore=N.new('ShaderNodeTexVoronoi');pore.name='AFN121_OWN_PORE_MICROHEIGHT';pore.feature='F1';pore.distance='EUCLIDEAN';pore.voronoi_dimensions='3D';pore.inputs['Scale'].default_value=2200.;pore.inputs['Randomness'].default_value=1.;pore.location=(-650,-600);L.new(coord.outputs['Vector'],pore.inputs['Vector'])
 noise=N.new('ShaderNodeTexNoise');noise.name='AFN121_LOCAL_SEBUM_VARIATION';noise.noise_dimensions='3D';noise.inputs['Scale'].default_value=600.;noise.inputs['Detail'].default_value=2.;noise.inputs['Roughness'].default_value=.5;noise.location=(-650,-900);L.new(coord.outputs['Vector'],noise.inputs['Vector'])
 subtract=N.new('ShaderNodeMath');subtract.operation='SUBTRACT';subtract.inputs[1].default_value=.5;L.new(noise.outputs['Fac'],subtract.inputs[0])
 multiply=N.new('ShaderNodeMath');multiply.operation='MULTIPLY';multiply.inputs[1].default_value=.06;L.new(subtract.outputs[0],multiply.inputs[0])
 add=N.new('ShaderNodeMath');add.name='AFN121_LOCAL_ROUGHNESS';add.operation='ADD';L.new(reg.outputs['Fac'],add.inputs[0]);L.new(multiply.outputs[0],add.inputs[1]);L.new(add.outputs[0],p.inputs['Roughness'])
 bump=N.new('ShaderNodeBump');bump.name='AFN121_MICROMETRE_SURFACE_NORMAL';bump.inputs['Strength'].default_value=1.;bump.inputs['Distance'].default_value=.000035;L.new(pore.outputs['Distance'],bump.inputs['Height']);L.new(bump.outputs['Normal'],p.inputs['Normal'])
 assert [(l.from_node.name,l.from_socket.name) for l in p.inputs['Base Color'].links]==priorBase
 mat['AFN121_scope']='Own approximate regional roughness and35um-distance microheight using actual native skin rest-metre attribute. Exact old diffuse path/IOR/SSS preserved. Not measured subject material, physical displacement, anatomy/contact/dynamics/runtime qualification.'
 skin['AFN121_surface_authoring']='Stable point rest-coordinate and approximate regional roughness fields; original geometry and all keys/UV/fibres exact; shader bump only, no geometric displacement.'
 bpy.context.view_layer.update();after=a.protected();assert before==after;assert UVs(skin)==oldUV
 assert np.isfinite(world).all() and np.isfinite(rough).all()
 np.savez_compressed(E/'skin-surface-authoring-lineage.npz',restWorldMetres=world.astype('f4'),regionalRoughness=rough.astype('f4'),sourceNativeUV=native)
 b.deliver(0.);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True,relative_remap=False);assert sha(SRC)==sourceHash
 save('a-build-summary.json',{'source':str(SRC),'output':str(OUT),'bytes':OUT.stat().st_size,'sha256':sha(OUT),'sourceSha256':sourceHash,'startedAuthoringUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'incompatibleNamedUVLayerExactlyEqualsNativeUV':True,'surfaceFoundationChanged':'Inherited Vitruvian UDIM roughness/height references were evaluated on an unrelated native chart. Those two active branches alone now use own actual-skin rest-coordinate construction and approximate authored regional roughness.','unchangedNativeDiffuseBranch':priorBase,'oldActiveSurfaceInputLinks':priorInputs,'allOriginalGeometryKeysFibresBefore':before,'allOriginalGeometryKeysFibresAfter':after,'allOriginalGeometryKeysFibresByteExact':True,'allUVHashesUnchanged':oldUV,'allOtherExistingMaterialsUnmodified':existingNames,'physicalApproximation':{'poreCellFrequencyPerMetre':2200.,'bumpDistanceMetres':.000035,'roughnessRange':list(map(float,[rough.min(),rough.max()])),'localRoughnessVariationScalePerMetre':600.,'notMeasuredSubjectCalibration':True},'shaderNormalNotFiniteDisplacement':True,'noAddedOrRemovedFibreOrChangedRadii':True,'noNewGeometryContactClaim':True,'secondsBeforePreview':time.time()-tick})
 rows=[]
 for view in ['face','body-face','oblique','profile','back']:
  rows.append(b.u.v.image('a-native-skin-surface',view));save('a-view-controls.json',rows)
 for label,value in [('half',.5),('closed',1.),('restored',0.)]:
  b.deliver(value);rows.append(b.u.v.image('a-native-skin-surface-'+label,'face'));save('a-view-controls.json',rows)
 print('R121_COMPLETE_NATIVE_SKIN_SURFACE_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
