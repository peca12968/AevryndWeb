"""Reconstruct the failed neck annulus, rather than merely weld its folds.
Four anatomical quadrant landmarks establish explicit boundary correspondence.
Hermite sections follow the actual body/source-head surface tangents. New
surface shares its boundary vertices and moves in live local neck frames.
"""
from pathlib import Path
import bpy,bmesh,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0099-continuous-head-neck';OLD=E.parent/'r0098-whole-head-foundation';S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0099-a2-continuous-head-neck-materials.blend';OUT=S/'aevrynd-female-next-r0099-b-anatomical-neck-surface.blend'
sp=importlib.util.spec_from_file_location('r99annulus',Path(__file__).with_name('build-female-next-r0099-continuous-skin.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);q=m.q;v=m.v;v.E=E
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,x):(E/n).write_text(json.dumps(x,indent=2,default=lambda a:a.item() if isinstance(a,np.generic) else a.tolist())+'\n',encoding='utf8')
def unit(a):return a/np.linalg.norm(a,axis=-1,keepdims=True)
def parameter(V,loop):
 loop=np.roll(loop,-int(np.argmin(V[loop,1])));p=V[loop];landmarks=[0,int(np.argmax(p[:,0])),int(np.argmax(p[:,1])),int(np.argmin(p[:,0])),len(loop)];assert all(a<b for a,b in zip(landmarks,landmarks[1:])),landmarks;u=np.empty(len(loop))
 for k,(a,b) in enumerate(zip(landmarks,landmarks[1:])):
  ids=np.arange(a,b+1)%len(loop);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p[ids],axis=0),axis=1))];u[a:b]=.25*k+.25*arc[:-1]/arc[-1]
 return loop,u,landmarks
def interpolate(V,loop,u,g):
 ext=np.r_[u,1.];i=np.searchsorted(ext,g,side='right')-1;i=np.minimum(i,len(loop)-1);w=(g-ext[i])/(ext[i+1]-ext[i]);a=loop[i];b=loop[(i+1)%len(loop)];return (1-w[:,None])*V[a]+w[:,None]*V[b],a,b,w
def normals(V,T):
 N=np.zeros_like(V);cross=np.cross(V[T[:,1]]-V[T[:,0]],V[T[:,2]]-V[T[:,0]])
 for j in range(3):np.add.at(N,T[:,j],cross)
 length=np.linalg.norm(N,axis=1);N[length>0]/=length[length>0,None];return N
def strip(lower,lu,upper,uu):
 i=j=0;faces=[];le=np.r_[lu,1.];ue=np.r_[uu,1.]
 while i<len(lower) or j<len(upper):
  a=int(lower[i%len(lower)]);b=int(upper[j%len(upper)])
  if j==len(upper) or (i<len(lower) and le[i+1]<=ue[j+1]):faces.append([a,int(lower[(i+1)%len(lower)]),b]);i+=1
  else:faces.append([a,int(upper[(j+1)%len(upper)]),b]);j+=1
 return np.array(faces,'i4')
def patch_nodes(ob,skin,head):
 ng=bpy.data.node_groups.new('AFN99_LIVE_ANATOMICAL_NECK_FRAME','GeometryNodeTree');ng.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');ng.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');n=ng.nodes;L=ng.links;inp=n.new('NodeGroupInput');out=n.new('NodeGroupOutput')
 def attr(name,kind='FLOAT'):
  a=n.new('GeometryNodeInputNamedAttribute');a.data_type=kind;a.inputs['Name'].default_value=name;return a.outputs['Attribute']
 def math(op,a,b=None):
  x=n.new('ShaderNodeMath');x.operation=op
  for i,val in enumerate([a,b] if b is not None else [a]):
   if isinstance(val,(int,float)):x.inputs[i].default_value=val
   else:L.new(val,x.inputs[i])
  return x.outputs[0]
 def vec(op,a,b=None):
  x=n.new('ShaderNodeVectorMath');x.operation=op;L.new(a,x.inputs[0])
  if b is not None:L.new(b,x.inputs[3] if op=='SCALE' else x.inputs[1])
  return x.outputs['Value' if op=='DOT_PRODUCT' else 'Vector']
 def mix(a,b,w):return vec('ADD',vec('SCALE',a,math('SUBTRACT',1,w)),vec('SCALE',b,w))
 positions=[]
 for source,prefix in [(skin,'S'),(head,'H')]:
  info=n.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE';info.inputs['Object'].default_value=source;info.inputs['As Instance'].default_value=False;pos=n.new('GeometryNodeInputPosition')
  for j in range(2):
   sample=n.new('GeometryNodeSampleIndex');sample.data_type='FLOAT_VECTOR';sample.domain='POINT';sample.clamp=False;L.new(info.outputs['Geometry'],sample.inputs['Geometry']);L.new(pos.outputs['Position'],sample.inputs['Value']);L.new(attr('AFN99_Patch'+prefix+str(j),'INT'),sample.inputs['Index']);positions.append(sample.outputs['Value'])
 s0,s1,h0,h1=positions;t=attr('AFN99_PatchT');low=mix(s0,s1,attr('AFN99_PatchSW'));high=mix(h0,h1,attr('AFN99_PatchHW'));tangent=vec('NORMALIZE',mix(vec('SUBTRACT',s1,s0),vec('SUBTRACT',h1,h0),t));axial=vec('SUBTRACT',high,low);z=vec('NORMALIZE',vec('SUBTRACT',axial,vec('SCALE',tangent,vec('DOT_PRODUCT',axial,tangent))));normal=vec('NORMALIZE',vec('CROSS_PRODUCT',tangent,z));coef=attr('AFN99_PatchCoefficients','FLOAT_VECTOR');xyz=n.new('ShaderNodeSeparateXYZ');L.new(coef,xyz.inputs[0]);delta=vec('ADD',vec('ADD',vec('SCALE',tangent,xyz.outputs[0]),vec('SCALE',z,xyz.outputs[1])),vec('SCALE',normal,xyz.outputs[2]));position=vec('ADD',mix(low,high,t),delta);setpos=n.new('GeometryNodeSetPosition');L.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);L.new(attr('AFN99_IsPatch','BOOLEAN'),setpos.inputs['Selection']);L.new(position,setpos.inputs['Position']);L.new(setpos.outputs['Geometry'],out.inputs['Geometry']);md=ob.modifiers.new('AFN99_LIVE_NECK_CURVATURE_FRAME','NODES');md.node_group=ng
def main():
 tick=time.time();assert not OUT.exists();z=np.load(E/'actual-interface-input.npz');line=np.load(OLD/'b-native-head-lineage.npz');bpy.ops.wm.open_mainfile(filepath=str(SRC));s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();skin=bpy.data.objects['AFN74_SKIN_AND_EXISTING_OCULAR_LINING'];head=bpy.data.objects['AFN98_ORIGINAL_ARTIST_HEAD_AND_NECK_COLLAR'];A=np.array(head.matrix_world);inv=np.linalg.inv(A[:3,:3]);SV=z['skinV'];ns=len(SV);nhead=len(line['sourceHeadVertexIDs']);HV=z['headV'][:nhead];HT=line['sourceHeadOriginalTriangles'];ST=z['skinT'];kd=KDTree(ns)
 for i,p in enumerate(SV):kd.insert(p,i)
 kd.balance();lower=[]
 for pt in z['headV'][line['neckHeadVertexIDs']]:
  co,i,d=kd.find(Vector(pt));assert d<1e-8;lower.append(i)
 lower,lu,ll=parameter(SV,np.array(lower,'i4'));upper,uu,ul=parameter(HV,z['headUpperLoop']);grid=np.unique(np.r_[lu,uu]);M=len(grid);lo,s0,s1,sw=interpolate(SV,lower,lu,grid);hi,h0,h1,hw=interpolate(HV,upper,uu,grid);sn=normals(SV,ST);hn=normals(HV,HT);ln=unit((1-sw[:,None])*sn[s0]+sw[:,None]*sn[s1]);un=unit((1-hw[:,None])*hn[h0]+hw[:,None]*hn[h1]);lt=unit(SV[np.roll(lower,-1)]-SV[np.roll(lower,1)]);ut=unit(HV[np.roll(upper,-1)]-HV[np.roll(upper,1)]);ltv=unit(interpolate(lt,np.arange(len(lower)),lu,grid)[0]);utv=unit(interpolate(ut,np.arange(len(upper)),uu,grid)[0]);ld=unit(np.cross(ln,ltv));ud=unit(np.cross(un,utv));ld*=np.where(ld[:,2]>=0,1,-1)[:,None];ud*=np.where(ud[:,2]>=0,1,-1)[:,None];length=np.linalg.norm(hi-lo,axis=1)[:,None];ld*=length;ud*=length;times=np.array([.25,.5,.75]);patch=[];frames=[]
 for t in times:
  P=(2*t**3-3*t*t+1)*lo+(t**3-2*t*t+t)*ld+(-2*t**3+3*t*t)*hi+(t**3-t*t)*ud;patch.append(P);frames.append(t)
 patch=np.concatenate(patch);V=np.vstack((SV,HV,patch));base=ns+nhead;rings=[lower]+[np.arange(base+j*M,base+(j+1)*M,dtype='i4') for j in range(3)]+[upper+ns];parameters=[lu]+[grid]*3+[uu];PF=np.concatenate([strip(a,au,b,bu) for a,au,b,bu in zip(rings,parameters,rings[1:],parameters[1:])]);F=np.vstack((ST,HT+ns,PF));mesh=bpy.data.meshes.new('AFN99_REBUILT_CONTINUOUS_HEAD_NECK');mesh.from_pydata(((V-A[:3,3])@inv.T).tolist(),[],F.tolist());mesh.update();ob=bpy.data.objects.new(mesh.name,mesh);s.collection.objects.link(ob);ob.matrix_world=head.matrix_world.copy();canonical=[x for x in bpy.data.objects['AFN60_BODY_ORAL_AND_OCULAR_LINING'].data.materials]
 for material in canonical:mesh.materials.append(material)
 mesh.polygons.foreach_set('material_index',np.r_[z['skinMaterial'],z['headMaterial'][:len(HT)],np.full(len(PF),4,'i4')]);mesh.polygons.foreach_set('use_smooth',np.ones(len(F),bool))
 # Transfer new neck corners in one local source chart per face. Preserve
 # source body/head loops exactly, without blending across unrelated UDIMs.
 cut=skin.modifiers['AFN98_REPLACE_OUTER_HEAD_REGION_ONLY'];cut.show_viewport=False;bpy.context.view_layer.update();sd,sourceV=q.geom(skin);sd.calc_loop_triangles();sourceT=q.arr(sd.loop_triangles,'vertices',len(sd.loop_triangles),3,dtype='i4');sourceLoops=q.arr(sd.loop_triangles,'loops',len(sd.loop_triangles),3,dtype='i4');sourceUV={u.name:q.arr(u.data,'uv',len(sd.loops),2).copy() for u in sd.uv_layers};tree=BVHTree.FromPolygons(sourceV.tolist(),sourceT.tolist(),all_triangles=True);cut.show_viewport=True;bpy.context.view_layer.update();neckUV={name:[] for name in sourceUV}
 for face in PF:
  pts=V[face];co,no,i,d=tree.find_nearest(Vector(pts.mean(0)));tri=sourceV[sourceT[i]];a=tri[1]-tri[0];b=tri[2]-tri[0];aa=np.dot(a,a);ab=np.dot(a,b);bb=np.dot(b,b);den=aa*bb-ab*ab;assert den>1e-24;rel=pts-tri[0];x=(bb*(rel@a)-ab*(rel@b))/den;y=(aa*(rel@b)-ab*(rel@a))/den;weights=np.column_stack((1-x-y,x,y))
  for name,uv in sourceUV.items():neckUV[name].append(weights@uv[sourceLoops[i]])
 for j,name in enumerate(sourceUV):
  old=np.concatenate((z['skinUV'+str(j)][z['skinLoops']],z['headUV'+str(j)][z['headLoops'][:len(HT)]],np.array(neckUV[name]))).reshape(-1,2);mesh.uv_layers.new(name=name).data.foreach_set('uv',old.ravel())
 count=len(V);use=np.r_[np.ones(ns,bool),np.zeros(nhead+len(patch),bool)];si=np.r_[np.arange(ns,dtype='i4'),np.zeros(nhead+len(patch),'i4')];hidx=np.r_[np.zeros(ns,'i4'),np.arange(nhead,dtype='i4'),np.zeros(len(patch),'i4')];flag=np.r_[np.zeros(base,bool),np.ones(len(patch),bool)];tt=np.repeat(times,M);s0=np.tile(s0,3);s1=np.tile(s1,3);h0=np.tile(h0,3);h1=np.tile(h1,3);sw=np.tile(sw,3);hw=np.tile(hw,3);LS0=(SV[s0]-A[:3,3])@inv.T;LS1=(SV[s1]-A[:3,3])@inv.T;LH0=(HV[h0]-A[:3,3])@inv.T;LH1=(HV[h1]-A[:3,3])@inv.T;low=(1-sw[:,None])*LS0+sw[:,None]*LS1;high=(1-hw[:,None])*LH0+hw[:,None]*LH1;tangent=unit((1-tt[:,None])*(LS1-LS0)+tt[:,None]*(LH1-LH0));axial=high-low;axial=unit(axial-np.sum(axial*tangent,axis=1)[:,None]*tangent);normal=unit(np.cross(tangent,axial));delta=(patch-A[:3,3])@inv.T-((1-tt[:,None])*low+tt[:,None]*high);coeff=np.column_stack([np.sum(delta*d,axis=1) for d in [tangent,axial,normal]])
 arrays=[('AFN99_SkinVertex','INT',si),('AFN99_HeadVertex','INT',hidx),('AFN99_UseSkin','BOOLEAN',use),('AFN99_IsPatch','BOOLEAN',flag)]
 for name,data in [('S0',s0),('S1',s1),('H0',h0),('H1',h1),('SW',sw),('HW',hw),('T',tt),('Coefficients',coeff)]:
  full=np.zeros((count,3) if data.ndim==2 else count,'i4' if data.dtype.kind in 'iu' else 'f4');full[base:]=data;arrays.append(('AFN99_Patch'+name,'FLOAT_VECTOR' if data.ndim==2 else 'INT' if data.dtype.kind in 'iu' else 'FLOAT',full))
 for name,kind,data in arrays:mesh.attributes.new(name,kind,'POINT').data.foreach_set('vector' if kind=='FLOAT_VECTOR' else 'value',np.asarray(data).ravel())
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();mesh.update();m.live_positions(ob,skin,head);patch_nodes(ob,skin,head);bpy.data.objects['AFN99_CONTINUOUS_RENDER_SKIN'].hide_render=True;bpy.data.objects['AFN99_CONTINUOUS_RENDER_SKIN'].hide_set(True);bpy.context.view_layer.update();d,actual=q.geom(ob);err=float(np.linalg.norm(actual-V,axis=1).max());assert err<4e-6,err;mesh.calc_loop_triangles();actualT=q.arr(mesh.loop_triangles,'vertices',len(mesh.loop_triangles),3,dtype='i4');edges=np.concatenate([actualT[:,[0,1]],actualT[:,[1,2]],actualT[:,[2,0]]]);un,ix,inc=np.unique(np.sort(edges,axis=1),axis=0,return_inverse=True,return_counts=True);direction=np.bincount(ix,weights=np.where(edges[:,0]<edges[:,1],1,-1));assert np.all(inc==2) and np.all(direction==0);ob['scope']='Continuous head-neck surface rebuilt from actual source/body tangent directions and four anatomical quadrant boundary correspondences. Shares existing boundary vertices; old folded collar excluded.3 inner section rings; live source-edge/local-frame curvature transfer. Not a self-intersection, contact or complete-operation certificate.';ob['sourceCredit']=head.get('sourceCredit','');m.m.rig.shade.settings();m.m.rig.k.b.camera('face');s.camera.data.lens=85;s.render.hair_subdiv=3;bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
 np.savez_compressed(E/'b-anatomical-neck-lineage.npz',restWorld=V,triangles=actualT,oldSkinVertexCount=ns,originalFineHeadVertexCount=nhead,lowerBodyLoop=lower,upperHeadLoop=upper,lowerParameter=lu,upperParameter=uu,commonParameter=grid,newNeckVertexStart=base,patchTriangles=PF,sourceS0=s0,sourceS1=s1,sourceH0=h0,sourceH1=h1,sourceSW=sw,sourceHW=hw,sourceT=tt,frameCoefficients=coeff);save('b-build-summary.json',{'source':str(SRC),'sourceSha256':sha(SRC),'output':str(OUT),'outputSha256':sha(OUT),'outputBytes':OUT.stat().st_size,'renderSkin':ob.name,'actualVertices':len(V),'triangles':len(actualT),'originalFoldedCollarTrianglesRemoved':752,'newNeckVertices':len(patch),'newNeckTriangles':len(PF),'sharedBodyBoundaryVertices':len(lower),'sharedHeadBoundaryVertices':len(upper),'anatomicalQuadrantCorrespondences':['anterior','right','posterior','left'],'lowerLandmarkIndices':ll,'upperLandmarkIndices':ul,'innerSectionTimes':times,'bodyFineHeadAndOriginalEyesPreserved':True,'neutralLiveSourceMaximumWorldErrorM':err,'boundaryEdges':0,'internalOrientationConflictingEdges':0,'proofScope':'Edge incidence and winding only; not self-intersection, finite rendered contacts or continuous time.','newCompleteAppearanceOperationContactRuntimeAccepted':False,'secondsBeforePreview':time.time()-tick});rows=[]
 for view in ['face','profile','oblique','body-face']:rows.append(v.image('b-anatomical-neck',view));save('b-view-controls.json',rows)
 print('R99_ANATOMICAL_NECK_COMPLETE_PREVIEW_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
