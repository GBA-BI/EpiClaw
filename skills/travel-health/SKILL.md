---
name: travel-health
description: "Travel health risk assessment: country disease risk matrix, vaccine and prophylaxis..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [travel-health, travel-medicine, country-risk, vaccination, malaria-prophylaxis, WHO-outbreak]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"✈️","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]}],"trigger_keywords":["travel","travel health","travel medicine","pre-travel advice","destination health","malaria prophylaxis","yellow fever vaccination","travel risk"]}}
---

# ✈️ Travel Health

Use this skill when the user needs travel health risk assessment: country disease risk matrix, vaccine and prophylaxis recommendations, WHO outbreak news integration.

## OpenClaw Routing

- Route here for: `travel`, `travel health`, `travel medicine`, `pre-travel advice`, `destination health`, `malaria prophylaxis`
- Alias: `travel`
- Entrypoint: `skills/travel-health/travel_health.py`
- Expected inputs: Disease names, pathogen names, destination countries, literature questions, or surveillance briefing prompts.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `lit-reviewer`, `disease-profiler`, `pathogen-intel`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `travel`
- `travel health`
- `travel medicine`
- `pre-travel advice`
- `destination health`
- `malaria prophylaxis`
- `yellow fever vaccination`
- `travel risk`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python travel_health.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
