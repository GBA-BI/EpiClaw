---
name: epi-gis
description: "Geospatial disease mapping: GeoPandas choropleths, SaTScan-style cluster detection,..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [geospatial, choropleth, spatial-clustering, Morans-I, hotspot, SaTScan]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"🗺️","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"numpy","bins":[]},{"kind":"uv","package":"scipy","bins":[]},{"kind":"uv","package":"matplotlib","bins":[]},{"kind":"uv","package":"geopandas","bins":[]},{"kind":"uv","package":"folium","bins":[]}],"trigger_keywords":["gis","epi gis","spatial analysis","choropleth","hotspot","cluster detection","moran's i","spatial autocorrelation","geospatial epidemiology","disease mapping"]}}
---

# 🗺️ Epi GIS

Use this skill when the user needs geospatial disease mapping: GeoPandas choropleths, SaTScan-style cluster detection, Moran's I spatial autocorrelation, Folium interactive maps.

## OpenClaw Routing

- Route here for: `gis`, `epi gis`, `spatial analysis`, `choropleth`, `hotspot`, `cluster detection`
- Alias: `gis`
- Entrypoint: `skills/epi-gis/epi_gis.py`
- Expected inputs: Point/location tables, regional incidence data, shapefiles/GeoJSON-compatible data, or climate time series.

## Execution Notes

- Prefer real user inputs when they are available.
- Fall back to `--demo` when the user has no local dataset yet.
- Let OpenClaw attempt to install missing CLI, Python, or R dependencies automatically at runtime. Fall back only if installation fails.
- Write `report.md` and `result.json`, plus any skill-specific tables, figures, or HTML outputs.

## Chaining

- Works well with: `multi-pathogen-dashboard`, `climate-health`, `pathogen-intel`
- Cite whether results came from user input, demo data, or external connectors.

## Trigger Keywords

- `gis`
- `epi gis`
- `spatial analysis`
- `choropleth`
- `hotspot`
- `cluster detection`
- `moran's i`
- `spatial autocorrelation`
- `geospatial epidemiology`
- `disease mapping`

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python epi_gis.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
