"""Remove copied obsolete datablocks only in a NEW in-memory candidate.
All original .blend/history files remain untouched and are hash references.
"""
from pathlib import Path
import bpy,json,hashlib,datetime
R=Path('D:/Download/Aevrynd');E=R/'Evidence/character-female-next/r0152-layered-groom'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def compact(a,extra):
 scene=bpy.context.scene;m=json.loads((E/'manifest-before.json').read_text('utf-8'));current=a.FIXED+a.MOVING;before={n:a.rawsig(bpy.data.objects[n]) for n in current};world={n:[a.a.hasharray(x) for x in a.geometry(bpy.data.objects[n])] for n in current};rig=bpy.data.objects['AFN138_ACTUAL_CURRENT_GAZE_RIG'];bones=[(b.name,list(b.head_local),list(b.tail_local)) for b in rig.data.bones];action=rig.animation_data.action.name
 references=[m['workingCompleteWomanReference'],m['previousCompleteWorkingWomanBeforeIndividualHead']]
 for x in references:assert sha(x['source'])==x['sha256']
 keep={bpy.data.objects[n] for n in current}|set(extra)|{rig}
 keep.update(o for o in bpy.data.objects if o.type in ['EMPTY','LIGHT','CAMERA'])
 changed=True
 while changed:
  changed=False
  for o in list(keep):
   refs=[o.parent]+[getattr(md,'object',None) for md in o.modifiers]+[getattr(c,'target',None) for c in o.constraints]
   if o.animation_data:
    refs += [t.id for f in o.animation_data.drivers for v in f.driver.variables for t in v.targets if t.id is not None]
   for r in refs:
    if isinstance(r,bpy.types.Object) and r not in keep:keep.add(r);changed=True
 removed=[{'name':o.name,'type':o.type,'wasHiddenRender':o.hide_render} for o in bpy.data.objects if o not in keep]
 assert all(x['wasHiddenRender'] for x in removed),[x for x in removed if not x['wasHiddenRender']]
 bpy.data.batch_remove(ids=[o for o in bpy.data.objects if o not in keep])
 ref=bpy.data.objects.new('AFN152_EXTERNAL_HISTORY_ROLLBACK_REFERENCE',None);scene.collection.objects.link(ref);ref.hide_render=True;ref.hide_set(True);ref['role']='Historical full sources preserved as external rollback, not displayed geometry or current controls.';ref['sourceRecords']=json.dumps(references,ensure_ascii=False)
 beforePurge={k:len(getattr(bpy.data,k)) for k in ['objects','meshes','hair_curves','materials','images','actions','armatures']}
 for prop in bpy.data.bl_rna.properties:
  if prop.type!='COLLECTION':continue
  coll=getattr(bpy.data,prop.identifier)
  try:
   for item in coll:
    if isinstance(item,bpy.types.ID) and getattr(item,'use_fake_user',False) and prop.identifier!='texts':item.use_fake_user=False
  except TypeError:pass
 for text in bpy.data.texts:text.use_fake_user=True
 bpy.data.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True);bpy.context.view_layer.update()
 assert before=={n:a.rawsig(bpy.data.objects[n]) for n in current} and world=={n:[a.a.hasharray(x) for x in a.geometry(bpy.data.objects[n])] for n in current}
 assert bones==[(b.name,list(b.head_local),list(b.tail_local)) for b in rig.data.bones] and action==rig.animation_data.action.name
 for x in references:assert sha(x['source'])==x['sha256']
 result={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Only copied obsolete datablocks removed from this NEW in-memory candidate. No original/history file deletion, move, compression or rewrite.','externalCompleteRollbackSources':references,'currentActualMeshObjectsRetained':current,'actualCurrentPoseRig':rig.name,'originalActionRetained':action,'currentRawMeshesUVAndNeutralWorldExact':True,'removedCopiedObjects':removed,'dataCountsBeforeOrphanPurge':beforePurge,'dataCountsAfterOrphanPurge':{k:len(getattr(bpy.data,k)) for k in beforePurge},'oldHiddenRollbackNoLongerDuplicatedInNewFile':True,'oldRollbackFullyPreservedExternallyNotCurrentOperationProof':True,'independentReopenGazeGuideSkinAndTextureVerificationStillRequired':True}
 (E/'current-only-source-construction.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return result
