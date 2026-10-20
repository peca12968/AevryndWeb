"""Actual complete-character/operation evidence and explicit dental-only comparison."""
from pathlib import Path
import bpy,numpy as np,json,hashlib,importlib.util,time
from mathutils import Vector
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0075-occlusion-authoring';OLD=E.parent/'r0074-oral-controls'
sp=importlib.util.spec_from_file_location('oral75render',Path(__file__).with_name('build-female-next-r0074-oral-controls.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);m.E=E;m.m.shade.g.E=E
def world(o):
    d=o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;p=np.array([v.co[:] for v in d.vertices]);a=np.array(o.matrix_world);return p@a[:3,:3].T+a[:3,3]
def dental_only(ref,tag):
    bpy.ops.wm.open_mainfile(filepath=ref['output']);s=bpy.context.scene;s.frame_set(1);bpy.context.view_layer.update();keep={'AFN74_UPPER_TEETH_RIGID','AFN74_LOWER_TEETH_RIGID'}
    for o in s.objects:
        if o.type in ('MESH','CURVES') and o.name not in keep:o.hide_render=True
    m.m.shade.settings();c=s.camera;c.location=(.12,-.145,1.409);c.rotation_euler=(Vector((0,-.110,1.405))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=85;s.render.resolution_x=s.render.resolution_y=640;s.cycles.samples=16;s.render.filepath=str(E/(tag+'-neutral-dental-only.png'));bpy.ops.render.render(write_still=True)
def main():
    tick=time.time();ref=json.loads((E/'c-build-summary.json').read_text());assert hashlib.sha256(Path(ref['output']).read_bytes()).hexdigest()==ref['outputSha256'];bpy.ops.wm.open_mainfile(filepath=ref['output']);s=bpy.context.scene;rows=[]
    for f,tag in ((1,'c-neutral'),(13,'c-open')):
        s.frame_set(f);bpy.context.view_layer.update();rows.extend([m.render(tag,'face'),m.render(tag,'body-face')])
    m.save('c-complete-view-controls.json',rows);lower=bpy.data.objects['AFN74_LOWER_TEETH_RIGID'];d=lower.data;edge=np.array([v.vertices[:] for v in d.edges]);count=np.zeros(len(edge),'i4')
    for loop in d.loops:count[loop.edge_index]+=1
    rootids=np.unique(edge[count==1]);assert len(rootids)>0;folder=E/'c-motion-frames';folder.mkdir(exist_ok=True);motion=[]
    for f in (1,4,7,10,13,17,21,25,28,31,34,37):
        s.frame_set(f);bpy.context.view_layer.update();rootgap=np.linalg.norm(world(lower)[rootids]-world(bpy.data.objects['AFN74_LOWER_TEETH_SOFT_SOURCE_REFERENCE'])[rootids],axis=1);row=m.render('c-motion-frames/'+str(f).zfill(4),'face',384,8);row.update(file=str(folder/(str(f).zfill(4)+'-face.png')),correspondingSourceGumRootBoundaryVertices=int(len(rootids)),maximumDentalGumRootCorrespondenceGapM=float(rootgap.max()),rootGapIsCorrespondenceNotSignedClearance=True);motion.append(row);m.save('c-motion-controls.json',motion)
    s.frame_set(13);bpy.context.view_layer.update();angles=[]
    for view in ('profile','alternate-oblique'):
        saved=[(o,o.matrix_world.copy()) for o in s.objects if o.type=='LIGHT'];m.m.shade.settings();m.m.k.b.camera('oblique' if view=='alternate-oblique' else view);s.camera.data.lens=85
        if view=='alternate-oblique':
            for o,_ in saved:o.location.x=-o.location.x;o.rotation_euler=(Vector(m.m.k.b.TARGET)-o.location).to_track_quat('-Z','Y').to_euler()
        s.render.resolution_x=s.render.resolution_y=640;s.cycles.samples=16;s.render.filepath=str(E/('c-operation-'+view+'.png'));bpy.ops.render.render(write_still=True);angles.append({'view':view,'frame':13,'camera':np.array(s.camera.matrix_world).tolist(),'lights':m.q.lights(),'resolution':640,'samples':16})
        for o,matrix in saved:o.matrix_world=matrix
    m.save('c-angle-light-controls.json',angles);dental_only(json.loads((OLD/'c-build-summary.json').read_text()),'r74');dental_only(ref,'r75');print('R75_ACTUAL_COMPLETE_OPERATION_EVIDENCE_DONE',time.time()-tick,flush=True)
if __name__=='__main__':main()
