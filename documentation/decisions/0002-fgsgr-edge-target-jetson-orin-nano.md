# Decision 0002 — Deploy FGSGR on NVIDIA Jetson Orin Nano

**Date:** 2026  
**Status:** Decided — hardware selected

## Decision

The FGSGR reasoning engine deploys exclusively on the NVIDIA Jetson Orin Nano. No cloud fallback.

## Alternatives considered

- Cloud inference (AWS, GCP) — ruled out: unacceptable latency for real-time flight control; fails in contested/disconnected environments
- x86 edge server — too heavy; drone swarm agents need compact, low-power boards
- Raspberry Pi / similar ARM SBCs — insufficient CUDA/tensor compute for the KAN + VAE-KL pipeline

## Why Jetson Orin Nano

- On-board CUDA cores support torch inference without cloud
- Low power envelope compatible with drone power budgets
- ARM64 architecture with NVIDIA GPU acceleration
- Sufficient VRAM for the tri-band spectral + metacognitive grid pipeline (with VRAM discipline)

## Consequences

- **All FGSGR modules must be VRAM-efficient** — no large FF layers, no parallel routing matrices
- **Dependencies:** `torch`, `numpy`, standard Python math only — no libraries that make network calls
- **No live backprop in `forward()`** — gradient tracking exhausts VRAM at inference time
- **No `torch.compile()` with dynamic shapes** — Jetson TensorRT path requires static shapes or careful dynamic shape handling
- x86-specific intrinsics and CUDA features above Orin Nano's SM version must not be used
