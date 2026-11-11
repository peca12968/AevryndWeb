"""Replace isolated rear lock lanes with continuously shared spatial guides."""
from pathlib import Path
import runpy

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / 'r0491-graduated-locks'
SOURCE = PARENT / 'female-next-r0491-graduated-locks-UNACCEPTED.blend'
DEST = ROOT / 'female-next-r0492-posterior-loft-UNACCEPTED.blend'
previous = runpy.run_path(str(PARENT / 'author-r0491.py'))
spatial = previous['previous']
foundation = previous['foundation']
digest = previous['digest']
read_json = previous['read_json']
write_json = previous['write_json']
array_hash = previous['array_hash']
read_attribute = previous['read_attribute']
positions = previous['positions']
set_positions = previous['set_positions']
smooth = previous['smooth']
BODY = previous['BODY']
CONTROL = 'R491 complete hair | diagonal'
POINTS = 80
RESOLUTION = 161
OUTER = 15


def duplicate_guide(scene, parent, label):
    guide = parent.copy()
    guide.data = parent.data.copy()
    guide.name = f'R492 native posterior rails | {label}'
    guide.data.name = f'R492 posterior rail controls | {label}'
    scene.collection.objects.link(guide)
    guide['aevrynd_posterior_layout'] = label
    guide.hide_render = True
    guide.hide_set(True)
    return guide


def build_field(stations, angles):
    rows, lengths = [], []
    for route in stations:
        points, arc, _, _ = spatial['dense_route'](route)
        rows.append(spatial['sample'](arc, points, np.linspace(0, arc[-1], RESOLUTION)))
        lengths.append(arc[-1])
    positions = np.asarray(rows)
    slopes = np.gradient(positions, angles, axis=0)
    return positions, slopes, np.array(lengths)


def field_sample(field, slopes, angles, theta, along):
    """Interpolate across shared rails and along the edited 3D splines."""
    theta = np.clip(theta, angles[0], angles[-1])
    left = np.clip(np.searchsorted(angles, theta, side='right')-1, 0, len(angles)-2)
    span = angles[left+1]-angles[left]
    t = (theta-angles[left])/span
    u = np.clip(along, 0, 1)*(RESOLUTION-1)
    lower = np.minimum(u.astype('i4'), RESOLUTION-2)
    fraction = (u-lower)[...,None]
    a = field[left,lower]*(1-fraction)+field[left,lower+1]*fraction
    b = field[left+1,lower]*(1-fraction)+field[left+1,lower+1]*fraction
    sa = slopes[left,lower]*(1-fraction)+slopes[left,lower+1]*fraction
    sb = slopes[left+1,lower]*(1-fraction)+slopes[left+1,lower+1]*fraction
    t = t[...,None]
    t2, t3 = t*t, t*t*t
    return (2*t3-3*t2+1)*a + (t3-2*t2+t)*span[...,None]*sa + (-2*t3+3*t2)*b + (t3-t2)*span[...,None]*sb


def generate(base, normals, ids, radii, owner, tree, guide):
    stations, angles, _, _ = spatial['read_guide'](guide)
    assert len(stations) == OUTER + 9
    roots = base[:,0].astype('f8')
    theta = np.arctan2(roots[:,0], roots[:,1]+.033)
    weight = 1 - smooth((abs(theta)-.94)/.38)
    weight[abs(theta) >= 1.32] = 0
    noise = ((ids.astype('u8')*np.uint64(2654435761))&np.uint64(0xffffffff)).astype('f8')/4294967296
    diagonal = guide['aevrynd_posterior_layout'] == 'crossfall'
    tier = owner >= OUTER
    candidate = base.copy()
    joins = np.zeros(len(base), dtype='i4')
    phase = np.arange(POINTS)[None,:]
    for is_inner in (False,True):
        layer = slice(OUTER,None) if is_inner else slice(0,OUTER)
        layer_angles = angles[3:12] if is_inner else angles
        field, slopes, arc = build_field(stations[layer], layer_angles)
        members = np.flatnonzero((tier == is_inner)&(weight > 0))
        for start_index in range(0,len(members),640):
            rows = members[start_index:start_index+640]
            angle = theta[rows]
            random = noise[rows]
            attached = roots[rows]
            length = np.interp(angle, layer_angles, arc)
            guide_indices = owner[rows] - (OUTER if is_inner else 0)
            entry = np.empty(len(rows))
            for index in np.unique(guide_indices):
                selected = guide_indices == index
                entry[selected] = np.interp(attached[selected,2]-.023,field[index,::-1,2],np.linspace(1,0,RESOLUTION))
            entry = np.maximum(entry,(.006+.014*random)/length)
            finish = 1-(.003+.014*random+.004*(1+np.cos(8*angle)))/length
            entry = np.minimum(entry,finish-.028/length)
            first = field_sample(field,slopes,layer_angles,angle,entry)
            upper = np.linalg.norm(first-attached,axis=1)
            join = np.clip(np.rint(79*upper/(upper+(finish-entry)*length)),11,44).astype('i4')
            relative = np.clip((phase-join[:,None])/(79-join[:,None]),0,1)
            along = entry[:,None] + relative*(finish-entry)[:,None]
            turn = angle[:,None] + np.zeros_like(along)
            if diagonal:
                # Sweep through neighbouring sectors. Opposite tier directions keep the overlap staggered.
                drift = -.062*np.sin(np.pi*along)+.076*smooth((along-.40)/.60)
                turn += drift*(-.52 if is_inner else 1.0)*np.cos(.84*angle[:,None])
            points = field_sample(field,slopes,layer_angles,turn,along)
            outward = foundation['normalized'](np.stack((points[:,:,0],points[:,:,1]+.033,np.zeros_like(along)),axis=2))
            periodic = .5+.5*np.cos(19*turn+(3.2*along if diagonal else .4))
            ridge = (.0005+(.0039 if diagonal else .0021)*periodic)*np.sin(np.pi*along)**2
            ridge += (.0025*(random-.42))[:,None]
            points += outward * (ridge*(.63 if is_inner else 1))[:,:,None]
            crest = .0018+.0042*smooth((attached[:,2]-1.455)/.111)
            new = spatial['surface_splice'](attached,normals[rows],points,join,crest)
            candidate[rows] = (base[rows]+weight[rows,None,None]*(new-base[rows])).astype('f4')
            joins[rows] = join
    clamp = np.where(weight > 0,joins+4,0)
    local = foundation['constrain_upper_shape'](candidate,clamp,radii,tree)
    assert np.isfinite(candidate).all() and np.array_equal(candidate[:,0],base[:,0])
    assert np.array_equal(candidate[weight == 0],base[weight == 0])
    return candidate, weight.astype('f4'), joins, local


def main():
    parent = read_json(PARENT/'construction-receipt.json')
    assert not DEST.exists() and digest(SOURCE) == parent['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False,use_scripts=False)
    scene = bpy.context.scene
    control = bpy.data.objects[CONTROL]
    guide = bpy.data.objects[parent['variants']['diagonal']['guideObject']]
    base = positions(control)
    assert array_hash(base) == parent['variants']['diagonal']['positionHash']
    omitted = []
    for obj in list(scene.objects):
        if (obj.type == 'CURVES' and obj != control) or (obj.name.startswith('R491 native layer guides') and obj != guide):
            omitted.append(obj.name)
            data = obj.data
            bpy.data.objects.remove(obj,do_unlink=True)
            if not data.users:
                bank = bpy.data.hair_curves if isinstance(data,bpy.types.Curves) else bpy.data.curves
                bank.remove(data)
    ids = read_attribute(control.data,'AFN409_CURVE_ID')
    radii = read_attribute(control.data,'radius').reshape(len(base),POINTS)
    owner = read_attribute(control.data,'AEVRYND_SPATIAL_LOCK_ID')
    normals, tree, error = foundation['binding_frame'](control,bpy.data.objects[BODY],base[:,0])
    variants = {}
    for label in ('shared','crossfall'):
        rails = duplicate_guide(scene,guide,label)
        bank, weights, joins, local = generate(base,normals,ids,radii,owner,tree,rails)
        obj = control.copy()
        obj.data = control.data.copy()
        obj.name = f'R492 complete hair | {label}'
        obj.data.name = f'R492 posterior shared strands | {label}'
        scene.collection.objects.link(obj)
        set_positions(obj,bank)
        for key, kind, values in (('AEVRYND_POSTERIOR_LOFT_WEIGHT','FLOAT',weights),('AEVRYND_POSTERIOR_JOIN_POINT','INT',joins)):
            obj.data.attributes.new(key,kind,'CURVE').data.foreach_set('value',values)
        obj['Aevrynd_Guide_Object'] = rails.name
        variants[label] = dict(object=obj.name,guideObject=rails.name,positionHash=array_hash(bank),
            weightHash=array_hash(weights),joinHash=array_hash(joins),
            changedStrands=int(np.any(bank != base,axis=(1,2)).sum()),
            unchangedFrontalAndOutsideStrands=int((weights == 0).sum()),**local)
    active = bpy.data.objects[variants['crossfall']['object']]
    for obj in scene.objects:
        if obj.type == 'CURVES':
            obj.hide_render = obj != active
            obj.hide_set(obj != active)
    bpy.ops.object.select_all(action='DESELECT')
    active.select_set(True)
    bpy.context.view_layer.objects.active = active
    bpy.data.texts.new('Aevrynd_R492_Posterior_Rails').write(
        'Two complete unaccepted grooms using shared posterior rails, native Blender spline inputs and the original roots.\n')
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 4
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST),compress=True,copy=True)
    assert digest(SOURCE) == parent['source']['sha256']
    write_json(ROOT/'construction-receipt.json',dict(source=dict(path=str(DEST),sha256=digest(DEST),bytes=DEST.stat().st_size),
        parent=parent['source'],controlObject=control.name,controlPositionHash=array_hash(base),rootHash=array_hash(base[:,0]),
        bindingMaximumErrorMetres=error,strands=len(base),pointsPerStrand=POINTS,defaultVisible='crossfall',variants=variants,historicalBanksInParent=omitted))
    print('R492_SOURCE',str(DEST),flush=True)


if __name__ == '__main__':
    main()
