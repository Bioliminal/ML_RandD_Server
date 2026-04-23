#!/usr/bin/env python3
"""Demo server smoke test (ML#25).

Repeatable, deterministic round-trip check against the deployed bioliminal
analysis server. Hits /health, /openapi.json, POST /sessions, GET
/sessions/{id}/report. Optionally re-posts the same fixture and verifies
report determinism.

Stdlib only — runs with any Python 3.10+, no venv required.

Usage:
    python3 tools/smoke_demo_server.py
    python3 tools/smoke_demo_server.py --base-url http://localhost:8000
    python3 tools/smoke_demo_server.py --quick   # skip determinism re-post
    python3 tools/smoke_demo_server.py -v        # echo response bodies

Exit codes:
    0  all checks pass
    1  one or more checks fail
    2  preflight failure (fixture missing, args invalid, etc.)

Logs:
    Every request + response (bodies, headers, status, latency) is written
    to tools/smoke-logs/<UTC-ISO>-<host>/. The console prints a one-line
    pass/fail per step and a final summary table. The full openapi.json is
    persisted so post-mortem schema drift is greppable without re-hitting
    the server.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "https://bioliminal-demo.aaroncarney.me"
# The mobile-handover fixtures (`sample_bicep_curl_with_emg.json`, 1 frame;
# `sample_valid_session.json`, 5 frames) are schema worked-examples and get
# rejected by the server's quality_gate (1s minimum). Default to the
# synthetic fixture that's 60 frames (~1.95s) and known to traverse the full
# pipeline. Override with --fixture when smoking the bicep pipeline once
# ML#18+ML#12 land.
DEFAULT_FIXTURE = (
    REPO_ROOT
    / "software"
    / "server"
    / "tests"
    / "fixtures"
    / "synthetic"
    / "overhead_squat_clean.json"
)
# Used by the reasoner-fires step — known to deterministically trigger the
# SBL knee_valgus rule. Skipped when --no-valgus or when the fixture is gone.
DEFAULT_VALGUS_FIXTURE = (
    REPO_ROOT
    / "software"
    / "server"
    / "tests"
    / "fixtures"
    / "synthetic"
    / "overhead_squat_valgus.json"
)
# Used by the pose-only step — the showcase no-hardware narrative beat. Lives
# in the sibling `bioliminal-ops` repo so both teams pull from one source. The
# resolver tolerates either a flat sibling-clone layout or the olorin symlink
# layout; override with --pose-only-fixture for anything else.
DEFAULT_POSE_ONLY_FIXTURE = (
    REPO_ROOT.parent
    / "bioliminal-ops"
    / "operations"
    / "handover"
    / "mobile"
    / "fixtures"
    / "sample_pose_only_bicep.json"
)
DEFAULT_LOG_DIR = REPO_ROOT / "tools" / "smoke-logs"

# Endpoints + schemas the deployed server MUST expose. Anything missing here
# means the deployed build is older than the rename / ML#1 evidence work.
EXPECTED_PATHS: list[tuple[str, str]] = [
    ("/health", "get"),
    ("/sessions", "post"),
    ("/sessions/{session_id}", "get"),
    ("/sessions/{session_id}/report", "get"),
]
# FastAPI splits `Session` into `Session-Input`/`Session-Output` when the
# validator and serializer schemas diverge, so accept either variant. Schemas
# only referenced internally (e.g. reasoning.config_schemas.EvidenceBlock,
# loaded from YAML at startup) never land in openapi.json, so they can't be
# used as a deploy-currency proof. `ConsentMetadata` is the newest request-
# path addition and is a decent "recent build" marker.
EXPECTED_SCHEMA_GROUPS: list[list[str]] = [
    ["Session", "Session-Input"],
    ["SessionCreateResponse"],
    ["Report"],
    ["ConsentMetadata"],
]


@dataclasses.dataclass
class StepResult:
    name: str
    ok: bool
    latency_ms: int
    detail: str


class Smoke:
    def __init__(
        self,
        base_url: str,
        fixture: Path,
        log_dir: Path,
        timeout: float,
        verbose: bool,
        user_agent: str,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.fixture = fixture
        self.timeout = timeout
        self.verbose = verbose
        self.user_agent = user_agent
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.run_dir = log_dir / f"{run_id}-{socket.gethostname()}"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.results: list[StepResult] = []
        self.app_name: str | None = None
        self.session_id_1: str | None = None
        self.session_id_2: str | None = None
        self.report_1_narrative: str | None = None
        self.report_2_narrative: str | None = None

    # -- I/O primitives --------------------------------------------------

    def _request(
        self, method: str, path: str, body: bytes | None = None
    ) -> tuple[int, dict[str, str], bytes, int]:
        """Return (status, headers, body, latency_ms). Never raises on HTTP errors."""
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, method=method)
        req.add_header("accept", "application/json")
        # Cloudflare's default WAF returns 1010 to Python-urllib/*; send a
        # realistic UA so the tunnel behaves the same way a phone would.
        req.add_header("user-agent", self.user_agent)
        if body is not None:
            req.add_header("content-type", "application/json")
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, data=body, timeout=self.timeout) as resp:
                resp_body = resp.read()
                headers = {k.lower(): v for k, v in resp.headers.items()}
                status = resp.status
        except urllib.error.HTTPError as exc:
            resp_body = exc.read() if hasattr(exc, "read") else b""
            headers = {k.lower(): v for k, v in (exc.headers or {}).items()}
            status = exc.code
        except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError) as exc:
            latency = int((time.perf_counter() - t0) * 1000)
            return -1, {"_error": repr(exc)}, b"", latency
        latency = int((time.perf_counter() - t0) * 1000)
        return status, headers, resp_body, latency

    def _persist(
        self,
        step_index: int,
        step_name: str,
        method: str,
        path: str,
        status: int,
        headers: dict[str, str],
        body: bytes,
        latency_ms: int,
        request_body: bytes | None = None,
    ) -> None:
        prefix = f"{step_index:02d}-{step_name}"
        envelope = {
            "request": {"method": method, "url": f"{self.base_url}{path}"},
            "response": {
                "status": status,
                "latency_ms": latency_ms,
                "headers": headers,
                "body_bytes": len(body),
            },
        }
        (self.run_dir / f"{prefix}-meta.json").write_text(json.dumps(envelope, indent=2))
        if request_body is not None:
            (self.run_dir / f"{prefix}-request.json").write_bytes(request_body)
        if body:
            (self.run_dir / f"{prefix}-response.json").write_bytes(body)

    def _record(self, name: str, ok: bool, latency_ms: int, detail: str) -> None:
        self.results.append(StepResult(name, ok, latency_ms, detail))
        marker = "PASS" if ok else "FAIL"
        print(f"  [{marker}] {name} ({latency_ms} ms) — {detail}")

    # -- Steps -----------------------------------------------------------

    def step_preflight(self) -> bool:
        if not self.fixture.is_file():
            self._record("preflight", False, 0, f"fixture missing: {self.fixture}")
            return False
        raw = self.fixture.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()[:16]
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            self._record("preflight", False, 0, f"fixture invalid JSON: {exc}")
            return False
        movement = data.get("metadata", {}).get("movement")
        n_frames = len(data.get("frames", []))
        n_emg = len(data.get("emg", []) or [])
        has_consent = bool(data.get("consent"))
        meta = {
            "base_url": self.base_url,
            "fixture": str(self.fixture),
            "fixture_sha256_16": digest,
            "fixture_movement": movement,
            "fixture_frames": n_frames,
            "fixture_emg_channels": n_emg,
            "fixture_has_consent": has_consent,
            "run_dir": str(self.run_dir),
            "started_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        (self.run_dir / "00-preflight.json").write_text(json.dumps(meta, indent=2))
        self._record(
            "preflight",
            True,
            0,
            f"fixture {digest} movement={movement} frames={n_frames} emg={n_emg} consent={has_consent}",
        )
        self._fixture_data = data
        self._fixture_bytes = raw
        return True

    def step_health(self) -> bool:
        status, headers, body, latency = self._request("GET", "/health")
        self._persist(1, "health", "GET", "/health", status, headers, body, latency)
        if status != 200:
            self._record("health", False, latency, f"status={status} body={body[:200]!r}")
            return False
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            self._record("health", False, latency, f"non-JSON body: {exc}")
            return False
        if payload.get("status") != "ok":
            self._record("health", False, latency, f"status field != ok: {payload!r}")
            return False
        self.app_name = payload.get("app")
        retention = payload.get("default_retention_days")
        cf_ray = headers.get("cf-ray", "no-cf-ray")
        # default_retention_days lands on /health in commit 8b7dce6 (ML#20).
        # Don't fail the gate when it's missing — older builds predate the
        # field — but surface it so deploy currency is visible.
        retention_str = (
            f"retention_days={retention}"
            if isinstance(retention, int) and retention >= 1
            else "retention=MISSING(pre-ML#20)"
        )
        self._record(
            "health", True, latency, f"app={self.app_name!r} {retention_str} cf-ray={cf_ray}"
        )
        return True

    def step_openapi(self) -> bool:
        status, headers, body, latency = self._request("GET", "/openapi.json")
        self._persist(2, "openapi", "GET", "/openapi.json", status, headers, body, latency)
        if status != 200:
            self._record("openapi", False, latency, f"status={status}")
            return False
        try:
            spec = json.loads(body)
        except json.JSONDecodeError as exc:
            self._record("openapi", False, latency, f"non-JSON: {exc}")
            return False
        paths = spec.get("paths", {}) or {}
        schemas = (spec.get("components", {}) or {}).get("schemas", {}) or {}
        missing_paths = [
            f"{method.upper()} {p}" for p, method in EXPECTED_PATHS
            if p not in paths or method not in (paths.get(p, {}) or {})
        ]
        missing_schemas = [
            "|".join(group) for group in EXPECTED_SCHEMA_GROUPS
            if not any(s in schemas for s in group)
        ]
        title = (spec.get("info", {}) or {}).get("title")
        if missing_paths or missing_schemas:
            self._record(
                "openapi",
                False,
                latency,
                f"title={title!r} missing_paths={missing_paths} missing_schemas={missing_schemas}",
            )
            return False
        self._record(
            "openapi",
            True,
            latency,
            f"title={title!r} paths={len(paths)} schemas={len(schemas)} (Session/Report/Consent present)",
        )
        return True

    def step_post_session(self, slot: int) -> str | None:
        status, headers, body, latency = self._request(
            "POST", "/sessions", body=self._fixture_bytes
        )
        self._persist(
            slot,
            f"post-session-{slot}",
            "POST",
            "/sessions",
            status,
            headers,
            body,
            latency,
            request_body=self._fixture_bytes,
        )
        if status not in (200, 201):
            self._record(
                f"post-session-{slot}", False, latency, f"status={status} body={body[:200]!r}"
            )
            return None
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            self._record(f"post-session-{slot}", False, latency, f"non-JSON: {exc}")
            return None
        session_id = payload.get("session_id")
        frames_received = payload.get("frames_received")
        expected_frames = len(self._fixture_data.get("frames", []))
        if not session_id:
            self._record(
                f"post-session-{slot}", False, latency, f"no session_id: {payload!r}"
            )
            return None
        if frames_received != expected_frames:
            self._record(
                f"post-session-{slot}",
                False,
                latency,
                f"frames_received={frames_received} expected={expected_frames}",
            )
            return None
        self._record(
            f"post-session-{slot}",
            True,
            latency,
            f"session_id={session_id} frames_received={frames_received}",
        )
        return session_id

    def step_get_report(self, slot: int, session_id: str) -> str | None:
        path = f"/sessions/{urllib.parse.quote(session_id)}/report"
        status, headers, body, latency = self._request("GET", path)
        self._persist(slot, f"get-report-{slot}", "GET", path, status, headers, body, latency)
        if status != 200:
            self._record(
                f"get-report-{slot}", False, latency, f"status={status} body={body[:200]!r}"
            )
            return None
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            self._record(f"get-report-{slot}", False, latency, f"non-JSON: {exc}")
            return None
        meta = payload.get("metadata") or {}
        meta_session_id = meta.get("session_id")
        meta_movement = meta.get("movement")
        narrative = payload.get("overall_narrative")
        # chain_observations live inside movement_section, not at the top
        # level — earlier smoke runs reported 0 because they read the wrong
        # path. Top-level chain_observations does not exist on Report.
        movement_section = payload.get("movement_section") or {}
        chain_obs = movement_section.get("chain_observations") or []
        problems: list[str] = []
        if meta_session_id != session_id:
            problems.append(f"metadata.session_id={meta_session_id} != {session_id}")
        expected_movement = self._fixture_data.get("metadata", {}).get("movement")
        if meta_movement != expected_movement:
            problems.append(f"metadata.movement={meta_movement} != {expected_movement}")
        if not isinstance(narrative, str) or not narrative.strip():
            problems.append(f"overall_narrative empty/non-str ({narrative!r})")
        if problems:
            self._record(f"get-report-{slot}", False, latency, "; ".join(problems))
            return None
        self._record(
            f"get-report-{slot}",
            True,
            latency,
            f"narrative_chars={len(narrative)} chain_observations={len(chain_obs)}",
        )
        if self.verbose:
            print(f"      narrative: {narrative!r}")
        return narrative

    def step_reasoner_fires(self, slot: int, fixture_path: Path) -> bool:
        """Post a known-bad fixture and assert ≥1 chain_observation comes back.

        Without this, a regressed reasoner that always returns no observations
        would still pass the rest of the smoke (clean fixture is silent by
        design). We pick the valgus fixture because it deterministically
        triggers the SBL knee_valgus rule on a healthy build.
        """
        if not fixture_path.is_file():
            self._record(
                "reasoner-fires",
                False,
                0,
                f"valgus fixture missing: {fixture_path}",
            )
            return False
        body = fixture_path.read_bytes()
        status, headers, resp_body, latency = self._request("POST", "/sessions", body=body)
        self._persist(
            slot,
            "post-session-valgus",
            "POST",
            "/sessions",
            status,
            headers,
            resp_body,
            latency,
            request_body=body,
        )
        if status not in (200, 201):
            self._record(
                "reasoner-fires", False, latency, f"POST status={status} body={resp_body[:200]!r}"
            )
            return False
        try:
            session_id = json.loads(resp_body)["session_id"]
        except (json.JSONDecodeError, KeyError) as exc:
            self._record("reasoner-fires", False, latency, f"bad POST body: {exc}")
            return False
        path = f"/sessions/{urllib.parse.quote(session_id)}/report"
        status2, headers2, resp_body2, latency2 = self._request("GET", path)
        self._persist(
            slot + 1,
            "get-report-valgus",
            "GET",
            path,
            status2,
            headers2,
            resp_body2,
            latency2,
        )
        if status2 != 200:
            self._record(
                "reasoner-fires", False, latency2, f"GET status={status2} body={resp_body2[:200]!r}"
            )
            return False
        try:
            report = json.loads(resp_body2)
        except json.JSONDecodeError as exc:
            self._record("reasoner-fires", False, latency2, f"non-JSON report: {exc}")
            return False
        chain_obs = (report.get("movement_section") or {}).get("chain_observations") or []
        if not chain_obs:
            self._record(
                "reasoner-fires",
                False,
                latency + latency2,
                "valgus fixture returned 0 chain_observations — reasoner regressed or rules broke",
            )
            return False
        chains = sorted({o.get("chain") for o in chain_obs})
        severities = sorted({o.get("severity") for o in chain_obs})
        self._record(
            "reasoner-fires",
            True,
            latency + latency2,
            f"{len(chain_obs)} observation(s); chains={chains} severities={severities}",
        )
        if self.verbose:
            for o in chain_obs[:3]:
                print(f"      {o.get('chain')}/{o.get('severity')}: {o.get('narrative','')[:80]!r}")
        return True

    def step_pose_only(self, slot: int, fixture_path: Path) -> bool:
        """Post the pose-only fixture and assert the Report shape is well-formed.

        Pose-only is the showcase narrative beat (no hardware in the loop).
        A regression that breaks the optional-EMG path would still pass the
        rest of the smoke (default fixture is EMG-bearing), so this step is
        the safety net for the no-hardware Report path.
        """
        if not fixture_path.is_file():
            self._record(
                "pose-only",
                False,
                0,
                f"pose-only fixture missing: {fixture_path}",
            )
            return False
        body = fixture_path.read_bytes()
        # Sanity: this fixture really is pose-only (no emg, no consent).
        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            self._record("pose-only", False, 0, f"non-JSON fixture: {exc}")
            return False
        if data.get("emg") or data.get("consent"):
            self._record(
                "pose-only",
                False,
                0,
                "pose-only fixture has emg/consent — not pose-only",
            )
            return False
        status, headers, resp_body, latency = self._request("POST", "/sessions", body=body)
        self._persist(
            slot,
            "post-session-pose-only",
            "POST",
            "/sessions",
            status,
            headers,
            resp_body,
            latency,
            request_body=body,
        )
        if status not in (200, 201):
            self._record(
                "pose-only", False, latency, f"POST status={status} body={resp_body[:200]!r}"
            )
            return False
        try:
            session_id = json.loads(resp_body)["session_id"]
        except (json.JSONDecodeError, KeyError) as exc:
            self._record("pose-only", False, latency, f"bad POST body: {exc}")
            return False
        path = f"/sessions/{urllib.parse.quote(session_id)}/report"
        status2, headers2, resp_body2, latency2 = self._request("GET", path)
        self._persist(
            slot + 1,
            "get-report-pose-only",
            "GET",
            path,
            status2,
            headers2,
            resp_body2,
            latency2,
        )
        if status2 != 200:
            self._record(
                "pose-only", False, latency2, f"GET status={status2} body={resp_body2[:200]!r}"
            )
            return False
        try:
            report = json.loads(resp_body2)
        except json.JSONDecodeError as exc:
            self._record("pose-only", False, latency2, f"non-JSON report: {exc}")
            return False
        movement_section = report.get("movement_section") or {}
        per_rep = movement_section.get("per_rep_metrics")
        chain_obs = movement_section.get("chain_observations")
        problems: list[str] = []
        # per_rep may be absent if quality_gate rejected the session, but if
        # present it must have a `reps` list (possibly empty for short clips).
        if per_rep is not None and "reps" not in per_rep:
            problems.append(f"per_rep_metrics missing 'reps' key: {list(per_rep.keys())}")
        # chain_observations may be omitted (= empty), but never the wrong type.
        if chain_obs is not None and not isinstance(chain_obs, list):
            problems.append(f"chain_observations non-list: {type(chain_obs).__name__}")
        if problems:
            self._record("pose-only", False, latency + latency2, "; ".join(problems))
            return False
        n_reps = len(per_rep.get("reps", [])) if per_rep else 0
        n_obs = len(chain_obs) if chain_obs else 0
        self._record(
            "pose-only",
            True,
            latency + latency2,
            f"reps={n_reps} chain_observations={n_obs} (no emg, no consent)",
        )
        return True

    def step_determinism(self) -> bool:
        if self.report_1_narrative is None or self.report_2_narrative is None:
            self._record("determinism", False, 0, "missing one or both narratives")
            return False
        if self.report_1_narrative == self.report_2_narrative:
            self._record(
                "determinism",
                True,
                0,
                "narratives identical across two posts of the same fixture",
            )
            return True
        self._record(
            "determinism",
            False,
            0,
            f"narratives diverged: r1={self.report_1_narrative!r} r2={self.report_2_narrative!r}",
        )
        return False

    # -- Driver ----------------------------------------------------------

    def run(
        self,
        skip_determinism: bool,
        valgus_fixture: Path | None,
        pose_only_fixture: Path | None,
    ) -> int:
        print(f"== smoke run → {self.base_url}")
        print(f"   logs → {self.run_dir}")
        if not self.step_preflight():
            return 2
        if not self.step_health():
            return self._finish()
        if not self.step_openapi():
            return self._finish()
        self.session_id_1 = self.step_post_session(3)
        if not self.session_id_1:
            return self._finish()
        self.report_1_narrative = self.step_get_report(4, self.session_id_1)
        if self.report_1_narrative is None:
            return self._finish()
        if skip_determinism:
            print("   (skipping determinism re-post + reasoner-fires + pose-only per --quick)")
            return self._finish()
        self.session_id_2 = self.step_post_session(5)
        if not self.session_id_2:
            return self._finish()
        self.report_2_narrative = self.step_get_report(6, self.session_id_2)
        if self.report_2_narrative is None:
            return self._finish()
        self.step_determinism()
        if valgus_fixture is not None:
            self.step_reasoner_fires(7, valgus_fixture)
        if pose_only_fixture is not None:
            self.step_pose_only(9, pose_only_fixture)
        return self._finish()

    def _finish(self) -> int:
        summary = {
            "base_url": self.base_url,
            "app_name": self.app_name,
            "session_ids": [s for s in (self.session_id_1, self.session_id_2) if s],
            "results": [dataclasses.asdict(r) for r in self.results],
            "all_passed": all(r.ok for r in self.results),
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        (self.run_dir / "99-summary.json").write_text(json.dumps(summary, indent=2))
        passed = sum(1 for r in self.results if r.ok)
        total = len(self.results)
        print(f"== {passed}/{total} steps passed — summary: {self.run_dir}/99-summary.json")
        return 0 if summary["all_passed"] else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    p.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIR)
    p.add_argument("--timeout", type=float, default=30.0)
    p.add_argument("--quick", action="store_true", help="skip determinism re-post + reasoner-fires + pose-only steps")
    p.add_argument("--valgus-fixture", type=Path, default=DEFAULT_VALGUS_FIXTURE)
    p.add_argument("--no-valgus", action="store_true", help="skip the reasoner-fires step")
    p.add_argument("--pose-only-fixture", type=Path, default=DEFAULT_POSE_ONLY_FIXTURE,
                   help="fixture for the no-hardware showcase path (sibling bioliminal-ops repo by default)")
    p.add_argument("--no-pose-only", action="store_true", help="skip the pose-only step")
    p.add_argument("-v", "--verbose", action="store_true", help="echo report narratives")
    p.add_argument(
        "--user-agent",
        default=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 bioliminal-smoke/1.0"
        ),
        help="UA header (default mimics Chrome + bioliminal-smoke tag so the Cloudflare WAF doesn't 1010 us)",
    )
    args = p.parse_args(argv)
    smoke = Smoke(
        base_url=args.base_url,
        fixture=args.fixture,
        log_dir=args.log_dir,
        timeout=args.timeout,
        verbose=args.verbose,
        user_agent=args.user_agent,
    )
    valgus = None if args.no_valgus else args.valgus_fixture
    pose_only = None if args.no_pose_only else args.pose_only_fixture
    return smoke.run(
        skip_determinism=args.quick,
        valgus_fixture=valgus,
        pose_only_fixture=pose_only,
    )


if __name__ == "__main__":
    sys.exit(main())
