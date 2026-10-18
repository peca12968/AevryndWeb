"""Reopen exact cached and material-study assets; inherit only identical geometry evidence."""
import bpy,json,importlib.util
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('cache',Path(__file__).with_name('rebuild-female-next-r0013-native-cache.py'));cache=importlib.util.module_from_spec(spec);spec.loader.exec_module(cache)
verify,route=cache.verify,cache.route;E,S=route.E,route.S

def hierarchy():
    return {o.name:{'parent':o.parent.name if o.parent else None,'type':o.parent_type,'bone':o.parent_bone,'basis':[v for row in o.matrix_basis for v in row],'parentInverse':[v for row in o.matrix_parent_inverse for v in row],'modifiers':[(m.name,m.type,m.show_viewport,m.show_render) for m in o.modifiers]} for o in bpy.data.objects if o.type=='CURVES' and o.name.startswith('AFN13_')}

def main():
    base=S/'aevrynd-female-next-r0013-b-native-envelope-hair-study.blend';proof=json.loads((E/'b-resolved-static-verification.json').read_text());assert route.sha(base)==proof['candidateSha256'] and proof['status']=='PASS_TESTED_STATIC_SURFACE_SCOPE'
    bpy.ops.wm.open_mainfile(filepath=str(base));before=verify.original_state();h=hierarchy();fibres=cache.fibres();rows=[]
    for path in (S/'aevrynd-female-next-r0013-b-safe-io-native-envelope-hair-study.blend',S/'aevrynd-female-next-r0013-c-huang-reference.blend'):
        bpy.ops.wm.open_mainfile(filepath=str(path));checks={'sourceState':verify.original_state()==before,'fibresRadiiMaterialNames':cache.fibres()==fibres,'parentingAndModifiers':hierarchy()==h,'noLibraries':len(bpy.data.libraries)==0,'packedFileImages':all(i.packed_file for i in bpy.data.images if i.source=='FILE')};assert all(checks.values()),checks
        original=path
        if 'c-huang' in path.name:
            c=bpy.context.scene.camera;headZ=1.5624730926266572*.91;c.location=(0.,-.90,headZ+.015);c.rotation_euler=(Vector((0.,-.02,headZ))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100
            scene=bpy.context.scene;scene.render.resolution_x=scene.render.resolution_y=1100
            path=S/'aevrynd-female-next-r0013-c-huang-reference-front-view.blend';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(path))
            assert verify.original_state()==before and cache.fibres()==fibres
        rows.append({'source':str(original),'output':str(path),'sha256':route.sha(path),'checks':checks,'inheritedCollisionEvidence':'b-resolved-static-verification.json','scope':'Same exact neutral-world fibres/radii, original skin/rig and parenting. Inherit five static pose surface/body evidence only. No self collision or dynamic proof.'})
    (E/'saved-delivery-verification.json').write_text(json.dumps({'status':'PASS_SAVED_REOPEN_AND_EXACT_SCOPE_INHERITANCE','bodyHairStaticReferenceSha256':proof['candidateSha256'],'fibreSha256':fibres,'assets':rows,'overallCharacterAccepted':False,'runtimePromoted':False},indent=2)+'\n');print('AFN13_DELIVERY_REOPEN_PASS',flush=True)

if __name__=='__main__':main()
