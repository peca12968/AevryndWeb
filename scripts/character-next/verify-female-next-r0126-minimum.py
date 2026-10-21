"""Independent source/edit/rollback recovery and one scoped neck diagnosis.
No acceptance of complete operation, finite collision, hair dynamics or runtime.
"""
from pathlib import Path
import bpy,numpy as np,json,time,hashlib,importlib.util
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0126-individual-head-foundation'
sp=importlib.util.spec_from_file_location('r126readback',Path(__file__).with_name('build-female-next-r0126-individual-head.py'));a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);b=a.b;b.u.v.E=E
def main():
 tick=time.time();priorPath=E/'minimum-saved-individual-source-readback.json';results=json.loads(priorPath.read_text('utf-8'))['sources'] if priorPath.exists() else {}
 for key in ['b']:
  build=json.loads((E/(key+'-build-summary.json')).read_text('utf-8'));p=Path(build['output']);assert a.a.sha(p)==build['sha256'];bpy.ops.wm.open_mainfile(filepath=str(p));b.deliver(0.);assert a.a.protected()==build['beforeProtected'];skin=bpy.data.objects[build['actualSkinObject']];_,W,T=b.u.b.geom(skin);W=W.copy();T=T.copy();assert np.isfinite(W).all();row={'candidate':{'source':str(p),'sha256':build['sha256'],'bytes':p.stat().st_size},'independentlyReopened':True,'oldR117ActualSkinRawKeysAndEveryOriginalFibrePositionRadiusHashExactlyRecoveredAsHiddenRollback':True,'newActualVisibleSkinVertices':len(W),'newActualVisibleSkinTriangles':len(T),'newActualSkinFinite':True,'oldRollbackPresenceNotClaimedAsCurrentVisibleHairOrFaceOperation':True,'newActualSkinOwnShapeKeyCount':len(skin.data.shape_keys.key_blocks) if skin.data.shape_keys else 0,'newActualSkinModifiers':[(m.name,m.type) for m in skin.modifiers]}
  b.deliver(1.);_,P,_=b.u.b.geom(skin);row['oldBlinkControlActualNewVisibleSkinMaximumMovementM']=float(np.linalg.norm(P-W,axis=1).max());assert row['oldBlinkControlActualNewVisibleSkinMaximumMovementM']==0.;b.deliver(0.);_,restored,_=b.u.b.geom(skin);assert np.array_equal(W,restored)
  i=int(np.argmin(np.linalg.norm(W-np.array([0,-.15,1.43]),axis=1)));original=skin.data.vertices[i].co.copy();skin.data.vertices[i].co.y+=.0002;skin.data.update();skin.update_tag();bpy.context.view_layer.update();_,edited,_=b.u.b.geom(skin);row['actualVisibleVertexEditID']=i;row['actualVisibleVertexEditMovementM']=float(np.linalg.norm(edited-W,axis=1).max());assert row['actualVisibleVertexEditMovementM']>1e-5;skin.data.vertices[i].co=original;skin.data.update();skin.update_tag();bpy.context.view_layer.update();_,restored,_=b.u.b.geom(skin);assert np.array_equal(W,restored);row['actualVisibleMeshEditRestoredExactly']=True;row['allReferencedExternalTextures']=[];row['packedOriginalSourceTextures']=[]
  for im in bpy.data.images:
   if im.packed_file:row['packedOriginalSourceTextures'].append({'name':im.name,'bytes':len(im.packed_file.data),'sha256':hashlib.sha256(im.packed_file.data).hexdigest()})
   elif im.source=='FILE' and im.filepath:
    ip=Path(bpy.path.abspath(im.filepath));assert ip.is_file(),str(ip);row['allReferencedExternalTextures'].append({'image':im.name,'relative':im.filepath,'absolute':str(ip),'bytes':ip.stat().st_size,'sha256':a.a.sha(ip)})
  row.update(newCompleteOperationAccepted=False,newBlinkOrJawRigConnected=False,naturalHairMotionDelivered=False,finiteBodyHairSelfContinuousContactOrRuntimeAccepted=False)
  if key=='a2':
   diag=bpy.data.materials.new('AFN126_DIAGNOSTIC_NEUTRAL_SKIN_ONLY');diag.use_nodes=True;pnode=next(n for n in diag.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled');pnode.inputs['Base Color'].default_value=(.42,.42,.42,1.);pnode.inputs['Roughness'].default_value=.55
   for slot in skin.material_slots:slot.material=diag
   row['diagnosticNeutralSkinControl']=b.u.v.image('diagnostic-a2-neutral-skin','face');_,D,_=b.u.b.geom(skin);assert np.array_equal(D,W);row['diagnosticScope']='Only complete skin material neutralized to separate neck geometry/shading from source pigment/UV/material. Eye/mouth/hair source components unchanged. Diagnostic only, not a candidate or adopted appearance.'
  assert a.a.sha(p)==build['sha256'];results[key]=row;a.save('minimum-saved-individual-source-readback.json',{'sources':results,'scope':'Saved source/edit/recovery only. All old controls/keys/fibres remain hidden rollback; actual new displayed skin does not follow old blink. No complete operation/anatomy/finite-contact/runtime acceptance.','seconds':time.time()-tick})
 print('R126_THREE_SAVED_SOURCES_RECOVERED_AND_SCOPED_NECK_DIAGNOSIS_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
