---
name: contact-tracing
description: "Network-based contact tracing: generation intervals, secondary attack rates,..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [contact-tracing, transmission-network, generation-interval, superspreader, outbreak-response]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"👥","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"matplotlib","bins":[]}],"trigger_keywords":["trace","contact tracing","transmission chain","generation interval","secondary attack rate","superspreader","who infected whom","exposure network"]}}
---

# 👥 Contact Tracing

Use this skill when the user needs network-based contact tracing: generation intervals, secondary attack rates, superspreader detection.

## OpenClaw Routing

- Route here for: `trace`, `contact tracing`, `transmission chain`, `generation interval`, `secondary attack rate`, `superspreader`
- Alias: `trace`
- Entrypoint: `skills/contact-tracing/contact_tracing.py`
- Expected inputs: Linelists, case counts, exposure histories, contact networks, or outbreak framing questions.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `rt-estimator`, `epi-orchestrator`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `trace`
- `contact tracing`
- `transmission chain`
- `generation interval`
- `secondary attack rate`
- `superspreader`
- `who infected whom`
- `exposure network`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python contact_tracing.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
