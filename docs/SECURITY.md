# Security Notes

This pack is intentionally conservative.

## Do Not Commit

- `.env`
- API keys
- access tokens
- cookies
- browser profiles
- private URLs
- model weights
- runtime caches
- generated reports with proprietary code snippets

## Endpoint Policy

Local endpoints are allowed by default:

- `localhost`
- `127.0.0.1`
- `::1`

Remote endpoints require explicit user approval and the `--allow-remote-endpoint` flag.

## Model Weights

This repository does not include LongCat weights. Use the official LongCat documentation and your own infrastructure plan if you need full serving.

