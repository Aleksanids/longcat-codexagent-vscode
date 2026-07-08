from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]


def run(args: list[str], expect: int = 0) -> tuple[int, str]:
    proc = subprocess.run(args, cwd=ROOT, text=True, encoding="utf-8", errors="replace", capture_output=True)
    output = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != expect:
        raise AssertionError(f"{args} expected {expect}, got {proc.returncode}\n{output}")
    return proc.returncode, output


def load_json_output(args: list[str]) -> dict:
    _, output = run(args)
    return json.loads(output)


def main() -> int:
    errors: list[str] = []
    required_paths = [
        ".codex/agents/longcat_local_agent.toml",
        ".agents/skills/longcat-local-agent/SKILL.md",
        ".agents/skills/longcat-local-agent/references/source_map.md",
        "scripts/run_longcat_local_agent.py",
        "archive/source_materials/longcat_2_meituan_20260707/README.md",
        "archive/source_materials/longcat_2_meituan_20260707/LICENSE",
    ]
    for rel in required_paths:
        if not (ROOT / rel).exists():
            errors.append(f"missing required LongCat file: {rel}")

    try:
        route = load_json_output(
            [
                sys.executable,
                str(ROOT / "scripts" / "run_longcat_local_agent.py"),
                "--route-check",
                "--task",
                "LongCat repo-level code review with GitHub sync",
                "--json",
                "--no-report",
            ]
        )
        if not route["route"]["should_attach"]:
            errors.append("route-check did not attach for explicit LongCat task")
    except Exception as exc:
        errors.append(f"route-check failed: {exc}")

    try:
        large_task = (
            "Описание для Codex: кнопка Обновить реестр в TenderVestDocs.\n"
            "Pipeline: строка реестра -> поиск источников -> /api/import -> /api/refresh-sources -> "
            "RegistryEnrichmentService -> нормализация -> безопасная запись -> журнал обновления.\n"
            * 70
        )
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as handle:
            handle.write(large_task)
            temp_task = Path(handle.name)
        try:
            route_file = load_json_output(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "run_longcat_local_agent.py"),
                    "--route-check",
                    "--task-file",
                    str(temp_task),
                    "--json",
                    "--no-report",
                ]
            )
        finally:
            temp_task.unlink(missing_ok=True)
        if not route_file["route"]["should_attach"]:
            errors.append("route-check did not attach for large TenderVestDocs pipeline task")
    except Exception as exc:
        errors.append(f"route-check task-file failed: {exc}")

    try:
        readiness = load_json_output(
            [
                sys.executable,
                str(ROOT / "scripts" / "run_longcat_local_agent.py"),
                "--check",
                "--json",
                "--no-report",
            ]
        )
        blockers = readiness["readiness"]["blockers"]
        if "workstation_not_sized_for_full_local_serving" not in blockers:
            errors.append("readiness missing hardware blocker disclosure")
        if readiness["readiness"]["policy"]["weights_download"] != "disabled":
            errors.append("weights download policy is not disabled")
        if readiness["readiness"]["source"]["present"] is not True:
            errors.append("LongCat source copy is not present")
    except Exception as exc:
        errors.append(f"readiness check failed: {exc}")

    try:
        run([sys.executable, str(ROOT / "scripts" / "validate_python_syntax.py"), str(ROOT / "scripts" / "run_longcat_local_agent.py")])
    except Exception as exc:
        errors.append(f"syntax validation failed: {exc}")

    if errors:
        print("LONGCAT LOCAL AGENT VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("LONGCAT LOCAL AGENT VALIDATION OK")
    print("mode=github_sync_plus_local_endpoint no_weights_download no_autostart")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
