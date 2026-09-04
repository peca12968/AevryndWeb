# Operations telemetry deployment

The remote publisher is outbound-only. It opens no listener and sends a signed snapshot every 10 seconds.

## Public-key enrollment

Installation creates or reuses an ECDSA P-256 key in the current user's Windows CNG key store. The persisted private key is marked non-exportable and remains protected by the Windows KSP/user ACL. It is never written to the repository, enrollment document, command line, or log. The staging directory is non-inherited and grants access only to the installing user, SYSTEM, and Administrators; reparse points are rejected.

PowerShell 7 is required at the fixed path `C:\Program Files\PowerShell\7\pwsh.exe`. Windows PowerShell 5.1 is intentionally rejected by `#requires` before the script can read credentials, write files, register tasks, or send network traffic.

Install on each remote PC:

```powershell
& 'C:\Program Files\PowerShell\7\pwsh.exe' -NoProfile -File .\Install-OperationsTelemetry.ps1 -NodeId taichung
& 'C:\Program Files\PowerShell\7\pwsh.exe' -NoProfile -File .\Install-OperationsTelemetry.ps1 -NodeId taoyuan
```

The installer prints the path of `<node>-enrollment.json`. That file contains only `nodeId`, algorithm, public `keyId`, public key, and creation time, so it may be returned through a GitHub Issue relay. Before enabling the node, copy those public values to external website configuration (not `appsettings.json`):

```text
Operations__RemoteTelemetry__Nodes__taichung__AuthenticationMode=EcdsaP256
Operations__RemoteTelemetry__Nodes__taichung__Keys__<keyId>__PublicKey=<publicKey>
Operations__RemoteTelemetry__Nodes__taichung__Keys__<keyId>__Revoked=false
```

The website binds the configured public key to the exact allowlisted node and exact key ID. Requests also bind method/path, node, Unix timestamp, random nonce, and raw body. A two-minute freshness window and a persistent nonce ledger reject replay across process restarts.

For rotation, first run the installer with a new non-secret key name and `-EnrollOnly`, for example `-KeyName Aevrynd-OperationsTelemetry-taichung-v2 -EnrollOnly`. Enroll that public key alongside the old one, then rerun without `-EnrollOnly` to switch the publisher and task. After the overlap window, set the old key's external `Revoked` value to `true` and later remove it. A revoked, unknown, or public-key/hash-mismatched key ID fails closed.

Legacy HMAC is available only when a node is explicitly configured with `AuthenticationMode=HmacSha256` and an external 32–64-byte Base64 `Secret`. Modes are exclusive: an ECDSA node never falls back to HMAC. Do not use legacy HMAC for new enrollment.

`-WhatIf` exits before directory, key, file, task, or network mutation. PowerShell 7 is fail-fast via `#requires`.

Use `& 'C:\Program Files\PowerShell\7\pwsh.exe' -NoProfile -File .\Stop-OperationsTelemetry.ps1 -NodeId <node>` to stop it; add `-Remove` to unregister the task and remove the staged publisher.

## Work sources

Current work is read from `C:\ProgramData\Aevrynd\Codex\status.json`. Schema version 1 accepts `working`, `blocked`, `completed`, `failed`, and `cancelled`, plus `task`, `updatedUtc`, `ttl`, and optional `startedUtc`. An expired non-terminal status is recorded as `cancelled`, never guessed as successful or failed.

Explicit completed events may be written atomically to `C:\ProgramData\Aevrynd\Codex\operations-history.json`:

```json
{
  "schemaVersion": 1,
  "events": [
    {
      "name": "Bounded regression audit",
      "type": "qwen",
      "startedAt": "2026-09-04T08:00:00Z",
      "updatedAt": "2026-09-04T08:05:00Z",
      "endedAt": "2026-09-04T08:05:00Z",
      "status": "completed",
      "evidenceSummary": "Release validation completed."
    }
  ]
}
```

The sender and server both enforce size, text, identity, host, state, and timeline bounds. History is deduplicated by `(Name, StartedAt)` and retained server-side. Missing GPU counters are transmitted as `null` and displayed as `unavailable`.
