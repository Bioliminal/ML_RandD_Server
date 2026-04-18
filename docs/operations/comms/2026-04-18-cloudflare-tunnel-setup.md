# Cloudflare Tunnel Setup — Demo Server (2026-04-18)

**Audience:** Windows-side Claude Code on the demo server workstation.
**Prereq:** The standup brief `2026-04-16-demo-server-standup.md` has been followed through step 6 (server running on `0.0.0.0:8000`, local smoke test returns 201).
**Goal:** expose the server at `https://bioliminal-demo.aaroncarney.me` via a persistent Cloudflare named tunnel.
**Decisions already made (do not re-litigate):**
- Named tunnel (not `trycloudflare.com` quick-tunnel — we want a stable URL for the 4/20 demo, not an ephemeral one).
- Hostname: `bioliminal-demo.aaroncarney.me` (Aaron owns this zone on Cloudflare).
- Ingress rule: `localhost:8000` → tunnel.
- No Zero Trust / Access wrapper — demo is unauthenticated by design.
- Run mode: foreground in a persistent shell for the demo window (simpler than Windows-service install; Aaron will restart manually if it drops).

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

## Step 2 — Authenticate to Aaron's Cloudflare account

```
cloudflared tunnel login
```

This opens a browser — **Aaron must log in personally** (this is his Cloudflare account, not a service account). Pick the `aaroncarney.me` zone when prompted. On success, a cert file is written to `%USERPROFILE%\.cloudflared\cert.pem`. That file is the only thing that proves you can create tunnels under his account; treat it accordingly.

If you see "No zones found" after login, Aaron needs to verify `aaroncarney.me` is actually in his Cloudflare account. Stop and check.

## Step 3 — Create the named tunnel

```
cloudflared tunnel create bioliminal-demo
```

Output includes a tunnel UUID and creates `%USERPROFILE%\.cloudflared\<UUID>.json` (the credentials file). Copy the UUID — you'll need it for the config. If a tunnel named `bioliminal-demo` already exists (e.g. re-running this script), use the existing one:

```
cloudflared tunnel list
```

## Step 4 — Route DNS at the hostname

```
cloudflared tunnel route dns bioliminal-demo bioliminal-demo.aaroncarney.me
```

This creates a CNAME record in the `aaroncarney.me` zone pointing at the tunnel. If it reports "already exists," that's fine — the record was set up in a prior run.

## Step 5 — Write the config file

Create `%USERPROFILE%\.cloudflared\config.yml` (use a real text editor, not Notepad's Unicode default; UTF-8 no BOM):

```yaml
tunnel: bioliminal-demo
credentials-file: C:\Users\<your-username>\.cloudflared\<UUID>.json

ingress:
  - hostname: bioliminal-demo.aaroncarney.me
    service: http://localhost:8000
  - service: http_status:404
```

Substitute `<your-username>` and `<UUID>` with the real values. The trailing `http_status:404` rule is mandatory — cloudflared rejects configs without a catch-all.

## Step 6 — Run the tunnel (foreground, demo-window persistent)

In a fresh CMD / PowerShell window (leave it open):
```
cloudflared tunnel run bioliminal-demo
```

Expected: log lines saying the tunnel registered with 4 Cloudflare edge nodes and is active. Leave this window open for the demo. If the machine reboots, this window closes and the tunnel goes down — Aaron will need to re-run the command.

(If you want a Windows service install instead — for reboots — `cloudflared service install` works, but only after `config.yml` is in place. Skip unless Aaron asks.)

## Step 7 — Verify from outside

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

## Step 8 — Post the outcome on gitlab

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
| "No zones found" after `tunnel login` | Cloudflare account doesn't own `aaroncarney.me` | Stop and confirm with Aaron |
| Tunnel runs but `curl` from outside returns 502 | Server not actually bound to `0.0.0.0:8000` | Re-check standup brief step 5 |
| `POST /sessions` returns 422 through tunnel but 201 locally | Request body being rewritten by something | Rare; check `config.yml` for stray TLS or header rules |
| Tunnel drops after a few minutes | Laptop sleep / network change | Keep the server on wired ethernet, disable sleep |

## Exit criteria

- [ ] `cloudflared tunnel list` shows `bioliminal-demo`.
- [ ] `https://bioliminal-demo.aaroncarney.me/health` returns 200 from an external network.
- [ ] `POST` of `sample_bicep_curl_with_emg.json` returns 201 from external.
- [ ] Outcome posted on gitlab `ML_RandD_Server#11`.

When all four are green, standup + tunnel are done. No further work needed until M4 (dress rehearsal).

---

*Questions → Aaron. If the Cloudflare account doesn't have `aaroncarney.me` or Aaron wants a different hostname, stop and ask — don't improvise.*
