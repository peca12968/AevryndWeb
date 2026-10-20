"""Complete woman: finite fibres with constant parent-family offsets.
Original paths, material and root-frame program retained. Derivative-cone
packing is a scoped neutral inter-child design, not global groom clearance.
"""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time,math
R=Path(r'D:\Download\Aevrynd');S=R/'engine/assets/characters/female-next/source';E=R/'Evidence/character-female-next/r0080-cone-offsets';SRC=S/'aevrynd-female-next-r0076-a-proximal-crown-sculpt-study.blend';OUT=S/'aevrynd-female-next-r0080-a-cone-offset-filaments.blend';SHA='bd8e5bb124756aa486a6a00b26a2a5cf2ca4438cf122ef3a756b172d1c3ba3f5'
def module(n,f):
 sp=importlib.util.spec_from_file_location(n,Path(__file__).with_name(f));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
q=module('cone80data','qualify-female-next-r0075-dental-motion.py');m=module('cone80render','build-female-next-r0074-oral-controls.py');m.E=E;m.m.shade.g.E=E
DIAMETER=math.sqrt(79.3*49.2)*1e-6;GAP=6e-6
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(E/n).write_text(json.dumps(v,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else x.tolist())+'\n',encoding='utf-8')
def bezier_cp(x):
 a=np.concatenate((x[:1],x[:-1]));d=np.concatenate((x[1:],x[-1:]));b=x[:-1];c=x[1:];return np.stack((b,b+(x[1:]-a[:-1])/6,c-(d[1:]-x[:-1])/6,c),axis=1)
def main():
 tick=time.time();assert not OUT.exists() and sha(SRC)==SHA;bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);m.m.shade.settings();o=bpy.data.objects['AFN68_MAIN_RENDER_CURVES'];old=o.data;A=np.array(o.matrix_world);AI=np.linalg.inv(A);sv=np.linalg.svd(A[:3,:3],compute_uv=False);local=q.arr(old.position_data,'vector',len(old.position_data),3).astype('f8');world=local@A[:3,:3].T+A[:3,3];counts=np.array([c.points_length for c in old.curves],dtype='i4');starts=np.r_[0,np.cumsum(counts)[:-1]];oldr=q.arr(old.attributes['radius'].data,'value',len(local));assert s.render.hair_type=='CYLINDER' and s.render.hair_subdiv==0
 oldattrs=[]
 for at in old.attributes:
  if at.name in ('position','radius'):continue
  if at.data_type in ('FLOAT_VECTOR','FLOAT_COLOR','BYTE_COLOR'):width=3 if at.data_type=='FLOAT_VECTOR' else 4;prop='vector' if width==3 else 'color';dtype='f4'
  elif at.data_type in ('FLOAT','INT','BOOLEAN','INT8'):width=1;prop='value';dtype='f4' if at.data_type=='FLOAT' else 'i4'
  else:continue
  oldattrs.append((at.name,at.data_type,at.domain,prop,q.arr(at.data,prop,len(at.data),width,dtype).copy()))
 P=[];radii=[];curveParent=[];pointParent=[];childIDs=[];offsets=[];plans=[];childCounts=[]
 for i,(st,n) in enumerate(zip(starts,counts)):
  x=world[st:st+n];xl=local[st:st+n];cp=bezier_cp(x);deriv=3*np.diff(cp,axis=1).reshape(-1,3);axis=x[-1]-x[0];axis/=np.linalg.norm(axis);length=np.linalg.norm(deriv,axis=1);cos=float(np.min(deriv@axis/np.maximum(length,1e-30)));t=np.empty_like(xl);t[0]=xl[1]-xl[0];t[-1]=xl[-1]-xl[-2];t[1:-1]=xl[2:]-xl[:-2];t/=np.linalg.norm(t,axis=1)[:,None];area=abs(np.linalg.det(A[:3,:3]))/np.linalg.norm(t@A[:3,:3].T,axis=1);rr=(DIAMETER/2)/np.sqrt(area);rr[-2]*=.8;rr[-1]=5e-6/math.sqrt(area[-1]);radcp=bezier_cp(rr[:,None])[:,:,0];rmax=float(max(rr.max(),radcp.max())*sv.max());envelope=float(oldr[st:st+n].min()*sv.min());k=1;spacing=0.
  if cos>0.:
   spacing=(2*rmax+GAP)/cos
   if spacing/math.sqrt(3)+rmax<=envelope:k=3
   elif spacing/2+rmax<=envelope:k=2
  u=np.cross(axis,np.eye(3)[np.argmin(abs(axis))]);u/=np.linalg.norm(u);v=np.cross(axis,u)
  if k==3:angles=np.arange(3)*2*np.pi/3;off=(np.cos(angles)[:,None]*u+np.sin(angles)[:,None]*v)*(spacing/math.sqrt(3))
  elif k==2:off=np.array([-u,u])*spacing/2
  else:off=np.zeros((1,3))
  for j,delta in enumerate(off):
   target=x+delta;native=target@AI[:3,:3].T+AI[:3,3];P.append(native.astype('f4'));radii.append(rr.astype('f4'));curveParent.append(i);pointParent.append(np.arange(st,st+n,dtype='i4'));childIDs.append(j);offsets.append(delta);childCounts.append(n)
  plans.append({'sourceBundle':i,'children':k,'axis':axis.tolist(),'derivativeControlCosineLowerBound':cos,'maximumWorldRadiusUpperBoundM':rmax,'sourceInscribedEnvelopeRadiusM':envelope,'spacingM':spacing if k>1 else 0.,'idealFamilyClearanceLowerBoundM':spacing*cos-2*rmax if k>1 else None,'noPackingMeansSinglePreservedGuide':k==1})
 P=np.concatenate(P);radii=np.concatenate(radii);pointParent=np.concatenate(pointParent);curveParent=np.array(curveParent,'i4');childIDs=np.array(childIDs,'i4');offsets=np.array(offsets);d=bpy.data.hair_curves.new('AFN80_CONSTANT_OFFSET_FINITE_FIBRES');d.add_curves([int(v) for v in childCounts]);d.position_data.foreach_set('vector',P.ravel());at=d.attributes.new('radius','FLOAT','POINT');at.data.foreach_set('value',radii)
 for name,kind,domain,prop,values in oldattrs:
  if domain not in ('POINT','CURVE'):continue
  parent=pointParent if domain=='POINT' else curveParent;at=d.attributes.get(name) or d.attributes.new(name,kind,domain);at.data.foreach_set(prop,values[parent].ravel())
 for name,vals in [('AFN80_SourceBundle',curveParent),('AFN80_RenderChild',childIDs)]:at=d.attributes.new(name,'INT','CURVE');at.data.foreach_set('value',vals)
 for mat in old.materials:d.materials.append(mat)
 o.data=d;o['AFN80_scope']='Constant parent-family offsets, finite reference-derived fibre size, preserved original affine object and root-frame program/material. Derivative cone allows2/3 children only when finite-radius packing fits the original inscribed envelope; other guides retained as single fibres. Neutral within-family construction only, not follicles, between-family/body contact, natural dynamics or engine.';s['AFN80_scope']=o['AFN80_scope'];bpy.context.view_layer.update();actual=q.hair(o);assert np.isfinite(actual).all();target=world[pointParent]+np.repeat(offsets,np.array(childCounts),axis=0);constructionError=float(np.linalg.norm(actual-target,axis=1).max());assert constructionError<2e-6
 np.savez_compressed(E/'a-lineage.npz',sourceLocal=local.astype('f4'),sourceWorld=world,sourceMatrix=A,sourceCounts=counts,sourceRadius=oldr,childCounts=np.array(childCounts,'i4'),curveParent=curveParent,pointParent=pointParent,childIDs=childIDs,constantWorldOffsets=offsets,actualNativeRadii=radii)
 save('a-construction.json',{'plans':plans,'formula':'All original Catmull-Rom derivative Bernstein vectors lie in convex cone(axis,cos). All parent chords then lie in that cone. A constant perpendicular offset delta gives cross-parameter centre distance at least abs(delta)*cos. Subtract two finite radius upper bounds and quantization allowance. Only distinct children of the same parent, neutral pose.','catmullRomBezierConversionAuthoredIndependently':True,'noRootPathRelocationOrGuideDeletion':True,'worldPositionsAfterExistingRootProgramErrorM':constructionError,'interFamilyBodyFollicleDynamicAcceptance':False})
 m.m.k.b.camera('face');s.camera.data.lens=85;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True);hist={str(k):sum(p['children']==k for p in plans) for k in (1,2,3)};save('a-build-summary.json',{'source':str(SRC),'sourceSha256':SHA,'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'sourceCurves':len(counts),'sourcePoints':len(local),'actualCurves':len(childCounts),'actualPoints':len(P),'childrenHistogram':hist,'neutralEquivalentAreaDiameterM':DIAMETER,'minimumIdealWithinFamilyClearanceM':GAP,'originalMaterialObjectFrameAndRootProgramUnchanged':True,'bodyFaceOralFlyawayLightExposureUnedited':True,'rendererCurveTypeAttribute':str(d.attributes.get('curve_type')),'secondsBeforePilot':time.time()-tick});rows=[]
 for view in ('face','body-face'):rows.append(m.render('a-pilot',view));save('a-pilot-controls.json',rows)
 print('R80_COMPLETE_CONSTANT_OFFSET_PREVIEW',hist,time.time()-tick,flush=True)
if __name__=='__main__':main()
