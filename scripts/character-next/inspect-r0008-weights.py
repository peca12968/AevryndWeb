import bpy,json
bpy.ops.wm.open_mainfile(filepath=r'D:\Download\Aevrynd\engine\assets\characters\female-next\source\aevrynd-female-next-r0008-a-tight-study.blend')
b=bpy.data.objects['AFN_R0008_Body'];g=b.vertex_groups;print('GROUPS='+json.dumps([(x.index,x.name) for x in g]));v=min(b.data.vertices,key=lambda v:(v.co.x-.028)**2+(v.co.z-1.46)**2+(v.co.y+.13)**2);print('SAMPLE='+json.dumps({'index':v.index,'position':list(v.co),'groups':[(g[x.group].name,x.weight) for x in v.groups]}))
