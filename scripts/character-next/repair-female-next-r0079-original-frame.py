"""Repair B coordinate-space adaptation, preserving the original root-frame program.
Same B filament construction/control, not another appearance hypothesis.
Neutral world section area is calibrated under the retained affine object scale;
world sections are explicitly elliptical, not falsely claimed circular.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Matrix
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0079-physical-filaments';OUT=S/'aevrynd-female-next-r0079-b-original-frame-filaments.blend'
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
q=module('frame79data','qualify-female-next-r0075-dental-motion.py');m=module('frame79render','build-female-next-r0074-oral-controls.py');m.E=E;m.m.shade.g.E=E

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(E/n).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def main():
 tick=time.time();b=q.read(E/'b-build-summary.json');control=q.read(E/'b-source-material-control-summary.json');assert not OUT.exists() and sha(Path(b['source']))==b['sourceSha256'];bpy.ops.wm.open_mainfile(filepath=b['source']);ng=bpy.data.objects['AFN68_MAIN_RENDER_CURVES'].modifiers['AFN69_LIVE_RENDER_SCALP_FRAME'].node_group;constants=[]
 for n in ng.nodes:
  if n.bl_idname!='ShaderNodeVectorMath':continue
  for i,s in enumerate(n.inputs):
   if s.type=='VECTOR' and not s.is_linked:constants.append({'node':n.name,'index':i,'operation':n.operation,'value':list(s.default_value)})
 bpy.ops.wm.open_mainfile(filepath=control['output']);s=bpy.context.scene;s.frame_set(1);o=bpy.data.objects['AFN68_MAIN_RENDER_CURVES'];z=np.load(E/'b-AFN68_MAIN_RENDER_CURVES-physical-lineage.npz');A=z['sourceMatrix'];inv=np.linalg.inv(A);P=q.arr(o.data.position_data,'vector',len(o.data.position_data),3).astype('f8');local=P@inv[:3,:3].T+inv[:3,3];counts=np.array([c.points_length for c in o.data.curves]);starts=np.r_[0,np.cumsum(counts)[:-1]];tangent=np.empty_like(local)
 for n in np.unique(counts):
  ids=starts[counts==n,None]+np.arange(n)[None,:];x=local[ids];t=np.empty_like(x);t[:,0]=x[:,1]-x[:,0];t[:,-1]=x[:,-1]-x[:,-2];t[:,1:-1]=x[:,2:]-x[:,:-2];t/=np.linalg.norm(t,axis=2)[:,:,None];tangent[ids]=t
 stretch=np.linalg.norm(tangent@A[:3,:3].T,axis=1);areaScale=abs(np.linalg.det(A[:3,:3]))/stretch;worldRadius=q.arr(o.data.attributes['radius'].data,'value',len(P));localRadius=worldRadius/np.sqrt(areaScale);o.data.position_data.foreach_set('vector',local.astype('f4').ravel());o.data.attributes['radius'].data.foreach_set('value',localRadius.astype('f4'));o.matrix_world=Matrix(A.tolist());md=o.modifiers['AFN69_LIVE_RENDER_SCALP_FRAME'];ng=md.node_group.copy();ng.name='AFN79_ORIGINAL_AFFINE_FRAME_'+o.name
 for row in constants:
  n=ng.nodes[row['node']];assert n.operation==row['operation'];n.inputs[row['index']].default_value=row['value']
 md.node_group=ng;o['AFN79_scope']='B three-child projected-coverage geometry, restored original affine root-frame program. Family mean retains original guide under the existing program; neutral area-equivalent world diameter calibrated, cross sections are affine ellipses. Original active proxy material retained. No follicle, self/body contact, natural dynamics or runtime acceptance.';bpy.context.view_layer.update();actual=q.hair(o);restError=float(np.linalg.norm(actual-P,axis=1).max());assert restError<2e-6
 save('b-original-frame-construction.json',{'sourceControl':control['output'],'sourceControlSha256':control['outputSha256'],'sourceOriginalGuide':b['source'],'sourceOriginalGuideSha256':b['sourceSha256'],'sameBGeometryConstruction':True,'worldNativeCenterPointsPreservedWithinM':restError,'originalObjectMatrix':A.tolist(),'originalVectorNodeConstantsRestored':len(constants),'neutralSectionAreaScaleFormula':'abs(det(A))/length(A*unit_local_tangent)','worldSectionsAreAffineEllipsesNotCircles':True,'normalizationWasNotAcceptedAsPreservedMotion':True,'dynamicSectionAreaOrPhysicalStretchNotCalibrated':True})
 np.savez_compressed(E/'b-original-frame-radius-lineage.npz',neutralLocalTangent=tangent.astype('f4'),areaScale=areaScale.astype('f4'),physicalAreaEquivalentWorldRadius=worldRadius,actualLocalRadius=localRadius.astype('f4'),sourceMatrix=A)
 m.m.k.b.camera('face');s.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;s['AFN79_fixed_scope']='Same B geometry/control with original affine root-frame program restored. Neutral area-equivalent filament size, original material; no full contact, natural motion or runtime acceptance.';bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);save('b-original-frame-build-summary.json',{'source':control['output'],'sourceSha256':control['outputSha256'],'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'sameBMethodImplementationCorrection':True,'originalCompleteSource':b['source'],'originalCompleteSha256':b['sourceSha256'],'secondsBeforePilot':time.time()-tick});rows=[]
 for view in ('face','body-face'):rows.append(m.render('b-original-frame',view));save('b-original-frame-views.json',rows)
 print('R79_B_ORIGINAL_FRAME_REPAIRED',restError,time.time()-tick,flush=True)
if __name__=='__main__':main()
