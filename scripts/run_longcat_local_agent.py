from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "archive" / "source_materials" / "longcat_2_meituan_20260707"
REPORTS_DIR = ROOT / "reports"
REPO_URL = "https://github.com/meituan-longcat/LongCat-2.0.git"
DEFAULT_BASE_URL = "http://127.0.0.1:13423"
DEFAULT_MODEL = "meituan-longcat/LongCat-2.0-FP8"
MODEL_IDS = [
    "meituan-longcat/LongCat-2.0",
    "meituan-longcat/LongCat-2.0-FP8",
    "meituan-longcat/LongCat-2.0-INT8",
]
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}


ROUTE_KEYWORDS: dict[str, int] = {
    "longcat": 5,
    "owl alpha": 5,
    "meituan": 4,
    "longcat-2.0": 5,
    "local llm": 4,
    "локальная модель": 4,
    "локальный агент": 4,
    "moe": 3,
    "1m context": 3,
    "1 million context": 3,
    "1 миллион": 3,
    "repo-level": 3,
    "repository-level": 3,
    "multi-file": 2,
    "large-context": 3,
    "большой контекст": 3,
    "code review": 2,
    "refactor": 2,
    "agentic": 3,
    "harness": 2,
    "pipeline": 2,
    "/api/": 2,
    "tendervestdocs": 2,
    "registryenrichmentservice": 2,
    "обновить реестр": 3,
    "архитектур": 2,
    "пайплайн": 2,
    "claude code": 3,
    "openclaw": 3,
    "hermes": 3,
    "github sync": 3,
    "гитхаб": 2,
}


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def run_cmd(args: list[str], cwd: Path | None = None, timeout: int = 15) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            args,
            cwd=cwd or ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        return {"ok": False, "exit_code": None, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "exit_code": None,
            "stdout": exc.stdout or "",
            "stderr": f"timeout after {timeout}s",
        }
    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def module_present(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def is_local_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    return host.lower() in LOCAL_HOSTS


def endpoint_url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + "/" + path.lstrip("/")


def route_decision(task: str) -> dict[str, Any]:
    task_lower = task.lower()
    matches: list[dict[str, Any]] = []
    score = 0
    for keyword, weight in ROUTE_KEYWORDS.items():
        if keyword in task_lower:
            matches.append({"keyword": keyword, "weight": weight})
            score += weight
    if len(task) >= 8000:
        matches.append({"keyword": "large_task_text", "weight": 3})
        score += 3
    should_attach = score >= 3
    if not task.strip():
        should_attach = False
    if "tiny typo" in task_lower or "опечатк" in task_lower:
        score = max(0, score - 2)
        should_attach = score >= 3
    return {
        "should_attach": should_attach,
        "score": score,
        "confidence": "high" if score >= 6 else "medium" if score >= 3 else "low",
        "matched_keywords": matches,
        "reasons": [
            reason
            for reason in [
                "explicit LongCat/local-agent signal" if any(item["weight"] >= 4 for item in matches) else "",
                "task may benefit from large-context or repo-level advisory review" if score >= 3 else "",
                "large task text suggests an advisory large-context model can be useful" if len(task) >= 8000 else "",
            ]
            if reason
        ],
        "policy": "attach only as advisory; endpoint call requires local endpoint and explicit allow flag",
    }


def source_commit() -> dict[str, Any]:
    if not SOURCE_DIR.is_dir():
        return {"present": False, "path": str(SOURCE_DIR), "commit": None, "dirty": None}
    if not (SOURCE_DIR / ".git").exists():
        return {
            "present": True,
            "path": str(SOURCE_DIR),
            "commit": None,
            "dirty": False,
            "status": "source evidence copy; not a git checkout",
        }
    commit = run_cmd(["git", "rev-parse", "HEAD"], cwd=SOURCE_DIR)
    dirty = run_cmd(["git", "status", "--short"], cwd=SOURCE_DIR)
    return {
        "present": True,
        "path": str(SOURCE_DIR),
        "commit": commit["stdout"] if commit["ok"] else None,
        "dirty": bool(dirty["stdout"]) if dirty["ok"] else None,
        "status": dirty["stdout"] if dirty["ok"] else dirty["stderr"],
    }


def sync_github() -> dict[str, Any]:
    SOURCE_DIR.parent.mkdir(parents=True, exist_ok=True)
    if not SOURCE_DIR.exists():
        clone = run_cmd(
            [
                "git",
                "-c",
                "http.sslBackend=schannel",
                "-c",
                "http.schannelCheckRevoke=false",
                "clone",
                "--depth",
                "1",
                REPO_URL,
                str(SOURCE_DIR),
            ],
            timeout=120,
        )
        return {"action": "clone", "ok": clone["ok"], "command": "git clone --depth 1", "output": clone, "source": source_commit()}
    if not (SOURCE_DIR / ".git").exists():
        init = run_cmd(["git", "init"], cwd=SOURCE_DIR, timeout=30)
        if not init["ok"]:
            return {"action": "init", "ok": False, "output": init, "source": source_commit()}
        remote = run_cmd(["git", "remote", "add", "origin", REPO_URL], cwd=SOURCE_DIR, timeout=30)
        if not remote["ok"] and "already exists" not in (remote["stderr"] + remote["stdout"]).lower():
            return {"action": "remote_add", "ok": False, "output": remote, "source": source_commit()}
    fetch = run_cmd(
        [
            "git",
            "-c",
            "http.sslBackend=schannel",
            "-c",
            "http.schannelCheckRevoke=false",
            "fetch",
            "--depth",
            "1",
            "origin",
            "main",
        ],
        cwd=SOURCE_DIR,
        timeout=120,
    )
    if not fetch["ok"]:
        return {"action": "fetch", "ok": False, "output": fetch, "source": source_commit()}
    reset = run_cmd(["git", "reset", "--hard", "FETCH_HEAD"], cwd=SOURCE_DIR, timeout=30)
    return {"action": "fetch_reset", "ok": reset["ok"], "fetch": fetch, "reset": reset, "source": source_commit()}


def hardware_inventory() -> dict[str, Any]:
    nvidia = run_cmd(
        ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
        timeout=10,
    )
    return {
        "nvidia_smi": nvidia,
        "full_local_serving_feasible": False,
        "feasibility_note": "Official LongCat GPU guidance recommends multi-GPU SGLang deployment; this wrapper requires an already running endpoint.",
    }


def runtime_inventory() -> dict[str, Any]:
    return {
        "python": sys.version.split()[0],
        "modules": {
            "requests": module_present("requests"),
            "torch": module_present("torch"),
            "sglang": module_present("sglang"),
            "vllm": module_present("vllm"),
            "transformers": module_present("transformers"),
            "huggingface_hub": module_present("huggingface_hub"),
        },
        "executables": {
            "git": run_cmd(["git", "--version"], timeout=5)["ok"],
            "docker": run_cmd(["docker", "--version"], timeout=5)["ok"],
            "uv": run_cmd(["uv", "--version"], timeout=5)["ok"],
        },
    }


def probe_endpoint(base_url: str, timeout: float) -> dict[str, Any]:
    if not is_local_url(base_url):
        return {
            "ok": False,
            "status": "remote_blocked",
            "base_url": base_url,
            "reason": "remote endpoint is disabled by default",
        }
    if not module_present("requests"):
        return {"ok": False, "status": "requests_missing", "base_url": base_url}
    import requests

    try:
        response = requests.get(endpoint_url(base_url, "/v1/models"), timeout=timeout)
    except requests.RequestException as exc:
        return {"ok": False, "status": "not_reachable", "base_url": base_url, "error": str(exc)}
    payload: Any
    try:
        payload = response.json()
    except ValueError:
        payload = response.text[:500]
    return {
        "ok": 200 <= response.status_code < 300,
        "status": "reachable" if 200 <= response.status_code < 300 else "http_error",
        "base_url": base_url,
        "status_code": response.status_code,
        "payload": payload,
    }


def build_readiness(base_url: str, probe: bool, timeout: float) -> dict[str, Any]:
    source = source_commit()
    runtime = runtime_inventory()
    hardware = hardware_inventory()
    endpoint = {"checked": False, "ok": False, "base_url": base_url}
    if probe:
        endpoint = {"checked": True, **probe_endpoint(base_url, timeout)}
    blockers: list[str] = []
    if not source["present"]:
        blockers.append("github_source_copy_missing")
    if not runtime["modules"]["requests"]:
        blockers.append("requests_module_missing")
    if probe and not endpoint["ok"]:
        blockers.append("local_endpoint_not_ready")
    if not probe:
        blockers.append("endpoint_not_probed")
    if not runtime["modules"]["sglang"] and not runtime["modules"]["vllm"]:
        blockers.append("local_serving_runtime_absent")
    blockers.append("workstation_not_sized_for_full_local_serving")
    status = "ready_for_endpoint_call" if probe and endpoint["ok"] else "blocked_not_ready"
    return {
        "status": status,
        "source": source,
        "runtime": runtime,
        "hardware": hardware,
        "endpoint": endpoint,
        "model_ids": MODEL_IDS,
        "blockers": blockers,
        "policy": {
            "weights_download": "disabled",
            "background_autostart": "disabled",
            "remote_endpoint_default": "disabled",
            "endpoint_call_requires_allow_flag": True,
        },
    }


def call_endpoint(base_url: str, model: str, prompt: str, timeout: float, allow_remote: bool) -> dict[str, Any]:
    if not is_local_url(base_url) and not allow_remote:
        return {"ok": False, "status": "remote_blocked", "reason": "remote endpoint requires --allow-remote-endpoint"}
    if not module_present("requests"):
        return {"ok": False, "status": "requests_missing"}
    import requests

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are an advisory code-review helper for CodexAgent. Do not claim tests passed unless evidence is provided.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    try:
        response = requests.post(endpoint_url(base_url, "/v1/chat/completions"), json=payload, timeout=timeout)
    except requests.RequestException as exc:
        return {"ok": False, "status": "not_reachable", "error": str(exc)}
    try:
        body: Any = response.json()
    except ValueError:
        body = response.text[:2000]
    return {
        "ok": 200 <= response.status_code < 300,
        "status": "completed" if 200 <= response.status_code < 300 else "http_error",
        "status_code": response.status_code,
        "body": body,
    }


def write_report(payload: dict[str, Any], report_dir: Path | None) -> Path:
    target_dir = report_dir or (REPORTS_DIR / f"longcat_local_agent_{now_stamp()}")
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / "readiness.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return path


def emit(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"status={payload.get('status', payload.get('action', 'ok'))}")
    if "route" in payload:
        route = payload["route"]
        print(f"should_attach={route['should_attach']} score={route['score']} confidence={route['confidence']}")
    if "readiness" in payload:
        print(f"readiness={payload['readiness']['status']}")
        print(f"blockers={', '.join(payload['readiness']['blockers'])}")
    if "report" in payload:
        print(f"report={payload['report']}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safe LongCat-2.0 local agent wrapper for CodexAgent.")
    parser.add_argument("--route-check", action="store_true", help="Decide whether LongCat should be attached for the task.")
    parser.add_argument("--task", default="", help="Task text for route detection.")
    parser.add_argument("--task-file", default="", help="UTF-8 task file for route detection.")
    parser.add_argument("--check", action="store_true", help="Run readiness checks.")
    parser.add_argument("--sync-github", action="store_true", help="Bounded GitHub source-copy sync. Does not download model weights.")
    parser.add_argument("--probe-endpoint", action="store_true", help="Probe local OpenAI-compatible endpoint.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="OpenAI-compatible base URL.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model id to call.")
    parser.add_argument("--prompt", default="", help="Prompt to send to LongCat endpoint.")
    parser.add_argument("--allow-endpoint-call", action="store_true", help="Allow sending prompt to the configured endpoint.")
    parser.add_argument("--allow-remote-endpoint", action="store_true", help="Allow non-local endpoint. Requires explicit user approval.")
    parser.add_argument("--timeout", type=float, default=5.0, help="Endpoint timeout in seconds.")
    parser.add_argument("--report-dir", default="", help="Optional report directory.")
    parser.add_argument("--no-report", action="store_true", help="Do not write a report file.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if not any([args.route_check, args.check, args.sync_github, args.prompt]):
        args.check = True
    task_text = args.task
    if args.task_file:
        task_path = Path(args.task_file)
        task_text = task_path.read_text(encoding="utf-8")

    payload: dict[str, Any] = {
        "status": "ok",
        "root": str(ROOT),
        "created_at": datetime.now().replace(microsecond=0).isoformat(),
    }
    exit_code = 0

    if args.route_check:
        payload["route"] = route_decision(task_text)
        if args.task_file:
            payload["route"]["task_file"] = str(Path(args.task_file).resolve())

    if args.sync_github:
        payload["sync"] = sync_github()
        if not payload["sync"]["ok"]:
            payload["status"] = "sync_failed"
            exit_code = 1

    if args.check or args.probe_endpoint:
        payload["readiness"] = build_readiness(args.base_url, args.probe_endpoint, args.timeout)

    if args.prompt:
        if not args.allow_endpoint_call:
            payload["status"] = "endpoint_call_blocked"
            payload["reason"] = "--allow-endpoint-call is required before sending prompts"
            exit_code = 2
        else:
            payload["endpoint_call"] = call_endpoint(
                args.base_url,
                args.model,
                args.prompt,
                args.timeout,
                args.allow_remote_endpoint,
            )
            if not payload["endpoint_call"]["ok"]:
                payload["status"] = "endpoint_call_failed"
                exit_code = 2

    if not args.no_report:
        report_dir = Path(args.report_dir).resolve() if args.report_dir else None
        payload["report"] = str(write_report(payload, report_dir))

    emit(payload, args.json)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
