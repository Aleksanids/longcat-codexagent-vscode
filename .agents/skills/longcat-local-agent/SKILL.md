---
name: longcat-local-agent
description: Safely attach LongCat-2.0 as a local CodexAgent advisory agent through GitHub source sync and a localhost OpenAI-compatible endpoint.
---

# LongCat Local Agent

## Purpose

Подключать LongCat-2.0 к CodexAgent как безопасный локальный advisory-agent для coding, repo-level, large-context and agentic workflow задач.

Интеграция состоит из двух частей:

- GitHub source sync: легковесная копия README/LICENSE/deployment guidance из `meituan-longcat/LongCat-2.0`.
- Local endpoint adapter: подключение к уже поднятому OpenAI-compatible endpoint LongCat на localhost.

## When to use

Используй этот skill, когда задача явно или косвенно выигрывает от LongCat:

- пользователь упоминает `LongCat`, `Owl Alpha`, `Meituan`, `LongCat-2.0`, MoE, 1M context, local LLM или локальный агент;
- задача про repo-level код, большой контекст, code review, multi-file refactor, agentic workflow, harness, Claude Code/OpenClaw/Hermes compatibility;
- нужно проверить или обновить pinned GitHub source-copy LongCat;
- нужно понять, можно ли подключить LongCat к текущему CodexAgent run.

## Inputs expected

- Подтвержденный root `D:\Codex\CodexAgent`.
- Текст задачи или краткий route card.
- Разрешение на endpoint call, если требуется фактически отправлять prompt в модель.
- Локальный base URL endpoint, если отличается от `http://127.0.0.1:13423`.
- Явное отдельное разрешение, если пользователь хочет скачивание весов, установку runtime, Docker, SGLang/vLLM, remote endpoint или автозапуск.

## Procedure

1. Подтверди root, scope, forbidden paths and acceptance criteria.
2. Выполни route-check:
   `python .\scripts\run_longcat_local_agent.py --route-check --task "<task>" --json`
3. Если `should_attach=false`, зафиксируй причину и не подключай LongCat.
4. Если `should_attach=true`, проверь readiness:
   `python .\scripts\run_longcat_local_agent.py --check --json`
5. Если нужна свежая source-copy из GitHub, выполни bounded sync:
   `python .\scripts\run_longcat_local_agent.py --sync-github --json`
6. Если endpoint уже поднят локально и пользователь разрешил вызов, проверь endpoint:
   `python .\scripts\run_longcat_local_agent.py --check --probe-endpoint --base-url http://127.0.0.1:13423 --json`
7. Для advisory ответа модели используй:
   `python .\scripts\run_longcat_local_agent.py --prompt "<prompt>" --allow-endpoint-call --base-url http://127.0.0.1:13423 --json`
8. Любой ответ LongCat считать advisory. Основной CodexAgent обязан проверить вывод через локальные tests, syntax, security and quality gates.

## Output format

1. Route decision: `should_attach`, reasons, confidence.
2. Readiness: hardware, runtime modules, source-copy, endpoint.
3. Action: `synced`, `checked`, `called` или controlled blocker.
4. Evidence: paths, commit, command and report path.
5. Risks, skipped checks and next action.

## Quality checks

- `python .\scripts\validate_longcat_local_agent.py`
- `python .\scripts\run_longcat_local_agent.py --route-check --task "LongCat repo-level code review" --json`
- `python .\scripts\run_longcat_local_agent.py --check --json`
- `python .\scripts\validate_agents.py`
- `python .\scripts\validate_skills.py`
- `python .\scripts\validate_skill_reference_links.py`
- `python .\scripts\validate_full_contour.py`

## Safety constraints

- Не скачивать веса модели автоматически.
- Не устанавливать `sglang`, `vllm`, `transformers`, Docker images, `uv`, CUDA kernels or package managers без отдельной прямой команды пользователя.
- Не создавать watchers, Scheduled Tasks, services, startup entries, background daemons or strict hooks.
- Не отправлять данные на remote endpoint without separate explicit permission.
- По умолчанию endpoint должен быть local-only: `localhost`, `127.0.0.1` or `::1`.
- Не читать/выводить `.env`, secrets, cookies, tokens, passwords, browser profiles or private URLs.

## Examples

- Вход: "LongCat помоги проверить большой refactor" -> route-check returns `should_attach=true`, readiness проверяется, endpoint используется только если local and allowed.
- Вход: "почини маленькую опечатку в README" -> `should_attach=false`; использовать обычный documentation/safe patch route.
- Вход: "обнови LongCat из GitHub" -> sync lightweight source-copy, record commit, no model weights.
- Вход: "подними LongCat полностью локально" -> hardware/runtime readiness; если железо не подходит, controlled blocker and provisioning note.

## Related agents

- `longcat_local_agent`
- `coding_agent_quality_operator`
- `external_agent_catalog_curator`
- `master_orchestrator_agent`

## Source notes

- Official GitHub: `https://github.com/meituan-longcat/LongCat-2.0`.
- Official Hugging Face FP8: `https://huggingface.co/meituan-longcat/LongCat-2.0-FP8`.
- Local source-copy: `archive/source_materials/longcat_2_meituan_20260707`.
- Detailed map: `references/source_map.md`.
