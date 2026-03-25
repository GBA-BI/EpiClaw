---
name: climate-health
description: "Climate-disease association analysis: DLNM distributed lag non-linear models;..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [climate-health, DLNM, temperature-disease, rainfall, ERA5, seasonal-epidemiology]
metadata: {"openclaw":{"requires":{"bins":["python3","Rscript"],"env":[],"config":[]},"always":false,"emoji":"🌡️","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"scipy","bins":[]},{"kind":"uv","package":"matplotlib","bins":[]},{"kind":"brew","formula":"r","bins":["Rscript"]}],"trigger_keywords":["climate","climate health","temperature and disease","dlnm","distributed lag","rainfall","climate change","malaria climate","dengue climate","seasonal epidemiology"]}}
---

# 🌡️ Climate Health

Use this skill when the user needs climate-disease association analysis: DLNM distributed lag non-linear models; temperature/rainfall vs. incidence; ERA5/NOAA data integration.

## OpenClaw Routing

- Route here for: `climate`, `climate health`, `temperature and disease`, `dlnm`, `distributed lag`, `rainfall`
- Alias: `climate`
- Entrypoint: `skills/climate-health/climate_health.py`
- Expected inputs: Point/location tables, regional incidence data, shapefiles/GeoJSON-compatible data, or climate time series.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `multi-pathogen-dashboard`, `pathogen-intel`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `climate`
- `climate health`
- `temperature and disease`
- `dlnm`
- `distributed lag`
- `rainfall`
- `climate change`
- `malaria climate`
- `dengue climate`
- `seasonal epidemiology`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python climate_health.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
