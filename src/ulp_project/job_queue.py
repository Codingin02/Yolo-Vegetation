"""Minimal JSON job queue stored under ignored data/runtime."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .paths import PROJECT_ROOT

RUNTIME_ROOT = PROJECT_ROOT / "data" / "runtime"
JOBS_DIR = RUNTIME_ROOT / "jobs"
RESULTS_DIR = RUNTIME_ROOT / "results"


def new_job_id(prefix: str = "job") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{prefix}_{stamp}_{uuid4().hex[:8]}"


def create_job(metadata: dict[str, object], runtime_root: Path = RUNTIME_ROOT) -> dict[str, object]:
    job_id = str(metadata.get("job_id") or new_job_id())
    jobs_dir = runtime_root / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    job = {
        "job_id": job_id,
        "status": "QUEUED",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata,
    }
    (jobs_dir / f"{job_id}.json").write_text(json.dumps(job, indent=2, ensure_ascii=False), encoding="utf-8")
    return job


def load_job(job_id: str, runtime_root: Path = RUNTIME_ROOT) -> dict[str, object]:
    path = runtime_root / "jobs" / f"{job_id}.json"
    if not path.exists():
        return {"status": "JOB_NOT_FOUND", "job_id": job_id}
    return json.loads(path.read_text(encoding="utf-8"))


def write_job_result(job_id: str, result: dict[str, object], runtime_root: Path = RUNTIME_ROOT) -> dict[str, object]:
    results_dir = runtime_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "job_id": job_id,
        "status": result.get("status", "RESULT_READY"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "result": result,
    }
    path = results_dir / f"{job_id}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"status": "RESULT_WRITTEN", "job_id": job_id, "result_json_path": str(path)}


def load_job_result(job_id: str, runtime_root: Path = RUNTIME_ROOT) -> dict[str, object]:
    path = runtime_root / "results" / f"{job_id}.json"
    if not path.exists():
        return {"status": "RESULT_NOT_READY", "job_id": job_id}
    return json.loads(path.read_text(encoding="utf-8"))
