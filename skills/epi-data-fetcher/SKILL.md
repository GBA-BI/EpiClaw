---
name: epi-data-fetcher
description: "Download and normalize epidemiological surveillance time series from WHO GHO, Our..."
version: 0.1.0
author: EpiClaw Team
license: MIT
tags: [data, who, surveillance, time-series, covid, malaria, influenza, download]
metadata: {"openclaw":{"requires":{"bins":["python3"],"env":[],"config":[]},"always":false,"emoji":"\ud83d\udce5","homepage":"https://github.com/tsunyu/epiclaw","os":["darwin","linux"],"install":[{"kind":"uv","package":"requests","bins":[]}],"trigger_keywords":["fetch disease data","download surveillance data","get who data","who gho","our world in data","owid","ecdc data","get epidemiological data","retrieve case data","download incidence data","public health data","surveillance time series"]}}
---

# 📥 Epi Data Fetcher

Use this skill when the user needs to retrieve, download, or normalize epidemiological surveillance
data from public health databases for use in analysis or modeling.

## OpenClaw Routing

- Route here for: `fetch disease data`, `who gho`, `our world in data`, `ecdc data`, `download surveillance`
- Alias: `epi-data`
- Entrypoint: `skills/epi-data-fetcher/epi_data_fetcher.py`
- Expected inputs: Disease name, ISO3 country code (optional), year range, data source

## Data Sources

| Source | Coverage | Diseases | API Type |
|--------|----------|----------|----------|
| **WHO GHO** | Global, annual | Malaria, cholera, TB, HIV, measles, dengue, influenza | REST OData |
| **Our World in Data** | Global, daily | COVID-19, monkeypox | Public CSV |
| **ECDC** | Europe, weekly | Influenza, COVID-19 | Open CSV |

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--disease` | `malaria` | Disease name (malaria, cholera, covid-19, influenza, tuberculosis, hiv, measles, dengue) |
| `--source` | `who` | Data source: `who`, `owid`, `ecdc`, `all` |
| `--country` | global | ISO3 country code (NGA, USA, DEU...) or omit for all countries |
| `--year-start` | `2015` | Start year for WHO/annual data |
| `--year-end` | `2024` | End year for WHO/annual data |
| `--output` | `output/epi-data-fetcher` | Output directory |
| `--demo` | off | Run offline demo with synthetic data |

## Output Format

```
output/
├── data.csv          # Normalized records (source, indicator, country, date/year, value)
├── report.md         # Summary with record counts and downstream skill guidance
└── result.json       # Machine-readable summary envelope
```

**data.csv columns** (WHO GHO):
`source, indicator, country, year, value, dim1`

**data.csv columns** (OWID):
`source, indicator, country, date, new_cases, new_deaths, total_cases, total_deaths, new_vaccinations, people_fully_vaccinated_per_hundred`

## Example Commands

```bash
# Fetch WHO malaria data for Nigeria 2015–2024
python skills/epi-data-fetcher/epi_data_fetcher.py \
  --disease malaria --source who --country NGA --output output/malaria_nga

# Fetch COVID-19 data from OWID for Germany
python skills/epi-data-fetcher/epi_data_fetcher.py \
  --disease covid-19 --source owid --country DEU --output output/covid_deu

# Fetch all sources for influenza, global
python skills/epi-data-fetcher/epi_data_fetcher.py \
  --disease influenza --source all --output output/influenza_global

# Demo mode (no internet required)
python skills/epi-data-fetcher/epi_data_fetcher.py --demo
```

## Downstream Skill Chains

The output `data.csv` feeds directly into analysis skills:

```bash
# Fetch → Rt estimation
python skills/epi-data-fetcher/epi_data_fetcher.py \
  --disease covid-19 --source owid --country USA --output /tmp/data
python skills/rt-estimator/rt_estimator.py \
  --input /tmp/data/data.csv --pathogen "COVID-19" --output /tmp/rt

# Fetch → Forecasting
python skills/epi-data-fetcher/epi_data_fetcher.py --disease malaria --source who --country KEN
python skills/disease-forecaster/disease_forecaster.py --input output/data.csv

# Fetch → Early warning CUSUM
python skills/epi-data-fetcher/epi_data_fetcher.py --disease cholera --source who --country BGD
python skills/early-warning-system/early_warning.py --input output/data.csv
```

## WHO GHO Indicator Reference

| Disease | Incidence Indicator | Mortality Indicator |
|---------|-------------------|---------------------|
| Malaria | `MALARIA_EST_INCIDENCE` | `MALARIA_EST_DEATHS` |
| Cholera | `WHS3_62` | `WHS3_63` |
| Tuberculosis | `MDG_0000000020` | `MDG_0000000021` |
| HIV/AIDS | `HIV_0000000026` | `HIV_0000000006` |
| Measles | `WHS4_544` | `WHS4_100` |

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `WHO GHO fetch failed` | WHO API unavailable or rate limit | Retry, or use `--demo` |
| `No OWID dataset configured` | Disease not in OWID catalogue | Use `--source who` instead |
| Empty data.csv | Country code wrong or no data | Check ISO3 code (e.g. NGA not Nigeria) |
| Slow fetch | WHO GHO is slow (OData) | Normal; WHO cache saves subsequent calls |

## Notes

- WHO GHO data is annual; for daily time series use `--source owid` (COVID-19/monkeypox only)
- Rate limiting: WHO requests are throttled to 2/sec; results cached for 24 hours locally
- All data processing is local; no user data is uploaded to external servers

## Chaining

- Works well with: `rt-estimator`, `disease-forecaster`, `early-warning-system`, `dashboard`, `disease-modeler`
- Cite data source in downstream reports: WHO GHO data is updated annually; OWID daily

## Trigger Keywords

- fetch disease data
- download surveillance data
- get who data
- who gho
- our world in data
- owid
- ecdc data
- get epidemiological data
- retrieve case data
- public health data

## Standalone Packaging

This standalone skill no longer depends on the repo-level `epiclaw` CLI. Run it directly with `python epi_data_fetcher.py --demo --output ./output`, or expose this directory as an OpenClaw skill root.
