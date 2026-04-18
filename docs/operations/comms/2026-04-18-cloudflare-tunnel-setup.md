# Cloudflare Tunnel Setup — Demo Server (2026-04-18)

**Audience:** Windows-side Claude Code on the demo server workstation.
**Prereq:** The standup brief `2026-04-16-demo-server-standup.md` has been followed through step 6 (server running on `0.0.0.0:8000`, local smoke test returns 201).
**Goal:** expose the server at `https://bioliminal-demo.aaroncarney.me` via a persistent Cloudflare named tunnel.
**Decisions already made (do not re-litigate):**
- Named tunnel (not `trycloudflare.com` quick-tunnel — we want a stable URL for the 4/20 demo, not an ephemeral one).
- Hostname: `bioliminal-demo.aaroncarney.me` (Aaron owns this zone on Cloudflare).
- Ingress rule: `localhost:8000` → tunnel.
- No Zero Trust / Access wrapper — demo is unauthenticated by design.
- Provisioning flow: **Dashboard token** (Path 1), not the CLI `cloudflared tunnel login` flow. No `cert.pem` to shuffle between machines; `cloudflared service install <token>` handles everything, and the tunnel persists across reboots as a Windows service.

---

## Step 1 — Install `cloudflared`

Check first:
```
cloudflared --version
```

If missing (from an elevated CMD / PowerShell):
```
winget install --id Cloudflare.cloudflared -e
```

Close and reopen the shell so `cloudflared` is on PATH. Re-run `cloudflared --version` to confirm.

## Step 2 — Create the tunnel in the Cloudflare dashboard (Aaron does this)

Aaron logs in at https://one.dash.cloudflare.com → **Networks → Tunnels** → **Create a tunnel** → connector type **Cloudflared** → name `bioliminal-demo` → **Save tunnel**. The next screen shows an install command containing a long token (`eyJ...`). Aaron copies that token only — not the whole command.

## Step 3 — Install the tunnel connector as a Windows service

Run (elevated CMD / PowerShell) with the token Aaron gives you:
```
cloudflared service install <token>
```

`cloudflared` registers as a Windows service, connects outbound to Cloudflare's edge, and persists across reboots. Confirm with:
```
Get-Service cloudflared
cloudflared tunnel list
```

## Step 4 — Add the public hostname route (Aaron does this)

Back in the Cloudflare dashboard on the tunnel's detail page → **Public Hostname** tab → **Add a public hostname**:
- Subdomain: `bioliminal-demo`
- Domain: `aaroncarney.me`
- Type: `HTTP`
- URL: `localhost:8000`

Save. Cloudflare creates the DNS record and starts routing traffic to the connector automatically. No CLI work, no config.yml, no cert.pem.

## Step 5 — Verify from outside

From any machine that is **not** the demo server (phone hotspot, laptop on another network, etc.):

```
curl -sS https://bioliminal-demo.aaroncarney.me/health
curl -sS -X POST https://bioliminal-demo.aaroncarney.me/sessions \
  -H 'content-type: application/json' \
  --data-binary @sample_bicep_curl_with_emg.json
```

The fixture lives at
`software/mobile-handover/fixtures/sample_bicep_curl_with_emg.json` in the
repo; copy it to the client machine first.

Expected: `/health` returns 200; `POST /sessions` returns 201 with a
`session_id` and `frames_received: 1`. On the server machine, a new session
directory should appear under `$AURALINK_DATA_DIR`.

## Step 6 — Post the outcome on gitlab

On gitlab `ML_RandD_Server#11`, add a comment with:
- Machine hostname (the Windows box).
- Tunnel URL: `https://bioliminal-demo.aaroncarney.me`.
- Time you verified the external round-trip.
- A paste of the successful `curl -sS https://bioliminal-demo.aaroncarney.me/health` response.

That's the signal to Kelsi that she can `--dart-define=SERVER_URL=https://bioliminal-demo.aaroncarney.me` in the mobile build.

---

## Things NOT to do

- Don't wrap this with Cloudflare Zero Trust / Access. Demo is unauthenticated by design.
- Don't edit Cloudflare zone records via the dashboard — use `cloudflared tunnel route dns`. The CLI is the source of truth.
- Don't create more than one tunnel. If `cloudflared tunnel list` shows extras, leave them; don't delete without asking.
- Don't commit `cert.pem` or `<UUID>.json` anywhere. They're account credentials.
- Don't change `localhost:8000` unless the server itself is bound to a different port (and if so, update both this config and `ML_RandD_Server#11`).

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `cloudflared` not found after winget install | Shell hasn't reloaded PATH | Close all shells, open fresh |
| Dashboard "Save tunnel" completed but no hostname added | Step 4 skipped — tunnel exists but is orphan | Go back to the tunnel's detail page → Public Hostname tab → add the route. Non-destructive. |
| Tunnel shows INACTIVE in dashboard | `service install <token>` never ran or failed | `Get-Service cloudflared` on the demo PC; if missing, re-run with a fresh token |
| Tunnel shows HEALTHY but `curl` from outside returns 502 | Server not actually bound to `0.0.0.0:8000` | Re-check standup brief step 5 |
| Tunnel shows HEALTHY but external curl returns 530 | No public-hostname route yet | Add the route per step 4 |
| `POST /sessions` returns 422 through tunnel but 201 locally | Request body being rewritten by something | Rare; check the dashboard's tunnel config for stray TLS or header rules |
| Tunnel drops after a few minutes | Laptop sleep / network change | Keep the server on wired ethernet, disable sleep |

## Exit criteria

- [ ] `cloudflared tunnel list` shows `bioliminal-demo`.
- [ ] `https://bioliminal-demo.aaroncarney.me/health` returns 200 from an external network.
- [ ] `POST` of `sample_bicep_curl_with_emg.json` returns 201 from external.
- [ ] Outcome posted on gitlab `ML_RandD_Server#11`.

When all four are green, standup + tunnel are done. No further work needed until M4 (dress rehearsal).

---

*Questions → Aaron. If the Cloudflare account doesn't have `aaroncarney.me` or Aaron wants a different hostname, stop and ask — don't improvise.*
