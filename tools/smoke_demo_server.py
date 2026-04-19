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
DEFAULT_FIXTURE = (
    REPO_ROOT.parent
    / "bioliminal-ops"
    / "operations"
    / "handover"
    / "mobile"
    / "fixtures"
    / "sample_bicep_curl_with_emg.json"
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
EXPECTED_SCHEMAS: list[str] = [
    "Session",
    "SessionCreateResponse",
    "Report",
    "EvidenceBlock",  # proves ML#1 evidence-block requirement shipped
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
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.fixture = fixture
        self.timeout = timeout
        self.verbose = verbose
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
        cf_ray = headers.get("cf-ray", "no-cf-ray")
        self._record("health", True, latency, f"app={self.app_name!r} cf-ray={cf_ray}")
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
        missing_schemas = [s for s in EXPECTED_SCHEMAS if s not in schemas]
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
            f"title={title!r} paths={len(paths)} schemas={len(schemas)} (Evidence+Report+Session present)",
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
        chain_obs = payload.get("chain_observations") or []
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

    def run(self, skip_determinism: bool) -> int:
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
            print("   (skipping determinism re-post per --quick)")
            return self._finish()
        self.session_id_2 = self.step_post_session(5)
        if not self.session_id_2:
            return self._finish()
        self.report_2_narrative = self.step_get_report(6, self.session_id_2)
        if self.report_2_narrative is None:
            return self._finish()
        self.step_determinism()
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
    p.add_argument("--quick", action="store_true", help="skip determinism re-post")
    p.add_argument("-v", "--verbose", action="store_true", help="echo report narratives")
    args = p.parse_args(argv)
    smoke = Smoke(
        base_url=args.base_url,
        fixture=args.fixture,
        log_dir=args.log_dir,
        timeout=args.timeout,
        verbose=args.verbose,
    )
    return smoke.run(skip_determinism=args.quick)


if __name__ == "__main__":
    sys.exit(main())
