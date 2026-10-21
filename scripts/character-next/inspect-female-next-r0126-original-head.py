"""Actual original licensed artist head/eyes/hair/materials before adaptation."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,datetime,time
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0126-individual-head-foundation';S=R/'engine/assets/characters/female-next/source';D=S/'r0126-source/individual-head-input';GLB=D/'artist-head-27f75fa94c384000bb6a79a3000f8e80.glb'
sp=importlib.util.spec_from_file_location('r126original',Path(__file__).with_name('build-female-next-r0116-native-eye-character.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;b.u.v.E=E
def save(n,d):(E/n).write_text(json.dumps(d,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item())+'\n',encoding='utf-8',newline='\n')
def main():
 tick=time.time();save('individual-foundation-work-start.json',{'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Import and directly stage actual complete original Angelica3D head/eyes/mouth/hair/UV/material source. Inspect native construction before adaptation to the same full woman.'});bpy.ops.wm.open_mainfile(filepath=str(S/'r0117-source/aevrynd-female-next-r0117-a-native-fibre-brows.blend'));before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(GLB));new=set(bpy.data.objects)-before;meshes=[o for o in new if o.type=='MESH'];data={};eye=next(o for o in meshes if o.name.startswith('Eye_Eye_'));_,W,T=b.u.b.geom(eye);left=W[W[:,0]<0].mean(0);right=W[W[:,0]>0].mean(0);sourceMean=(left+right)*.5;ipd=np.linalg.norm(right-left);scale=.0599392/ipd;target=np.array([0.,-.1099238,1.4629877]);M=np.eye(4);M[:3,:3]*=scale;M[:3,3]=target-sourceMean*scale
 for ob in new:
  A=ob.matrix_world.copy();ob.parent=None;ob.matrix_world=A;ob.name='AFN126_ORIGINAL_'+ob.name
 for ob in meshes:ob.matrix_world=__import__('mathutils').Matrix(M.tolist())@ob.matrix_world
 for ob in before:
  if ob.type in ['MESH','CURVES','CURVE','SURFACE']:ob.hide_render=True
 for ob in meshes:
  ob.hide_render=False;ob.hide_set(False);d,W,T=b.u.b.geom(ob);data[ob.name]={'vertices':len(W),'triangles':len(T),'boundsWorld':[W.min(0),W.max(0)],'uvLayers':[x.name for x in d.uv_layers],'materials':[x.name if x else None for x in d.materials],'shapeKeys':[x.name for x in ob.data.shape_keys.key_blocks] if ob.data.shape_keys else [],'modifiers':[(x.name,x.type) for x in ob.modifiers]};np.savez_compressed(E/(ob.name+'-original-geometry.npz'),world=W,triangles=T)
 save('original-artist-head-inspection.json',{'fullGLB':str(GLB),'sha256':a.sha(GLB),'sourceEyeMeans':[left,right],'sourceIPD':float(ipd),'stageWorldTransform':M,'sourceUniformScaleOnly':True,'sourceParts':data,'allOriginalSurfaceUVAndImportedMaterialsPreserved':True,'sourceShapeOrVertexTopologyEdited':False,'newActualCompleteWomanCandidate':False,'appearanceOrFunctionContactRuntimeAdopted':False})
 rows=[]
 for view in ['face','oblique','profile']:
  rows.append(b.u.v.image('original-artist-head-reference',view));save('original-reference-view-controls.json',rows)
 print('R126_ACTUAL_ORIGINAL_HEAD_REFERENCE_READY',scale,len(meshes),time.time()-tick,flush=True)
if __name__=='__main__':main()
