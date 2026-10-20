"""Isolate one publisher hairstyle before evaluating anything dense."""
from pathlib import Path
import bpy,json,numpy as np,time,importlib.util
sp=importlib.util.spec_from_file_location('guide68inspect',Path(__file__).with_name('inspect-female-next-r0068-guide-structure.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
def val(x):
    if hasattr(x,'name'):return {'data':x.name,'type':type(x).__name__}
    if isinstance(x,(int,float,str,bool)) or x is None:return x
    try:return list(x)
    except TypeError:return str(x)
def main():
    tick=time.time();assert m.sha(m.SRC)==m.SHA
    with bpy.data.libraries.load(str(m.SRC),link=False) as (src,dst):dst.objects=['head','eyes','long hair main','long hair strands','long hair growth mesh'];dst.texts=['Hair demo file info']
    rows=[];groups={}
    for o in dst.objects:
        row={'name':o.name,'parent':o.parent.name if o.parent else None,'location':list(o.location),'scale':list(o.scale),'matrixBasis':np.array(o.matrix_basis).tolist(),'instanceCollection':o.instance_collection.name if o.instance_collection else None}
        if o.type in ('MESH','CURVES'):
            d=o.data;P=np.array([v.co[:] for v in d.vertices],dtype='f4') if o.type=='MESH' else np.array([p.vector[:] for p in d.position_data],dtype='f4');row['localBounds']=[P.min(0).tolist(),P.max(0).tolist()]
        for md in o.modifiers:
            if md.type!='NODES' or not md.node_group:continue
            group=md.node_group;rows1=[]
            for n in group.nodes:
                nr={'name':n.name,'type':n.bl_idname,'mute':n.mute,'inputs':[(i.name,val(i.default_value),i.is_linked) for i in n.inputs if hasattr(i,'default_value')]}
                if n.bl_idname=='ShaderNodeGroup' or n.bl_idname=='GeometryNodeGroup':nr['group']=n.node_tree.name if n.node_tree else None
                rows1.append(nr)
            groups[group.name]={'interface':[{'name':i.name,'identifier':i.identifier,'direction':i.in_out,'default':val(i.default_value) if hasattr(i,'default_value') else None} for i in group.interface.items_tree if i.item_type=='SOCKET'],'nodes':rows1,'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in group.links]}
        rows.append(row)
    m.save('one-style-preflight.json',{'source':str(m.SRC),'sha256':m.SHA,'objects':rows,'groups':groups,'sourceLicenseNotice':dst.texts[0].as_string(),'evaluated':False,'seconds':time.time()-tick});print('R68_ONE_STYLE_PREFLIGHT',[(x['name'],x.get('localBounds')) for x in rows],list(groups),flush=True)
if __name__=='__main__':main()
