# LongCat Local Agent Source Map

## Primary sources

| Source | Local/remote path | Use |
|---|---|---|
| GitHub repository | `https://github.com/meituan-longcat/LongCat-2.0` | README, LICENSE, deployment notes, model facts. |
| Local source-copy | `archive/source_materials/longcat_2_meituan_20260707` | Pinned lightweight clone for offline evidence. |
| Hugging Face FP8 model card | `https://huggingface.co/meituan-longcat/LongCat-2.0-FP8` | Model ID, license, OpenAI-compatible endpoint examples for vLLM/SGLang. |
| Hugging Face base model card | `https://huggingface.co/meituan-longcat/LongCat-2.0` | Base model metadata and model card. |
| Hugging Face INT8 model card | `https://huggingface.co/meituan-longcat/LongCat-2.0-INT8` | Quantized model metadata. |

## Verified facts on 2026-07-07

- LongCat-2.0 is described by the official README/model card as a 1.6T-parameter MoE model with about 48B activated parameters per token.
- Official docs describe 1M-context training/use-case support and strong coding/agentic task focus.
- Official docs state model weights are released under MIT License.
- Official GPU deployment guidance recommends SGLang and 16x H20 using tensor/expert parallelism.
- Hugging Face provides OpenAI-compatible serving examples through vLLM/SGLang.
- Local machine inventory found NVIDIA GeForce RTX 2050 with 4096 MiB VRAM and about 16 GB RAM, so full local serving is not considered feasible on this workstation without external hardware/runtime provisioning.

## Local integration contract

- This skill does not download weights.
- This skill does not start background services.
- GitHub sync is bounded to source metadata and README/LICENSE evidence.
- Inference requires an already running local OpenAI-compatible endpoint.
- Remote endpoint calls require separate explicit approval.
