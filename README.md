# LongCat CodexAgent VS Code Pack

Clean, lightweight integration pack for using LongCat-2.0 as an advisory coding-agent helper in a local CodexAgent workflow.

This repository does not contain model weights, secrets, cookies, browser profiles, background services, scheduled tasks, or runtime caches.

## What This Pack Does

- Adds a `longcat_local_agent` route definition for CodexAgent-style workflows.
- Adds the `longcat-local-agent` skill with safety rules and source notes.
- Provides `scripts/run_longcat_local_agent.py` for:
  - route checks;
  - bounded GitHub source sync from `meituan-longcat/LongCat-2.0`;
  - local readiness checks;
  - localhost OpenAI-compatible endpoint probes;
  - optional advisory prompt calls when explicitly allowed.
- Provides VS Code tasks and launch configs for the helper scripts.
- Provides a Continue config example for an OpenAI-compatible local endpoint.

## What This Pack Does Not Do

- It does not download LongCat model weights.
- It does not install SGLang, vLLM, Docker, CUDA kernels, package managers, or model runtimes.
- It does not start LongCat automatically.
- It does not create watchers, services, startup entries, scheduled tasks, or strict hooks.
- It does not send code to remote endpoints unless you explicitly run the script with `--allow-remote-endpoint`.

## Expected Endpoint

By default, the helper expects a local OpenAI-compatible endpoint:

```text
http://127.0.0.1:13423
```

The default model id is:

```text
meituan-longcat/LongCat-2.0-FP8
```

LongCat-2.0 is a very large MoE model. The official GPU deployment guidance recommends multi-GPU SGLang deployment. On ordinary developer workstations, this pack should be treated as an adapter to an already-running endpoint, not as a full local serving installer.

## Quick Start

```powershell
python -m pip install -r requirements.txt
python .\scripts\run_longcat_local_agent.py --route-check --task "LongCat repo-level code review" --json
python .\scripts\run_longcat_local_agent.py --check --json
python .\scripts\run_longcat_local_agent.py --check --probe-endpoint --base-url http://127.0.0.1:13423 --json
python .\scripts\validate_longcat_local_agent.py
```

To sync the lightweight upstream source metadata:

```powershell
python .\scripts\run_longcat_local_agent.py --sync-github --json
```

This sync clones only the public LongCat GitHub source repository. It does not download model weights.

## Optional Advisory Call

Use only when an endpoint is already running and you want to send a prompt to it:

```powershell
python .\scripts\run_longcat_local_agent.py --prompt "Review this repository plan" --allow-endpoint-call --base-url http://127.0.0.1:13423 --json
```

Remote endpoints are blocked by default. To use a remote OpenAI-compatible endpoint, you must explicitly pass `--allow-remote-endpoint`; do not put API keys in committed files.

## VS Code

Install recommended extensions from `.vscode/extensions.json`, then run tasks:

- `LongCat: route check`
- `LongCat: readiness check`
- `LongCat: probe local endpoint`
- `LongCat: sync GitHub source`
- `LongCat: validate pack`

For Continue, see:

- `docs/continue-config.example.yaml`
- `.continue/rules/longcat-codexagent.md`

Copy the example into your local Continue config and keep real secrets in your local `.env`, not in git.

## Source Notes

- Official LongCat repository: <https://github.com/meituan-longcat/LongCat-2.0>
- Local lightweight source evidence is stored under `archive/source_materials/longcat_2_meituan_20260707`.
- See `.agents/skills/longcat-local-agent/references/source_map.md`.

## Safety Model

LongCat output is advisory. The main coding agent remains responsible for reading code, applying minimal patches, running tests, checking security boundaries, and reporting unverified assumptions.

