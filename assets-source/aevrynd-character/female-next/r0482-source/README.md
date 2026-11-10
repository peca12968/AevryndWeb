Aevrynd female-next r0482

This archive preserves two rejected neutral complete-groom studies and the r480 B comparison geometry inside one standalone Blender file. Both candidates retain hair self-contact and the rounded canopy, so no character appearance, motion, runtime or user acceptance is recorded.

The final credited Blender source is the authority for exported geometry. It contains 24,831 curves of 80 points per mode, persistent curve and point IDs, a complete neutral skin mesh, reconstructed scalp triangle and barycentric bindings, and a three-component local root offset. The standalone fixture has no rig or facial shape keys. Its images use the original keratin hair shader and shared diagnostic lighting and skin material.

Use bound-A.npz and bound-B.npz for the final data. The global and surface NPZs preserve intermediate failed binding stages for traceability. Their old triangle IDs do not address the exported skin triangle ordering. Motion caps inherited in these data remain unverified for the rebuilt groom.

The local root frame uses U along triangle vertex 0 to vertex 1, N as the geometric outward unit normal, and V as N cross U. Reconstruct the root from its barycentric anchor plus U, V and N multiplied by AEVRYND_ROOT_OFFSET_LOCAL, in metres. AEVRYND_ROOT_NORMAL_OFFSET retains its normal component.

From the repository root, the following Blender command exports the final native geometry and binding streams to a new output directory.

```powershell
& 'D:\SteamLibrary\steamapps\common\Blender\blender.exe' -b --disable-autoexec --python 'evidence/character-female-next/r0482-global-groom-separation/export-r0482.py' -- --source 'assets-source/aevrynd-character/female-next/r0482-source/female-next-r0482-global-groom-UNACCEPTED.blend' --out 'F:\AevryndEvidence\r0482-export-replay'
```

The contact-auditor project in the matching evidence directory has no package dependencies and targets .NET 8. Build it with an installed SDK, then pass each exported base, A or B directory to its HairContact.dll. It checks all spans starting at 0. The archived export receipts reproduce the final hair-contact counts exactly. These are neutral discrete geometry tests.

Original upstream notices are embedded as Blender text blocks and copied in licenses. The body and head retain their source authors and license obligations, including Angelica by DarkNik / original NikZava284 under CC BY 4.0 and the inherited CC0 body chain. The copied historical notices retain separate upstream qualifications. R482 modifications are recorded in the report and embedded provenance text. No exclusive ownership or complete rights qualification is asserted for third-party artwork.

Full round reconstruction scripts retain their original r480 and r481 input paths. The final-source export and capsule replay above are self-contained. The intervening unpublished history after r220 remains a separate pending archive task.
