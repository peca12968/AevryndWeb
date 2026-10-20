"""One physical filament representation on the complete r76 woman.
Seven finite render fibres per former coarse strand; centre guides and original
root-frame lineage retained. Circular world units, authored finite tip taper,
absorbing Chiang BSDF. Not a follicle, dynamics or engine implementation.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time,math,sys
from mathutils import Matrix
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0079-physical-filaments';SRC=S/'aevrynd-female-next-r0076-a-proximal-crown-sculpt-study.blend';OUT=S/'aevrynd-female-next-r0079-a-physical-filaments-study.blend';SHA='bd8e5bb124756aa486a6a00b26a2a5cf2ca4438cf122ef3a756b172d1c3ba3f5'
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=module('fiber79render','build-female-next-r0074-oral-controls.py');q=module('fiber79data','qualify-female-next-r0075-dental-motion.py');m.E=E;m.m.shade.g.E=E
OPTICAL='--projected-coverage' in sys.argv
TAG='b' if OPTICAL else 'a'
K=3 if OPTICAL else 7
if OPTICAL:OUT=S/'aevrynd-female-next-r0079-b-optical-filaments-study.blend'
D=math.sqrt(79.3*49.2)*1e-6;RAD=D/2;GAP=1.5e-6;SPACE=D+GAP

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(E/n).write_text(json.dumps(v,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else x.tolist())+'\n',encoding='utf-8')
def frames(P,starts,counts):
 normal=np.empty_like(P);binormal=np.empty_like(P)
 for n in np.unique(counts):
  sel=np.flatnonzero(counts==n);ids=starts[sel,None]+np.arange(n)[None,:];x=P[ids];t=np.empty_like(x);t[:,0]=x[:,1]-x[:,0];t[:,-1]=x[:,-1]-x[:,-2];t[:,1:-1]=x[:,2:]-x[:,:-2];t/=np.linalg.norm(t,axis=2)[:,:,None];nn=np.empty_like(x);axis=np.eye(3)[np.argmin(np.abs(t[:,0]),axis=1)];nn[:,0]=np.cross(t[:,0],axis);nn[:,0]/=np.linalg.norm(nn[:,0],axis=1)[:,None]
  for j in range(1,int(n)):
   v=np.cross(t[:,j-1],t[:,j]);c=np.einsum('ij,ij->i',t[:,j-1],t[:,j]);a=nn[:,j-1];a=a+np.cross(v,a)+np.cross(v,np.cross(v,a))/np.maximum(1+c,1e-8)[:,None];a-=t[:,j]*np.einsum('ij,ij->i',a,t[:,j])[:,None];a/=np.linalg.norm(a,axis=1)[:,None];nn[:,j]=a
  normal[ids]=nn;binormal[ids]=np.cross(t,nn)
 return normal,binormal

def material():
 mat=bpy.data.materials.new('AFN79_ABSORBING_CIRCULAR_FILAMENT');mat.use_nodes=True;tree=mat.node_tree;tree.nodes.clear();hair=tree.nodes.new('ShaderNodeBsdfHairPrincipled');hair.name='AFN79_DIELECTRIC_PIGMENT_CHIANG';hair.model='CHIANG';hair.parametrization='COLOR' if OPTICAL else 'MELANIN'
 values={'Melanin':.20454543828964233,'Melanin Redness':0.,'Tint':(1.,1.,1.,1.),'Roughness':.30,'Radial Roughness':.50,'Coat':0.,'IOR':1.55,'Offset':math.radians(2),'Random Color':.04,'Random Roughness':0.,'Weight':1.}
 for name,value in values.items():
  if name in hair.inputs:hair.inputs[name].default_value=value
 if OPTICAL:
  pigment=tree.nodes.new('ShaderNodeAttribute');pigment.attribute_name='AFN79_PigmentReflectance';tree.links.new(pigment.outputs['Color'],hair.inputs['Color'])
  if 'Random Color' in hair.inputs:hair.inputs['Random Color'].default_value=0.
 out=tree.nodes.new('ShaderNodeOutputMaterial');tree.links.new(hair.outputs['BSDF'],out.inputs['Surface']);mat['scope']='Circular-fibre absorbing BSDF; '+('explicit source artist reflectance palette attribute, no scalar-to-grey or unused melanin premise. ' if OPTICAL else 'source unused melanin art value, rejected pale result. ')+'Roughness is an art assumption, not sample-fitted; no Aevrynd implementation.';return mat,values

def make(o,mat):
 old=o.data;oldP=q.arr(old.position_data,'vector',len(old.position_data),3).copy();oldR=q.arr(old.attributes['radius'].data,'value',len(oldP)).copy();counts=np.array([c.points_length for c in old.curves],dtype='i4');starts=np.r_[0,np.cumsum(counts)[:-1]];A=np.array(o.matrix_world);P=oldP.astype('f8')@A[:3,:3].T+A[:3,3];normal,binormal=frames(P,starts,counts);pointParent=np.concatenate([np.tile(np.arange(st,st+n,dtype='i4'),K) for st,n in zip(starts,counts)]);child=np.concatenate([np.repeat(np.arange(K,dtype='i4'),n) for n in counts]);curveParent=np.repeat(np.arange(len(counts),dtype='i4'),K);angle=np.r_[0.,np.arange(6)*2*np.pi/6];cx=np.r_[0.,np.cos(angle[1:])*SPACE];cy=np.r_[0.,np.sin(angle[1:])*SPACE]
 if OPTICAL:
  derived=round(float(oldR.mean()*np.linalg.svd(A[:3,:3],compute_uv=False).mean()*2/D));assert derived==K;phase=np.arange(K)*2*np.pi/K;cx=np.cos(phase)*SPACE/math.sqrt(3);cy=np.sin(phase)*SPACE/math.sqrt(3)
 Q=P[pointParent]+normal[pointParent]*cx[child,None]+binormal[pointParent]*cy[child,None];assert np.isfinite(Q).all()
 newcounts=np.repeat(counts,K);radii=np.full(len(Q),RAD,'f4');newstarts=np.r_[0,np.cumsum(newcounts)[:-1]]
 # An authored taper on the actual last two native edges. No false claim
 # that a millimetre-exact continuous taper was measured or implemented.
 for st,n in zip(newstarts,newcounts):radii[st+n-2]*=.80;radii[st+n-1]=5e-6
 d=bpy.data.hair_curves.new('AFN79_'+o.name+'_WORLD_METRE_FIBRES');d.add_curves(newcounts.tolist());d.position_data.foreach_set('vector',Q.astype('f4').ravel());ra=d.attributes.get('radius') or d.attributes.new('radius','FLOAT','POINT');ra.data.foreach_set('value',radii);copied=[]
 for at in old.attributes:
  if at.name in ('position','radius') or at.domain!='CURVE':continue
  width=3 if at.data_type=='FLOAT_VECTOR' else 1;prop='vector' if width==3 else 'value'
  if at.data_type not in ('FLOAT_VECTOR','FLOAT','INT','BOOLEAN','INT8'):continue
  dtype='f4' if at.data_type in ('FLOAT_VECTOR','FLOAT') else 'i4';vals=q.arr(at.data,prop,len(counts),width,dtype=dtype);vals=vals[curveParent];target=d.attributes.get(at.name) or d.attributes.new(at.name,at.data_type,'CURVE');target.data.foreach_set(prop,vals.ravel());copied.append(at.name)
 for name,vals in [('AFN79_SourceBundle',curveParent),('AFN79_RenderChild',np.tile(np.arange(K,dtype='i4'),len(counts)))]:at=d.attributes.new(name,'INT','CURVE');at.data.foreach_set('value',vals)
 if OPTICAL:
  palette=bpy.data.materials['Brown hair'].node_tree.nodes['Group'];c1=np.array(palette.inputs['Color 1'].default_value);c2=np.array(palette.inputs['Color 2'].default_value);rnd=np.mod(np.sin(curveParent*12.9898+78.233)*43758.5453,1.);colors=c1[None,:]*(1-rnd[:,None])+c2[None,:]*rnd[:,None];at=d.attributes.new('AFN79_PigmentReflectance','FLOAT_COLOR','CURVE');at.data.foreach_set('color',colors.astype('f4').ravel())
 d.materials.append(mat);o.data=d;o.matrix_world=Matrix.Identity(4);md=o.modifiers['AFN69_LIVE_RENDER_SCALP_FRAME'];ng=md.node_group.copy();ng.name='AFN79_WORLD_METRE_'+o.name+'_ORIGINAL_ROOT_FRAMES';oldScale=np.diag(A[:3,:3]);oldShift=A[:3,3];scaleEdits=shiftEdits=0
 for node in ng.nodes:
  if node.bl_idname!='ShaderNodeVectorMath':continue
  for socket in node.inputs:
   if socket.is_linked or socket.type!='VECTOR':continue
   value=np.array(socket.default_value)
   if node.operation in ('MULTIPLY','DIVIDE') and np.max(np.abs(value-oldScale))<1e-7:socket.default_value=(1.,1.,1.);scaleEdits+=1
   elif node.operation in ('ADD','SUBTRACT') and np.max(np.abs(value-oldShift))<1e-7:socket.default_value=(0.,0.,0.);shiftEdits+=1
 assert scaleEdits==12 and shiftEdits==8,(scaleEdits,shiftEdits);md.node_group=ng;o['AFN79_scope']=str(K)+' explicit circular world-metre render fibres per original coarse bundle, source root-frame IDs/barycentrics retained per family; child mean/centre retains source guide. No independently modelled follicles, contact, natural dynamics or runtime acceptance.'
 # Preserve compact lineage rather than duplicate all1.45m child positions.
 np.savez_compressed(E/(TAG+'-'+o.name+'-physical-lineage.npz'),sourceLocal=oldP,sourceWorld=P,sourceRadius=oldR,sourceMatrix=A,counts=counts,normal=normal.astype('f4'),binormal=binormal.astype('f4'),centerChild=-1 if OPTICAL else 0,renderChildren=K,diameterM=D,ringSpacingM=SPACE,tipRadiusM=5e-6)
 bpy.context.view_layer.update();actual=q.hair(o);assert np.linalg.norm(actual-Q,axis=1).max()<2e-6
 return {'object':o.name,'sourceCurves':len(counts),'sourcePoints':len(P),'actualCurves':len(newcounts),'actualPoints':len(Q),'shaftDiameterM':D,'terminalRadiusM':5e-6,'hexRingSpacingM':SPACE,'oldWorldRadiusSingularValueBoundsM':[float(oldR.min()*np.linalg.svd(A[:3,:3],compute_uv=False).min()),float(oldR.max()*np.linalg.svd(A[:3,:3],compute_uv=False).max())],'pointwiseFamilyOuterRadiusAtKnotsM':(SPACE/math.sqrt(3) if OPTICAL else SPACE)+RAD,'actualSavedRestConstructionErrorM':float(np.linalg.norm(actual-Q,axis=1).max()),'guidePreservation':'family mean' if OPTICAL else 'central child','childrenPerSourceBundle':K,'copiedCurveAttributes':copied,'rootFrameScaleConstantsAdapted':scaleEdits,'rootFrameTranslationConstantsAdapted':shiftEdits,'childrenAreRenderInterpolationNotFollicleOrPhysicsEvidence':True}

def main():
 tick=time.time();assert not OUT.exists() and sha(SRC)==SHA;bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.scene.frame_set(1);m.m.shade.settings();mat,params=material();rows=[make(bpy.data.objects[n],mat) for n in (('AFN68_MAIN_RENDER_CURVES',) if OPTICAL else ('AFN68_MAIN_RENDER_CURVES','AFN68_FLYAWAY_RENDER_CURVES'))];s=bpy.context.scene;m.m.k.b.camera('face');s.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;s['AFN79_scope']='Physical filament appearance study, '+str(K)+' render fibres per source bundle. Source guide layout/root frames retained as family mean/centre; no follicle, natural motion, complete contact or runtime acceptance.';bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);save(TAG+'-build-summary.json',{'source':str(SRC),'sourceSha256':SHA,'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'representation':rows,'material':mat.name,'hairBSDF':'CHIANG/COLOR_BOUNDED_SOURCE_REFLECTANCE' if OPTICAL else 'CHIANG/MELANIN','sourceFlyawayNativeDataAndMaterialPreserved':OPTICAL,'densityRationale':'Projected-width quotient round(old mean world diameter/new circular diameter)=3, equilateral micro-bundle mean retains guide. Optical authoring approximation, not measured biological density.' if OPTICAL else 'Seven-fibre hexagonal cross-section fill, visually rejected for excessive coverage and pale response.','materialParameters':params,'noDensityRadiusPigmentSweep':True,'bodyFaceOralLightExposureUnedited':True,'secondsBeforePilot':time.time()-tick});controls=[]
 for view in ('face','body-face'):controls.append(m.render(TAG+'-pilot',view));save(TAG+'-pilot-controls.json',controls)
 print('R79_COMPLETE_PHYSICAL_FILAMENT_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
