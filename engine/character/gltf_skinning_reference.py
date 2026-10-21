"""Offline glTF2 bone/animation reference for Aevrynd asset qualification.
Uncompressed accessors, linear/step TRS animations and linear blend skinning.
Not a renderer, collision solver or production engine performance benchmark.
"""
import json,struct
from pathlib import Path
import numpy as np
def quaternion(q):
 q=np.asarray(q,dtype='f8');q=q/np.linalg.norm(q);x,y,z,w=q
 return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def slerp(a,b,u):
 a=a/np.linalg.norm(a);b=b/np.linalg.norm(b);dot=float(a@b)
 if dot<0:b=-b;dot=-dot
 if dot>.9995:q=(1-u)*a+u*b;return q/np.linalg.norm(q)
 angle=np.arccos(np.clip(dot,-1,1));return (np.sin((1-u)*angle)*a+np.sin(u*angle)*b)/np.sin(angle)
class GLB:
 def __init__(self,path):
  raw=Path(path).read_bytes();magic,version,size=struct.unpack_from('<4sII',raw);assert magic==b'glTF' and version==2 and size==len(raw);pos=12;self.binary=None
  while pos<len(raw):
   count,kind=struct.unpack_from('<II',raw,pos);chunk=raw[pos+8:pos+8+count];pos+=8+count
   if kind==0x4e4f534a:self.g=json.loads(chunk)
   elif kind==0x004e4942:self.binary=chunk
  assert self.binary is not None;self.cache={};self.parents={c:i for i,n in enumerate(self.g['nodes']) for c in n.get('children',[])}
 def accessor(self,index):
  if index in self.cache:return self.cache[index]
  a=self.g['accessors'][index];assert not a.get('sparse'),'Sparse accessor not supported by this qualification reference';bv=self.g['bufferViews'][a['bufferView']];assert bv.get('buffer',0)==0
  dtype=np.dtype({5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]);width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];stride=bv.get('byteStride',width*dtype.itemsize);offset=bv.get('byteOffset',0)+a.get('byteOffset',0);arr=np.ndarray((a['count'],width),dtype=dtype,buffer=self.binary,offset=offset,strides=(stride,dtype.itemsize)).astype('f8')
  if a.get('normalized'):
   info=np.iinfo(dtype);arr=np.maximum(-1,arr/info.max) if dtype.kind=='i' else arr/info.max
  self.cache[index]=arr;return arr
 def sample(self,sampler,t,path):
  times=self.accessor(sampler['input']).ravel();values=self.accessor(sampler['output']);mode=sampler.get('interpolation','LINEAR');assert mode in ['LINEAR','STEP']
  if t<=times[0]:return values[0]
  if t>=times[-1]:return values[-1]
  j=int(np.searchsorted(times,t));i=j-1
  if mode=='STEP':return values[i]
  u=(t-times[i])/(times[j]-times[i]);return slerp(values[i],values[j],u) if path=='rotation' else values[i]*(1-u)+values[j]*u
 def world_matrices(self,t,animation=0):
  overrides={};anims=self.g.get('animations',[])
  if anims:
   anim=anims[animation]
   for c in anim['channels']:
    target=c['target'];path=target['path'];assert path in ['translation','rotation','scale'];overrides.setdefault(target['node'],{})[path]=self.sample(anim['samplers'][c['sampler']],t,path)
  local=[]
  for i,n in enumerate(self.g['nodes']):
   o=overrides.get(i,{})
   if 'matrix' in n:assert not o;M=np.array(n['matrix']).reshape(4,4).T
   else:
    T=o.get('translation',n.get('translation',[0,0,0]));Q=o.get('rotation',n.get('rotation',[0,0,0,1]));S=o.get('scale',n.get('scale',[1,1,1]));M=np.eye(4);M[:3,:3]=quaternion(Q)@np.diag(S);M[:3,3]=T
   local.append(M)
  out={}
  def walk(i):
   if i not in out:out[i]=walk(self.parents[i])@local[i] if i in self.parents else local[i]
   return out[i]
  return [walk(i) for i in range(len(local))]
 def primitive_world(self,node_index,primitive,world):
  node=self.g['nodes'][node_index];att=primitive['attributes'];P=self.accessor(att['POSITION']);P4=np.c_[P,np.ones(len(P))]
  if 'skin' not in node:return (P4@world[node_index].T)[:,:3]
  skin=self.g['skins'][node['skin']];inverse=self.accessor(skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1);out=np.zeros((len(P),3));weightSum=np.zeros(len(P));slot=0
  while 'JOINTS_'+str(slot) in att:
   J=self.accessor(att['JOINTS_'+str(slot)]).astype('i4');W=self.accessor(att['WEIGHTS_'+str(slot)])
   for k in range(J.shape[1]):
    weightSum+=W[:,k]
    for j in np.unique(J[:,k]):
     ids=np.flatnonzero((J[:,k]==j)&(W[:,k]>0))
     if not len(ids):continue
     M=world[skin['joints'][int(j)]]@inverse[int(j)];out[ids]+=(P4[ids]@M.T)[:,:3]*W[ids,k,None]
   slot+=1
  assert np.max(abs(weightSum-1))<2e-6,'Unnormalized actual skin weights';return out
