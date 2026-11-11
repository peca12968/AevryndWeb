"""Compare original controls and Blender's evaluated curve samples on neutral skin."""
from pathlib import Path
import runpy
from time import perf_counter

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
author = runpy.run_path(str(ROOT / 'author-r0492.py'))
prior = runpy.run_path(str(ROOT.parent / 'r0490-spatial-lock-routes/neutral-contact-r0490.py'))
probe = prior['probe']
INDEX = 'aevrynd_audit_curve_index'
RADIUS = 'aevrynd_audit_radius'


def make_sample_modifier(groom):
    group = bpy.data.node_groups.new('R492 temporary evaluated sample audit', 'GeometryNodeTree')
    group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nodes = group.nodes
    links = group.links
    source = nodes.new('GeometryNodeObjectInfo')
    source.transform_space = 'ORIGINAL'
    source.inputs['Object'].default_value = groom
    output = nodes.new('NodeGroupOutput')
    index = nodes.new('GeometryNodeInputIndex')
    store_index = nodes.new('GeometryNodeStoreNamedAttribute')
    store_index.data_type = 'INT'
    store_index.domain = 'CURVE'
    store_index.inputs['Name'].default_value = INDEX
    links.new(source.outputs['Geometry'], store_index.inputs['Geometry'])
    links.new(index.outputs['Index'], store_index.inputs['Value'])
    lower = nodes.new('ShaderNodeMath')
    upper = nodes.new('ShaderNodeMath')
    together = nodes.new('ShaderNodeMath')
    lower.operation, upper.operation, together.operation = 'GREATER_THAN', 'LESS_THAN', 'MULTIPLY'
    links.new(index.outputs['Index'], lower.inputs[0])
    links.new(index.outputs['Index'], upper.inputs[0])
    links.new(lower.outputs[0], together.inputs[0])
    links.new(upper.outputs[0], together.inputs[1])
    select = nodes.new('GeometryNodeSeparateGeometry')
    select.domain = 'CURVE'
    links.new(store_index.outputs['Geometry'], select.inputs['Geometry'])
    links.new(together.outputs[0], select.inputs['Selection'])
    sample = nodes.new('GeometryNodeCurveToPoints')
    sample.mode = 'EVALUATED'
    links.new(select.outputs['Selection'], sample.inputs['Curve'])
    radius = nodes.new('GeometryNodeInputRadius')
    store_radius = nodes.new('GeometryNodeStoreNamedAttribute')
    store_radius.data_type = 'FLOAT'
    store_radius.domain = 'POINT'
    store_radius.inputs['Name'].default_value = RADIUS
    links.new(sample.outputs['Points'], store_radius.inputs['Geometry'])
    links.new(radius.outputs['Radius'], store_radius.inputs['Value'])
    to_mesh = nodes.new('GeometryNodePointsToVertices')
    links.new(store_radius.outputs['Geometry'], to_mesh.inputs['Points'])
    links.new(to_mesh.outputs['Mesh'], output.inputs['Geometry'])
    # Read the converted geometry from a temporary mesh host. The source groom stays intact.
    mesh = bpy.data.meshes.new('R492 temporary evaluated sample mesh')
    host = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.scene.collection.objects.link(host)
    modifier = host.modifiers.new('Temporary neutral point sampling', 'NODES')
    modifier.node_group = group
    return host, group, lower, upper


def evaluate_chunk(obj, group, lower, upper, first, end):
    lower.inputs[1].default_value = first-.5
    upper.inputs[1].default_value = end-.5
    group.update_tag()
    obj.update_tag()
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
    assert mesh is not None and len(mesh.vertices) > 0
    try:
        points = np.empty((len(mesh.vertices),3), dtype='f4')
        mesh.vertices.foreach_get('co', points.ravel())
        indices = author['read_attribute'](mesh, INDEX)
        radii = author['read_attribute'](mesh, RADIUS)
    finally:
        evaluated.to_mesh_clear()
    return points, indices, radii


def verify_endpoints(points, indices, radii, controls, control_radii, first, end):
    curve_indices, starts, lengths = np.unique(indices, return_index=True, return_counts=True)
    assert np.array_equal(curve_indices, np.arange(first,end))
    assert np.all(lengths >= controls.shape[1])
    assert np.array_equal(indices, np.repeat(curve_indices,lengths))
    ends = starts+lengths-1
    np.testing.assert_allclose(points[starts], controls[first:end,0], rtol=0, atol=2e-7)
    np.testing.assert_allclose(points[ends], controls[first:end,-1], rtol=0, atol=2e-7)
    np.testing.assert_allclose(radii[starts], control_radii[first:end,0], rtol=0, atol=2e-7)
    np.testing.assert_allclose(radii[ends], control_radii[first:end,-1], rtol=0, atol=2e-7)
    return int(lengths.min()), int(lengths.max())


def recheck_samples(points, indices, radii, ids, tree, state):
    for coords, index, radius in zip(points, indices, radii):
        center = Vector(coords)
        distance = probe['signed_gap'](center, tree)
        gap = float(distance-radius)
        crossings = None
        if gap < 0:
            state['negativeOrientedWarnings'] += 1
            crossings = probe['ray_counts'](center, tree)
            parity = [number % 2 for number in crossings]
            if all(parity):
                state['rayInsideCenters'] += 1
            elif not any(parity):
                gap = float(abs(distance)-radius)
                state['rayOutsideOverlap' if gap < 0 else 'rayOutsideAndClear'] += 1
            else:
                state['mixedParity'] += 1
        minimum = state['minimumAfterWarningRecheck']
        if minimum is None or gap < minimum['gapMetres']:
            state['minimumAfterWarningRecheck'] = dict(curveID=int(ids[index]), positionMetres=coords.tolist(),
                gapMetres=gap, warningRayCrossings=crossings)
    state['evaluatedSamples'] += len(points)


def main():
    proof = author['read_json'](ROOT / 'construction-receipt.json')
    source = Path(proof['source']['path'])
    assert author['digest'](source) == proof['source']['sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    body = bpy.data.objects[author['BODY']]
    control = bpy.data.objects[proof['controlObject']]
    _, tree, _ = author['foundation']['binding_frame'](control, body, author['positions'](control)[:,0])
    summary = dict(source=proof['source'], pose='complete neutral woman', skin=body.name, controlPointResults={},
        limitations=['Finite sample spacing between evaluated points', 'No hair self-contact, clothes or continuous motion'])
    recorded = ROOT/'neutral-contact.json'
    checkpoint = None
    if recorded.exists():
        saved = author['read_json'](recorded)
        assert saved['source']['sha256'] == proof['source']['sha256']
        summary['controlPointResults'] = saved['controlPointResults']
        checkpoint = saved.get('nativeEvaluatedSampleResult')
    for label, info in proof['variants'].items():
        obj = bpy.data.objects[info['object']]
        for other in bpy.context.scene.objects:
            if other.type == 'CURVES':
                other.hide_set(other != obj)
        bpy.context.view_layer.update()
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        controls = author['positions'](evaluated)
        assert author['array_hash'](controls) == info['positionHash']
        radii = author['read_attribute'](evaluated.data,'radius').reshape(controls.shape[:2])
        ids = author['read_attribute'](evaluated.data,'AFN409_CURVE_ID')
        if label not in summary['controlPointResults']:
            summary['controlPointResults'][label] = prior['audit'](controls,radii,ids,tree)
            author['write_json'](recorded,summary)
            print('R492_CONTROLS', label, summary['controlPointResults'][label], flush=True)

    assert label == 'crossfall'
    host, group, lower, upper = make_sample_modifier(obj)
    state = dict(variant=label, method='Blender Curve to Points in EVALUATED mode, preserving sampled radius and curve ownership',
        evaluatedSamples=0, verifiedCurves=0, samplesPerCurveMinimum=None, samplesPerCurveMaximum=0,
        negativeOrientedWarnings=0, rayInsideCenters=0, rayOutsideOverlap=0, rayOutsideAndClear=0,
        mixedParity=0, minimumAfterWarningRecheck=None)
    if checkpoint:
        assert checkpoint['variant'] == label and checkpoint['method'] == state['method']
        assert 0 < checkpoint['verifiedCurves'] < len(controls) and checkpoint['verifiedCurves'] % 520 == 0
        assert checkpoint['evaluatedSamples'] == checkpoint['verifiedCurves']*checkpoint['samplesPerCurveMinimum']
        assert checkpoint['samplesPerCurveMinimum'] == checkpoint['samplesPerCurveMaximum']
        state.update(checkpoint)
    first_remaining = state['verifiedCurves']
    summary['resumedFromVerifiedCurves'] = first_remaining
    started = perf_counter()
    for first in range(first_remaining,len(controls),520):
        end = min(first+520,len(controls))
        points, indices, sampled_radii = evaluate_chunk(host,group,lower,upper,first,end)
        low, high = verify_endpoints(points,indices,sampled_radii,controls,radii,first,end)
        recheck_samples(points,indices,sampled_radii,ids,tree,state)
        state['verifiedCurves'] = end
        state['samplesPerCurveMinimum'] = low if state['samplesPerCurveMinimum'] is None else min(low,state['samplesPerCurveMinimum'])
        state['samplesPerCurveMaximum'] = max(high,state['samplesPerCurveMaximum'])
        summary['nativeEvaluatedSampleResult'] = state
        author['write_json'](recorded,summary)
        if first == first_remaining or end == len(controls) or (first//520)%8 == 7:
            print('R492_NATIVE_PROGRESS', end, state['evaluatedSamples'], flush=True)
    state['finalProcessElapsedSeconds'] = perf_counter()-started
    assert author['digest'](source) == proof['source']['sha256']
    summary['nativeEvaluatedSampleResult'] = state
    author['write_json'](ROOT/'neutral-contact.json',summary)
    print('R492_NATIVE_CONTACT',state,flush=True)


if __name__ == '__main__':
    main()
