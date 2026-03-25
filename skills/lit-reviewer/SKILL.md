---
name: lit-reviewer
description: "PubMed and bioRxiv/medRxiv literature search; structured briefings with abstracts,..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [literature, pubmed, research, systematic-review]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"\ud83d\udcc4","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"requests","bins":[]}],"trigger_keywords":["lit review","lit reviewer","pubmed","literature search","research briefing","systematic review","papers about","recent studies","what does the literature say"]}}
---

# 📄 Lit Reviewer

Use this skill when the user needs pubMed and bioRxiv/medRxiv literature search; structured briefings with abstracts, MeSH terms, and key findings.

## OpenClaw Routing

- Route here for: `lit review`, `lit reviewer`, `pubmed`, `literature search`, `research briefing`, `systematic review`
- Alias: `lit-review`
- Entrypoint: `skills/lit-reviewer/lit_reviewer.py`
- Expected inputs: Disease names, pathogen names, destination countries, literature questions, or surveillance briefing prompts.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `disease-profiler`, `pathogen-intel`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `lit review`
- `lit reviewer`
- `pubmed`
- `literature search`
- `research briefing`
- `systematic review`
- `papers about`
- `recent studies`
- `what does the literature say`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python lit_reviewer.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
