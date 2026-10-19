"""Private visual study of an already-local artist reference; no data adoption."""
import bpy,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0034-master-locks';E.mkdir(parents=True,exist_ok=True)
REF=R/'Reference/character/blender-hair-styles/hair_nodes-female_hair_styles.blend'

def main():
    assert hashlib.sha256(REF.read_bytes()).hexdigest()=='1ad6202095c1793678fee7d69a7e9f8b5fdb6e5c293d300eb1062d2d437e8d48'
    bpy.ops.wm.open_mainfile(filepath=str(REF));s=bpy.context.scene
    for o in s.objects:
        o.hide_render=True
        for m in o.modifiers:m.show_viewport=False;m.show_render=False
    def mat(name,color):
        m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.58;return m
    clay=mat('PRIVATE_STUDY_CLAY',(.42,.42,.42));hair=mat('PRIVATE_STUDY_GUIDES',(.10,.045,.02))
    for name in ('head','eyes'):
        o=bpy.data.objects[name];o.location.x+=5;o.hide_render=False;o.data.materials.clear();o.data.materials.append(clay)
    rows={}
    for name in ('long hair main','long hair strands'):
        o=bpy.data.objects[name];o.hide_render=False;d=o.data;d.materials.clear();d.materials.append(hair)
        p=np.empty(len(d.points)*3,dtype='f4');d.position_data.foreach_get('vector',p);p=p.reshape(-1,3)
        lengths=[];sizes=[]
        for curve in d.curves:
            points=p[curve.first_point_index:curve.first_point_index+curve.points_length];lengths.append(float(np.linalg.norm(np.diff(points,axis=0),axis=1).sum()));sizes.append(len(points))
        rows[name]={'guides':len(d.curves),'points':len(d.points),'pointCountRange':[min(sizes),max(sizes)],'lengthRangeReferenceUnits':[min(lengths),max(lengths)],'lengthStdReferenceUnits':float(np.std(lengths)),'modifiersDisabledForSafeRawGuideStudy':True}
        radius=d.attributes.get('radius') or d.attributes.new('radius','FLOAT','POINT');radius.data.foreach_set('value',np.full(len(d.points),.006,dtype='f4'))
    s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.device='CPU';s.render.threads_mode='FIXED';s.render.threads=4;s.render.resolution_x=s.render.resolution_y=800;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.film_transparent=False
    world=bpy.data.worlds.new('PRIVATE_REFERENCE_WORLD');world.use_nodes=True;world.node_tree.nodes.get('Background').inputs[0].default_value=(.035,.035,.035,1);world.node_tree.nodes.get('Background').inputs[1].default_value=.5;s.world=world
    target=Vector((5,-.3,14.85))
    for name,loc,power,size in [('PRIVATE_KEY',(1,-7,19),1200,7),('PRIVATE_FILL',(9,-3,17),700,5)]:
        d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
    d=bpy.data.cameras.new('PRIVATE_STUDY_CAMERA');camera=bpy.data.objects.new(d.name,d);s.collection.objects.link(camera);s.camera=camera;d.lens=65
    private=E/'private-reference';private.mkdir(exist_ok=True)
    for view,loc in [('oblique',(10,-10,16)),('profile',(17,-2,15.8))]:
        camera.location=loc;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(private/f'bystedt-raw-guides-{view}.png');bpy.ops.render.render(write_still=True)
    (E/'artist-reference-study.json').write_text(json.dumps({'author':'Daniel Bystedt','reference':str(REF),'sha256':hashlib.sha256(REF.read_bytes()).hexdigest(),'declaredLicense':'CC-BY-SA exact version unresolved; reference-only','geometryOrNodeCodeAdopted':False,'rawGuideStatistics':rows,'privateImagesNotCharacterResultsOrRedistributedAssets':True,'studyScope':'Raw independently shaped artist guides, with interpolation/deform disabled. Diagnostic thickening/clay used to inspect flow; not the original finished render or collision/realism proof.'},indent=2)+'\n')
    print('R34_PRIVATE_REFERENCE_DONE',flush=True)
if __name__=='__main__':main()
