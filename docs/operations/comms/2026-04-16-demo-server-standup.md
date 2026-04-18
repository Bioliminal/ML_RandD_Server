# Demo Server Standup — Handover Brief (2026-04-16)

**Status:** current
**Created:** 2026-04-16
**Updated:** 2026-04-16
**Owner:** AaronCarney

**Audience:** Windows-side Claude Code instance on the demo server workstation.
**Goal:** stand up the BioLiminal analysis server + Cloudflare tunnel + prove phone-to-server reachability. One-shot setup for the 2026-04-20 bicep curl demo.
**Scope boundary:** server + tunnel + smoke test only. Do not touch ML models, rule YAML, mobile app, or anything labeled `post-demo`.

---

## What this machine is

The demo's analysis server. Receives `POST /sessions` from the phone, runs the pipeline (rule eval + geometry on BlazePose landmarks — CPU-only for bicep curl), returns a session_id, and serves reports at `GET /sessions/{id}/report`. Also hosts the Cloudflare tunnel that gives the phone a stable public URL regardless of demo-venue WiFi.

Not an ML training machine. Not a dev loop. After standup, this machine just runs the server until 4/20 wraps.

## Prereqs to verify before starting

- [ ] Python 3.11 or newer available (`python --version`).
- [ ] `uv` installed and on PATH (`uv --version`). If missing: `curl -LsSf https://astral.sh/uv/install.sh | sh` on WSL, or the official Windows installer.
- [ ] `git` available and authenticated for `gitlab.com/bioliminal/ML_RandD_Server`.
- [ ] `cloudflared` installed and authenticated to Aaron's Cloudflare account. Aaron has operational experience with Cloudflare tunnels — **do not redesign tunnel configuration**. Follow Aaron's existing tunnel or pattern.
- [ ] An open TCP port 8000 (or document the alternative you chose).
- [ ] A persistent directory for session storage, outside the repo (e.g. `C:\bioliminal-data` or `~/bioliminal-data`).

If any of these are missing, stop and ask Aaron before improvising.

## Standup steps

1. **Clone the repo.**
   ```
   git clone https://gitlab.com/bioliminal/ML_RandD_Server.git
   cd ML_RandD_Server
   ```

2. **Install dependencies.**
   ```
   cd software/server
   uv sync
   ```
   Expected: `.venv/` created, dependencies resolved. If `uv sync` fails, capture the full error before retrying.

3. **Set session storage location.**
   ```
   # bash / WSL
   export AURALINK_DATA_DIR=/path/to/persistent/bioliminal-data
   mkdir -p "$AURALINK_DATA_DIR"
   ```
   On Windows PowerShell: `$env:AURALINK_DATA_DIR = "C:\bioliminal-data"` and `mkdir`.

4. **Run the test suite once to confirm the install is sane.**
   ```
   uv run pytest -q
   ```
   Expect: **231 passed**. Anything red means stop and report.

5. **Start the server.**
   ```
   uv run uvicorn auralink.api.main:app --host 0.0.0.0 --port 8000
   ```
   `--host 0.0.0.0` is load-bearing — `127.0.0.1` would prevent the tunnel from reaching the server. No `--reload` in production mode.

   Consider running under a supervisor (nssm on Windows, systemd user unit on WSL) so the server survives reboots through 4/20. Minimum viable is a tmux/screen session + a runbook note.

6. **Smoke test from the same machine.**
   ```
   curl -s http://localhost:8000/health
   curl -s -X POST http://localhost:8000/sessions \
     -H 'content-type: application/json' \
     -d @software/mobile-handover/fixtures/sample_bicep_curl_with_emg.json
   ```
   Expected: `/health` returns `{"status":"ok"}` (or equivalent); `POST /sessions` returns a `201` with a `session_id` and `frames_received: 1`.

7. **Wire the Cloudflare tunnel to `localhost:8000`.** Aaron has existing Cloudflare-tunnel tooling — use it. Do not create a new Cloudflare account or re-auth unless Aaron says so.

8. **Smoke test through the tunnel.** From any machine with a public network:
   ```
   curl -s https://<tunnel-hostname>/health
   curl -s -X POST https://<tunnel-hostname>/sessions \
     -H 'content-type: application/json' \
     -d @sample_bicep_curl_with_emg.json
   ```
   (Copy the fixture to the client machine first if needed; it lives at `software/mobile-handover/fixtures/sample_bicep_curl_with_emg.json` in the repo.)

9. **Write the tunnel URL into gitlab issue `ML_RandD_Server#11`** as a comment. That's how the phone teammate finds it. Do not hardcode the URL anywhere in the repo.

## Acceptance — you're done when all of these are green

- [ ] `uv run pytest -q` → 231 passed.
- [ ] `GET http://localhost:8000/health` → 200.
- [ ] `POST http://localhost:8000/sessions` with the fixture → 201 + a session_id; `$AURALINK_DATA_DIR` gets a new entry.
- [ ] `GET https://<tunnel-hostname>/health` → 200 from a machine outside the host network.
- [ ] `POST https://<tunnel-hostname>/sessions` with the fixture → 201 from outside.
- [ ] Tunnel URL posted on gitlab `ML_RandD_Server#11`.

## Things NOT to do (explicit non-goals)

- Don't wire authentication. Demo is unauthenticated by design.
- Don't wire TLS termination on the server. The Cloudflare tunnel handles TLS.
- Don't tweak CORS, add middlewares, or modify `auralink/api/main.py` beyond what's already there.
- Don't change the pipeline, stage list, or schemas. ML_RandD_Server#12 owns the bicep curl rule YAML; don't pre-empt it.
- Don't upgrade Python, `uv`, or any dep unless `uv sync` demands it.
- Don't delete anything in `AURALINK_DATA_DIR` — it's the durable session history for the demo period.
- Don't run `git push` from this machine. It's a server, not a dev box.

## Troubleshooting cheatsheet

| Symptom | Likely cause | Fix |
|---|---|---|
| `uv sync` fails on a package | Python too old | Verify `python --version` ≥ 3.11. |
| `Address already in use` | Port 8000 taken | Pick another port; update tunnel + gitlab #11 comment to match. |
| Tunnel hits server, phone 422s on POST | Schema drift | Verify server is at `main` head — run `git log -1` and compare to gitlab `main`. |
| Server 500 on POST | Unexpected runtime error | Capture server log, paste into gitlab issue as comment, do not hot-patch. |
| Firewall blocking port 8000 | Windows Firewall rule missing | Only needed for LAN-fallback testing. Not required for tunnel path. |

## Exit criteria

When the acceptance checklist is green, post a short status note on gitlab `ML_RandD_Server#11`: which machine, tunnel URL, time, and a confirmation that the fixture round-trips from outside the network. Then stop. No further work needed until Aaron signals.

---

*If anything in this brief is ambiguous, ask Aaron. Don't improvise — the demo is Mon 4/20 and the cost of silent drift is higher than the cost of one question.*
