"""Organize editable hair layers and save a verified review copy without geometry edits."""
import bpy,json,importlib.util
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('physical',Path(__file__).with_name('diagnose-female-next-r0014-physical-reference.py'));physical=importlib.util.module_from_spec(spec);spec.loader.exec_module(physical)
verify,flow=physical.verify,physical.flow;E,S=flow.E,flow.S
src=S/'aevrynd-female-next-r0014-c-clump-volume-study.blend';proof=json.loads((E/'c-saved-scalp-flow-verification.json').read_text());assert proof['status']=='PASS_TESTED_STATIC_SURFACE_SCOPE' and len(proof['poses'])==5 and flow.route.sha(src)==proof['candidateSha256']
bpy.ops.wm.open_mainfile(filepath=str(src));before=verify.original();geo=physical.geometry();sigs={o.name:verify.strand_signature(o) for o in bpy.data.objects if o.type=='CURVES' and o.name.startswith('AFN14_')}
def move(o,name,hidden=False):
    col=bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if col.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(col)
    if o.name not in col.objects:col.objects.link(o)
    for old in list(o.users_collection):
        if old!=col:old.objects.unlink(o)
    col.hide_render=hidden;col.hide_viewport=hidden
groups=[]
for o in list(bpy.data.objects):
    if o.name.startswith('AFN14_'):
        hidden=o.type!='CURVES';name='AFN14_'+('SCALP_BINDING' if o.type=='MESH' else 'GUIDE_CONTROLS' if o.type=='CURVE' else o.name.removeprefix('AFN14_'));move(o,name,hidden);groups.append({'object':o.name,'collection':name,'hiddenControlLayer':hidden})
    elif o.name.startswith('AFN13_') and o.type in ('MESH','CURVE'):move(o,'AFN13_ARCHIVED_HELPERS',True)
scene=bpy.context.scene;c=scene.camera;headZ=1.5624730926266572*.91;c.location=(0.,-.90,headZ+.015);c.rotation_euler=(Vector((0.,-.02,headZ))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100;scene.render.resolution_x=scene.render.resolution_y=1100;scene['aevrynd_release_state']='EDITABLE_RESEARCH_REVIEW_NOT_RUNTIME';scene['aevrynd_groom_descriptor']='aevrynd-female-next-r0014-c-groom.authoring.json'
assert before==verify.original() and geo==physical.geometry()
dest=S/'aevrynd-female-next-r0014-c-review.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(dest));bpy.ops.wm.open_mainfile(filepath=str(dest))
checks={'originalHeadState':verify.original()==before,'exactHairWorldPositionsRadii':physical.geometry()==geo,'exactCountsMaterialsParenting':all(verify.strand_signature(bpy.data.objects[name])==sig for name,sig in sigs.items()),'noExternalLibraries':not bpy.data.libraries,'allFileImagesPacked':all(i.packed_file for i in bpy.data.images if i.source=='FILE')};assert all(checks.values()),checks
(E/'review-delivery-verification.json').write_text(json.dumps({'source':str(src),'sourceSha256':flow.route.sha(src),'output':str(dest),'outputSha256':flow.route.sha(dest),'checks':checks,'layers':groups,'inheritedStaticCollisionEvidence':'c-saved-scalp-flow-verification.json','scope':'Geometry/radii/parenting unchanged; five static pose evidence inherited exactly. Controls organized and saved camera reset only. No simulation, self collision, runtime or final visual acceptance.'},indent=2)+'\n');print('AFN14_REVIEW_REOPEN_PASS',flush=True)
