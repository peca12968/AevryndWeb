"""One-factor attribution after pigment-coordinate hypothesis falsified."""
import bpy,importlib.util,time,json
from pathlib import Path
sp=importlib.util.spec_from_file_location('skin42i',Path(__file__).with_name('inspect-female-next-r0042-skin-artifacts.py'));i=importlib.util.module_from_spec(sp);sp.loader.exec_module(i)
f=i.f;b=i.b;E=i.E;v=i.v
def props(data):
    return {p.identifier:getattr(data,p.identifier) for p in data.bl_rna.properties if not p.is_readonly and p.type in ('BOOLEAN','FLOAT','INT','ENUM') and not getattr(p,'is_array',False) and ('shadow' in p.identifier or 'sample' in p.identifier)}
def main():
    start=time.time();bpy.ops.wm.open_mainfile(filepath=str(i.SRC));s=bpy.context.scene;body=bpy.data.objects[b.BODY];mat=body.data.materials[0];hair=bpy.data.objects[f.OLD];before=f.state();f.E=E
    hair.hide_render=True;f.render('hair-hidden-diagnostic',('face','oblique'));hair.hide_render=False
    noBump=mat.copy();noBump.name='AFN42_DIAG_NO_MICROBUMP'
    for node in noBump.node_tree.nodes:
        if node.type=='BUMP':node.inputs['Strength'].default_value=0
    body.data.materials[0]=noBump;f.render('no-microbump-diagnostic',('face',))
    noSSS=mat.copy();noSSS.name='AFN42_DIAG_NO_SSS';noSSS.node_tree.nodes.get('Principled BSDF').inputs['Subsurface Weight'].default_value=0;body.data.materials[0]=noSSS;f.render('no-sss-diagnostic',('face',));body.data.materials[0]=mat
    assert f.state()==before;i.save('shadow-normal-diagnostic.json',{'source':str(i.SRC),'sourceSha256':b.sha(i.SRC),'originalStateRestoredExact':True,'lights':{o.name:props(o.data) for o in s.objects if o.type=='LIGHT'},'eevee':props(s.eevee),'seconds':time.time()-start,'scope':'Each render changes only explicitly named hair visibility, microbump strength or SSS weight; not adopted candidate.'})
    print('R42_SHADOW_NORMAL_DONE',time.time()-start,flush=True)
if __name__=='__main__':main()
