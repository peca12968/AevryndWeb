"""Actual geometry occlusion masks, separate from beauty materials/exposure."""
import bpy,json,importlib.util
from pathlib import Path
from mathutils import Vector
spec=importlib.util.spec_from_file_location('build',Path(__file__).with_name('build-female-next-r0019-native-blink.py'));build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
def main():
    E,S=build.E,build.S;rows=[]
    for variant,w in (('a',0.),('a',1.),('c',1.)):
        src=S/('aevrynd-female-next-r0019-a-native-blink-study.blend' if variant=='a' else 'aevrynd-female-next-r0019-c-angular-blink-study.blend');bpy.ops.wm.open_mainfile(filepath=str(src));build.set_blink(w,w);s=bpy.context.scene;s.render.threads_mode='FIXED';s.render.threads=4
        def material(name,color):
            m=bpy.data.materials.new(name);m.use_nodes=True;nodes=m.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');e=nodes.new('ShaderNodeEmission');e.inputs['Color'].default_value=(*color,1.);e.inputs['Strength'].default_value=1.;m.node_tree.links.new(e.outputs[0],out.inputs['Surface']);return m
        dark=material('AFN19_DIAGNOSTIC_OCCLUDER',(0.,0.,0.));white=material('AFN19_DIAGNOSTIC_EYE_ID',(1.,1.,1.))
        for o in bpy.data.objects:
            if o.type in ('MESH','CURVES','CURVE'):
                o.data.materials.clear();o.data.materials.append(white if o.name.startswith('AFN6_') else dark)
                if o.type=='MESH':
                    for p in o.data.polygons:p.material_index=0
        s.world.use_nodes=True
        for n in s.world.node_tree.nodes:
            if n.bl_idname=='ShaderNodeBackground':n.inputs['Color'].default_value=(0.,0.,0.,1.);n.inputs['Strength'].default_value=0.
        s.view_settings.view_transform='Raw';s.view_settings.look='None';s.view_settings.exposure=0.;s.view_settings.gamma=1.;fits=build.solid.stage.eyes.helper_centres();z=fits['L']['centre'][2];c=s.camera;c.location=(0.,-.43,z+.005);c.rotation_euler=(Vector((0.,-.115,z))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=100;s.render.resolution_x=1400;s.render.resolution_y=650;s.render.resolution_percentage=100;s.render.film_transparent=False;dest=E/f'{variant}-eye-visibility-{w:.2f}.png';s.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
        rows.append({'asset':str(src),'assetSha256':build.sha(src),'weight':w,'path':str(dest),'scope':'Opaque white union of existing eye component surfaces, all existing other geometry black; raw color, no source saved. Visibility in this fixed camera/AA render only, not a continuous geometric closure proof.'})
    build.save('eye-visibility-renders.json',{'renders':rows})
    print('R0019_EYE_VISIBILITY_MASKS_DONE',flush=True)
if __name__=='__main__':main()
