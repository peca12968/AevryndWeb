"""B geometry-only ablation with the exact original active hair material.
A control of an already-built geometry method, not a fourth authoring method.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0079-physical-filaments';OUT=S/'aevrynd-female-next-r0079-b-source-material-control.blend';sp=importlib.util.spec_from_file_location('control79render',Path(__file__).with_name('build-female-next-r0074-oral-controls.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);m.E=E;m.m.shade.g.E=E
qsp=importlib.util.spec_from_file_location('control79data',Path(__file__).with_name('qualify-female-next-r0075-dental-motion.py'));q=importlib.util.module_from_spec(qsp);qsp.loader.exec_module(q)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(E/n).write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def main():
 tick=time.time();b=q.read(E/'b-build-summary.json');assert not OUT.exists() and sha(Path(b['output']))==b['outputSha256'];bpy.ops.wm.open_mainfile(filepath=b['source']);o=bpy.data.objects['AFN68_MAIN_RENDER_CURVES'];old={}
 for at in o.data.attributes:
  if at.domain!='POINT' or at.name in ('position','radius'):continue
  kind=at.data_type
  if kind in ('FLOAT_VECTOR','FLOAT_COLOR','BYTE_COLOR'):width=3 if kind=='FLOAT_VECTOR' else 4;prop='vector' if width==3 else 'color';dtype='f4'
  elif kind in ('FLOAT','INT','BOOLEAN','INT8'):width=1;prop='value';dtype='f4' if kind=='FLOAT' else 'i4'
  else:continue
  old[at.name]=(kind,prop,q.arr(at.data,prop,len(at.data),width,dtype=dtype).copy())
 bpy.ops.wm.open_mainfile(filepath=b['output']);bpy.context.scene.frame_set(1);o=bpy.data.objects['AFN68_MAIN_RENDER_CURVES'];lineage=np.load(E/'b-AFN68_MAIN_RENDER_CURVES-physical-lineage.npz');counts=lineage['counts'];starts=np.r_[0,np.cumsum(counts)[:-1]];parent=np.concatenate([np.tile(np.arange(st,st+n,dtype='i4'),3) for st,n in zip(starts,counts)]);copied=[]
 for name,(kind,prop,values) in old.items():
  if o.data.attributes.get(name):continue
  at=o.data.attributes.new(name,kind,'POINT');at.data.foreach_set(prop,values[parent].ravel());copied.append(name)
 original=bpy.data.materials['Brown hair'];o.data.materials[0]=original;o['AFN79_control_scope']='Exact B physical fibre positions/radii/root-frame representation; original active hair material restored, original point shader metadata propagated. No added geometry construction, new absorption model, dynamics/contact or runtime acceptance.';bpy.context.scene['AFN79_control_scope']='B geometry-only source-material ablation. Not a fourth authoring method or accepted physical-scattering implementation.';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
 save('b-source-material-control-summary.json',{'source':b['output'],'sourceSha256':b['outputSha256'],'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'isControlOfExistingGeometryMethodB':True,'newGeometryConstruction':False,'originalActiveMaterial':'Brown hair','preservedPointShaderMetadata':copied,'sourceOriginalBodyAndLightUnedited':True,'secondsBeforePilot':time.time()-tick});rows=[]
 for view in ('face','body-face'):rows.append(m.render('b-source-material-control',view));save('b-source-material-control-views.json',rows)
 print('R79_B_GEOMETRY_ONLY_CONTROL_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
