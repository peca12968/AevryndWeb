# Female character r0506

r0506 is a rejected motion experiment on the r0505 B hairstyle. r0505 B remains the hairstyle research source and r0500 B is the whole working woman.

Open the Blender file on frame 1 and play frames 1–37. Select R506 native guide-motion hair and open the R506 baked guide dynamics modifier. Motion model 0 gives rigid head follow, 1 gives spring guides, and 2 gives guide-length projection and collision projection. All modes use the same 24,831 native Blender curves, material, follicle IDs, radii, head rig and body. The first nine controls on every strand are fixed in head space. The offsets play directly from the embedded meshes and drivers. The NPZ is the independent construction record.

The spring model moves the visible silhouette very little. The projected model produces a large local error at guide 8311, control 72. Its largest measured frame step is 67.94 mm. Reproducing the bank with only collision projection bypassed reduces the same frame step to 1.91 mm and the maximum guide-tip displacement from 66.73 mm to 6.73 mm. The six matched views also show the existing broad crown and rear surfaces and the thin temple curtains.

The native skin audit tests selected evaluated spline samples and chords at the peak, stop and early rebound frames. Consult skin-contact.json for actual counts, finite-radius witness checks, and scope. Continuous-time, strand-to-strand and garment clearance and engine playback require separate evidence.

Inherited source attribution and rights are in licenses. Geometry Nodes modifier input access follows the Blender 5.2 RNA API documented at https://developer.blender.org/docs/release_notes/5.2/python_api/.
