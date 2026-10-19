"""Read installed native groom interfaces before bounded production trial."""
from pathlib import Path
import bpy,importlib.util,json,hashlib,time
sp=importlib.util.spec_from_file_location('r51base',Path(__file__).with_name('build-female-next-r0051-eye-wall.py'))
k=importlib.util.module_from_spec(sp);sp.loader.exec_module(k)
b=k.b;f=k.f;E=b.R/'Evidence/character-female-next/r0052-native-groom';E.mkdir(parents=True,exist_ok=True)
SRC=b.S/'aevrynd-female-next-r0051-b-integrated-eye-wall.blend'
LIB=Path(r'D:\SteamLibrary\steamapps\common\Blender\5.2\datafiles\assets\nodes\procedural_hair_node_assets.blend')

def save(n,x):(E/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def socket(s):
    row={'name':s.name,'identifier':s.identifier,'type':s.socket_type,'direction':s.in_out}
    if hasattr(s,'default_value'):
        v=s.default_value
        row['default']=v if isinstance(v,(str,int,float,bool)) else (list(v) if hasattr(v,'__iter__') else str(v))
    return row

def main():
    tick=time.time();assert b.sha(SRC)=='b86f7eeedf6fd6a4d9a7f13ff42dc4051907516bc90be8261f02e7678242a3ff'
    bpy.ops.wm.open_mainfile(filepath=str(SRC));before=f.state()
    with bpy.data.libraries.load(str(LIB),link=False) as (source,target):
        names=source.node_groups[:]
        target.node_groups=[n for n in names if n in ('Interpolate Hair Curves','Clump Hair Curves','Deform Curves on Surface','Attach Hair Curves to Surface','Curl Hair Curves','Frizz Hair Curves')]
    groups={}
    for group in target.node_groups:
        groups[group.name]={'sockets':[socket(s) for s in group.interface.items_tree if s.item_type=='SOCKET'],
            'nodes':[{'name':n.name,'type':n.bl_idname,'group':n.node_tree.name if n.type=='GROUP' else None,
                      'operation':getattr(n,'operation',None)} for n in group.nodes],
            'links':[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in group.links]}
    o=bpy.data.objects['AFN33_C_BODY_BOUND_FIBRES'];d=o.data
    settings=bpy.context.scene.tool_settings.curves_sculpt
    rna=settings.bl_rna if settings else bpy.types.ToolSettings.bl_rna.properties['curves_sculpt'].fixed_type
    props={p.identifier:{'type':p.type,'readonly':p.is_readonly} for p in rna.properties}
    row={'source':str(SRC),'sourceSha256':b.sha(SRC),'installedBlender':bpy.app.version_string,
         'library':str(LIB),'librarySha256':b.sha(LIB),'groupNames':names,'groups':groups,
         'sculptOperators':dir(bpy.ops.sculpt_curves),'sculptSettingsProperties':props,
         'sourceHairSurface':d.surface.name if d.surface else None,'sourceHairSurfaceUV':d.surface_uv_map,
         'nativeCurveDataProperties':[p.identifier for p in d.bl_rna.properties],
         'sourceAppearanceStateUnchanged':f.state()==before,'seconds':time.time()-tick}
    save('installed-native-interfaces.json',row)
    print('R52_NATIVE_GROUPS',list(groups),flush=True)
    for name,group in groups.items():print(name,[(s['name'],s['identifier'],s.get('default')) for s in group['sockets']],flush=True)
    print('R52_SCULPT_PROPS',props,'OPERATORS',dir(bpy.ops.sculpt_curves),flush=True)

if __name__=='__main__':main()
