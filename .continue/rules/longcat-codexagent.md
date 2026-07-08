---
name: LongCat CodexAgent Safety
---

- Treat LongCat responses as advisory, not authoritative.
- Do not download model weights, start services, or install heavy runtimes unless the user explicitly asks.
- Prefer localhost OpenAI-compatible endpoints.
- Do not read or expose secrets, tokens, cookies, passwords, browser profiles, or private URLs.
- Run local syntax/tests/security checks before accepting generated code.
- If the endpoint is unavailable, report `blocked_not_ready` and continue with normal local analysis.

