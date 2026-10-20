"""Read publisher demo datablocks without linking/evaluating its whole scene."""
from pathlib import Path
import bpy,json,numpy as np,time,hashlib
R=Path(r'D:\Download\Aevrynd');D=R/'Reference/character/blender-bystedt-hair-cc-by-sa';E=R/'Evidence/character-female-next/r0068-guide-structure';E.mkdir(parents=True,exist_ok=True)
SRC=D/'hair_nodes-female_hair_styles.blend';SHA='1ad6202095c1793678fee7d69a7e9f8b5fdb6e5c293d300eb1062d2d437e8d48'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(E/n).write_text(json.dumps(v,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else x.tolist())+'\n',encoding='utf8')
def values(mod):
    result={}
    try:keys=mod.keys()
    except TypeError:return {'noIDProperties':True}
    for key in keys:
        try:
            value=mod[key]
            if hasattr(value,'name'):value={'data':value.name,'type':type(value).__name__}
            elif not isinstance(value,(int,float,str,bool)):value=list(value)
            json.dumps(value);result[key]=value
        except (TypeError,ValueError):pass
    return result
def main():
    tick=time.time();assert sha(SRC)==SHA
    with bpy.data.libraries.load(str(SRC),link=False) as (src,dst):
        inventory={'objects':list(src.objects),'scenes':list(src.scenes),'texts':list(src.texts),'collections':list(src.collections),'nodeGroups':list(src.node_groups)};dst.objects=src.objects;dst.texts=src.texts
    rows=[]
    for o in dst.objects:
        row={'name':o.name,'type':o.type,'matrix':np.array(o.matrix_world).tolist(),'hideRender':o.hide_render,'modifiers':[{'name':md.name,'type':md.type,'enabled':md.show_viewport,'render':md.show_render,'group':md.node_group.name if md.type=='NODES' and md.node_group else None,'inputs':values(md) if md.type=='NODES' else {}} for md in o.modifiers]}
        if o.type=='CURVES':
            d=o.data;P=np.empty(len(d.position_data)*3,dtype='f4');d.position_data.foreach_get('vector',P);P=P.reshape(-1,3);row.update(curves=len(d.curves),points=len(P),bounds=[P.min(0).tolist(),P.max(0).tolist()] if len(P) else [],surface=d.surface.name if d.surface else None,surfaceUV=d.surface_uv_map,attributes=[{'name':a.name,'type':a.data_type,'domain':a.domain} for a in d.attributes],materials=[m.name if m else None for m in d.materials])
        if o.type=='MESH':row.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),UVs=list(o.data.uv_layers.keys()),materials=[m.name if m else None for m in o.data.materials])
        rows.append(row)
    texts={t.name:t.as_string()[:30000] for t in dst.texts};save('publisher-raw-inventory.json',{'source':str(SRC),'sha256':SHA,'inventory':inventory,'objects':rows,'texts':texts,'linkedIntoScene':False,'dependencyGraphEvaluated':False,'embeddedCodeExecuted':False,'seconds':time.time()-tick});print('R68_RAW_DEMO_INVENTORY',len(rows),'TEXTS',list(texts),'CURVES',[(r['name'],r.get('curves'),r.get('points')) for r in rows if r['type']=='CURVES'],time.time()-tick,flush=True)
if __name__=='__main__':main()
