"""Bounded diagnosis of actual eye shading/UV/geometry on the complete woman."""
from pathlib import Path
import bpy,numpy as np,json,importlib.util,time
from mathutils import Vector
R=Path(r'D:\Download\Aevrynd');E=R/'Evidence/character-female-next/r0065-eye-shading';E.mkdir(parents=True,exist_ok=True);S=R/'engine/assets/characters/female-next/source';SRC=S/'aevrynd-female-next-r0060-b-limit-surface-assembly-study.blend'
def module(n,p):
    s=importlib.util.spec_from_file_location(n,Path(__file__).with_name(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
g=module('eye65base','build-female-next-r0061-surface-flow-groom.py');shade=module('eye65render','shade-female-next-r0061-physical-hair.py');k=g.k
def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def tree(t,depth=0):
    nodes=[]
    for n in t.nodes:
        inputs=[]
        for i in n.inputs:
            if not hasattr(i,'default_value'):continue
            v=i.default_value
            if not isinstance(v,(int,float,str,bool)):
                try:v=list(v)
                except TypeError:v=str(v)
            inputs.append({'socket':i.name,'value':v,'linked':i.is_linked})
        x={'name':n.name,'type':n.bl_idname,'inputs':inputs}
        if n.bl_idname=='ShaderNodeTexImage':x.update(image=n.image.name if n.image else None,colorSpace=n.image.colorspace_settings.name if n.image else None)
        if n.bl_idname=='ShaderNodeGroup' and n.node_tree and depth<2:x['group']=tree(n.node_tree,depth+1)
        nodes.append(x)
    return {'nodes':nodes,'links':[[l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name] for l in t.links]}
def close_render(tag):
    s=bpy.context.scene;shade.settings();k.b.camera('face');s.camera.location=(0.,-.50,1.468);target=Vector((0.,-.12,1.466));s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.lens=120;s.render.filepath=str(E/(tag+'-eyes-close.png'));bpy.ops.render.render(write_still=True)
    return {'file':s.render.filepath,'camera':np.array(s.camera.matrix_world).tolist(),'lens':120,'settings':shade.settings()}
def main():
    tick=time.time();assert g.sha(SRC)==g.SOURCE_SHA;bpy.ops.wm.open_mainfile(filepath=str(SRC));bpy.context.scene.frame_set(1);names=list(json.loads((E.parent/'r0060-ocular-assembly/b-build-summary.json').read_text())['visibleComponents'].values());rows=[];materials={}
    for name in names:
        o=bpy.data.objects[name]
        for md in o.modifiers:
            if md.type=='SUBSURF':md.levels=md.render_levels
        bpy.context.view_layer.update();row=k.mesh(o);mi,counts=np.unique(row['mi'],return_counts=True);slots={str(int(i)):{'name':o.data.materials[int(i)].name,'triangles':int(c)} for i,c in zip(mi,counts)};rows.append({'object':name,'worldBounds':[row['V'].min(0).tolist(),row['V'].max(0).tolist()],'usedMaterials':slots,'nativeUVLayers':list(o.data.uv_layers.keys())})
        for i in mi:
            mat=o.data.materials[int(i)]
            if mat.name not in materials and int(i) in (0,1,2,3):materials[mat.name]=tree(mat.node_tree)
    save('baseline-eye-shader-diagnosis.json',{'source':str(SRC),'sha256':g.sha(SRC),'components':rows,'opticalMaterials':materials,'seconds':time.time()-tick,'geometryOrMaterialsModified':False});print('R65_DIAGNOSIS_READY',[(r['object'],r['usedMaterials']) for r in rows[:4]],flush=True);save('baseline-close-control.json',close_render('baseline'))
if __name__=='__main__':main()
