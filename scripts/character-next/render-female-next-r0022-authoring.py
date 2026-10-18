"""Actual complete-head guide authoring review, explicitly not final hair."""
import bpy,json,importlib.util,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('groom',Path(__file__).with_name('build-female-next-r0022-patch-groom.py'));g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
E=g.R/'Evidence/character-female-next/r0022-patch-groom';C=E/'c-local-ear-hulls'
def digest(o):
    h=hashlib.sha256()
    for s in o.data.splines:
        p=np.empty((len(s.points),4),np.float32);s.points.foreach_get('co',p.ravel());h.update(p.tobytes())
    return h.hexdigest()
def main():
    source=g.S/'aevrynd-female-next-r0022-c-guides.blend';proof=json.loads((C/'guide-verification.json').read_text());assert g.sha(source)==proof['guideBlenderSha256'];bpy.ops.wm.open_mainfile(filepath=str(source));g.solid.stage.set_pose(bpy.data.objects['AFN_R0005_Rig'],'neutral');before=g.head_state();o=bpy.data.objects['AFN22_GUIDES'];shape=digest(o);bad={r['curve'] for r in proof['bodyCapsules']['failureSamples']};controls=json.loads((C/'guide-controls.json').read_text())['guides'];colors={'CROWN':(.70,.45,.12,1.),'FRONTAL_SWEEP':(.12,.36,.70,1.),'OCCIPITAL':(.17,.50,.35,1.),'TEMPORAL':(.44,.22,.56,1.),'FAILED':(.9,.025,.015,1.)};indices={}
    for name,color in colors.items():
        mat=bpy.data.materials.new('AFN22_DIAGNOSTIC_'+name);mat.diffuse_color=color;mat.use_nodes=True;bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=color;bsdf.inputs['Roughness'].default_value=.65;indices[name]=len(o.data.materials);o.data.materials.append(mat)
    for i,spline in enumerate(o.data.splines):spline.material_index=indices['FAILED' if i in bad else controls[i]['family']]
    for part in bpy.data.objects:
        if part.type=='CURVES' and part.name.startswith('AFN14_'):part.hide_render=True;part.hide_viewport=True
    o.hide_render=False;o.hide_viewport=False;o.data.bevel_depth=.00012;o['aevrynd_layer']='DIAGNOSTIC_GUIDE_DISPLAY_NOT_RENDER_HAIR';o['displayBevelM']=.00012;o['contactEvidenceRadiusM']=.00006;o['failedGuideIds']=sorted(bad);assert digest(o)==shape
    s=bpy.context.scene;s['aevrynd_release_state']='FAILED_GUIDE_AUTHORING_REVIEW_NOT_FINAL_HAIR';s['aevrynd_review_legend']='424 source guides only; red=body-contact guide; display radius120um, body-check radius60um. Final child hair not generated.';bpy.context.preferences.filepaths.save_version=0;dest=g.S/'aevrynd-female-next-r0022-c-authoring-review.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));bpy.ops.wm.open_mainfile(filepath=str(dest));assert digest(bpy.data.objects['AFN22_GUIDES'])==shape
    s=bpy.context.scene;head=1.5624730926266572*.91;target=(0.,-.02,head);rows=[]
    for mode in ('saved','alternate'):
        if mode=='alternate':
            for light in (o for o in bpy.data.objects if o.type=='LIGHT'):light.location.x=-light.location.x;light.rotation_euler=(Vector(target)-light.location).to_track_quat('-Z','Y').to_euler()
        for view,location in (('face',(0.,-.90,head+.015)),('oblique',(.46,-.82,head+.04)),('profile',(.86,-.16,head+.02))):
            if mode=='alternate' and view!='oblique':continue
            camera=s.camera;camera.location=location;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=100;s.render.resolution_x=s.render.resolution_y=800;s.render.resolution_percentage=100;s.render.threads_mode='FIXED';s.render.threads=4;path=E/f'c-guide-review-{mode}-{view}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True);rows.append({'view':view,'light':mode,'path':str(path)})
    (E/'authoring-review-verification.json').write_text(json.dumps({'source':str(source),'sourceSha256':g.sha(source),'output':str(dest),'outputSha256':g.sha(dest),'guideCoordinateArraysExact':True,'guideCoordinateDigest':shape,'failedGuideIds':sorted(bad),'bodyFailureSegments':proof['bodyCapsules']['unqualifiedSegments'],'displayRadiusM':.00012,'contactCheckRadiusM':.00006,'renders':rows,'scope':'Actual source head and 424 guide paths, with diagnostic material/display-width changes. Not child hair, not a realism or collision acceptance, no new geometry candidate.'},indent=2)+'\n');print('R0022_AUTHORING_REVIEW_READY',flush=True)
if __name__=='__main__':main()
