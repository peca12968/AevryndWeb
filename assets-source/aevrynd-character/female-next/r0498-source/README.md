# Aevrynd female-next r0498

This Blender 5.2.3 source carries the actual rigged woman with r497 B hair, the original r448 blink controls and two native cheek shape keys. B is enabled on opening. A adds malar support. B adds an oblique cheek ridge with shallow relief underneath the lateral orbit. The face domain uses the inherited skin materials, with protected eyelid motion, other material domains and scalp bindings. The basis, triangle topology and hair positions keep their original hashes.

The fixed neutral frontal, oblique and profile views show A as the rounder cheek and B as the more gradual orbital-to-cheek transition. B changes 1,320 stored skin vertices by up to 2.282 mm. A changes 1,087 by up to 3.178 mm. B is retained as an offline research candidate. The improvement is subtle and closed-eye folds still appear stylized. There is no overall score increase.

The independent reopen verified the native control on the evaluated mesh. Setting B temporarily from 1 to 0.55 moved 1,313 evaluated vertices. Returning to 1 restored the exact coordinate hash. At blink settings 0, 0.5 and 1 on frame 1, the measured guarded skin vertices and the separately evaluated eye, sclera-reflect, tear-meniscus and eyelash meshes retain their baseline coordinates. No external libraries or unpacked file images were found.

Both changed cheek patches have zero newly overlapping polygon pairs against the rest of the skin and against the four ocular layers at the three sampled blink positions. Shared-vertex self pairs are excluded. B's smallest sampled moved-vertex distance to those ocular meshes is about 3.396 mm, unsigned. The altered triangles retain their orientation in all three poses. The results cover the changed face patch at discrete positions. Continuous blink clearance, full facial expressions, whole-body contacts and engine validation remain open.

The first portrait render was interrupted after five verified frames by the system commit reserve. The resume verified the original source and the completed image hashes, released the hidden hair data in memory and rendered the remaining frames. No renderer wrote the saved source.

The original aligned Angelica face was inspected as visual correspondence for the inherited topology. DarkNik and NikZava284 are credited under CC BY 4.0. The derived scene imports none of the reference geometry and carries the exact inherited notices. The camera fixtures and render settings are recorded in the preview script and receipt.
