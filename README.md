# EpiClaw

EpiClaw is a project built on top of [OpenClaw](https://github.com/openclaw/openclaw) for our own domain scenarios.

It is designed to extend OpenClaw with our team-specific Epi skills, while gradually adding the ability to connect with BioOS and operate BioOS resources. The goal is to make EpiClaw a more practical capability layer for epidemic prevention, early warning, epidemiological analysis, and bioinformatics-related workflows.

## What is this repository for

This repository is mainly used for two things:

1. **Collecting and organizing our team-specific skills**
2. **Extending EpiClaw with BioOS-related capabilities**

At this stage, the repository already contains a consolidated set of epidemiology and public-health-oriented skills copied into `skills/`, so it is no longer just a placeholder for future accumulation. It is now a working skill library covering surveillance, outbreak investigation, modeling, statistical epidemiology, genomic epidemiology, bioinformatics, spatial analysis, evidence synthesis, and public data connectors.

## Current positioning

EpiClaw is currently under development.

Right now, this repository mainly serves as a place to collect skills for our teammates. Everyone can put their own scenario-specific skills into the `skills/` directory, so that these skills can be gradually accumulated, reused, and improved.

At the moment, the repository contains **49 skills** under `skills/`:

- directory structure stays flat under `skills/<skill-name>/`
- classification exists in documentation, not in filesystem layout
- each skill directory can be used directly as an OpenClaw skill root

Typical examples now include:

- epidemic prevention / early warning related skills
- outbreak investigation and contact tracing skills
- cross-cutting epidemiology analysis skills
- epidemiological modeling and forecasting skills
- statistical analysis and policy evaluation skills
- genomic epidemiology and pathogen surveillance skills
- bioinformatics and omics analysis skills
- public data acquisition and connector skills
- BioOS-related capabilities that may be added incrementally in this repository

The current epidemiological skill set can be summarized by the following primary categories:

- `Surveillance & Monitoring`
- `Outbreak Investigation`
- `Modeling & Forecasting`
- `Statistical Epidemiology & Policy`
- `Genomic Epidemiology`
- `Bioinformatics & Omics`
- `Spatial & Environmental`
- `Evidence & Intelligence`
- `Data Acquisition & Connectors`

This repository also currently includes one additional cross-cutting skill, `epidemiologist-analyst`, which is broader than a single primary category and acts more like a general epidemiology reasoning layer across surveillance, outbreak investigation, causal inference, intervention evaluation, and public health decision support.

If you want to find a skill by scenario, the current grouping is roughly:

- routine surveillance, anomaly detection, dashboards: `Surveillance & Monitoring`
- field investigation, line list analysis, contact tracing: `Outbreak Investigation`
- Rt estimation, forecasting, compartmental or stochastic models: `Modeling & Forecasting`
- effect estimation, sample size, serology, survival, VE, policy: `Statistical Epidemiology & Policy`
- lineage, typing, AMR, phylogenetics, transmission, recombination: `Genomic Epidemiology`
- QC, assembly, structure, metagenomics, RNA-seq, repertoire, VCF workflows: `Bioinformatics & Omics`
- GIS, spatial clustering, climate-health analysis: `Spatial & Environmental`
- literature review, pathogen intelligence, disease profiles, travel health: `Evidence & Intelligence`
- public epidemiology and sequence fetching: `Data Acquisition & Connectors`

Representative examples in the current repository include:

- `epidemiologist-analyst`
- `early-warning-system`, `syndromic-surveillance`, `wastewater-surveillance`
- `outbreak-investigator`, `contact-tracing`, `epi-analyst`
- `disease-modeler`, `disease-forecaster`, `rt-estimator`, `stochastic-modeler`
- `epi-calculator`, `meta-analysis`, `vaccine-effectiveness`, `policy-evaluator`
- `variant-surveillance`, `phylodynamics`, `pathogen-typing`, `transmission-inference`
- `sequence-qc`, `genome-assembler`, `protein-structure`, `rnaseq-de`
- `epi-gis`, `climate-health`
- `pathogen-intel`, `lit-reviewer`, `disease-profiler`, `travel-health`
- `epi-data-fetcher`, `ncbi-sequence-fetcher`

## BioOS integration

One important direction of EpiClaw is to connect with **BioOS**, so that the agent can gradually gain the ability to interact with BioOS resources, such as:

- viewing or operating workspace resources
- interacting with workflows
- managing files or analysis outputs
- supporting domain workflows on top of BioOS

This part is still evolving.

The currently imported skills are still primarily standalone OpenClaw skills. In practice, most of them expose:

- a `SKILL.md` entrypoint description
- a direct Python entry script
- `--demo` mode for example execution
- `--output <dir>` for structured outputs such as `report.md`, `result.json`, figures, tables, or HTML reports

That makes the current repository useful immediately as a local skill library, while BioOS-facing integration can continue to be layered on top later.

## Repository structure

The repository structure should now be understood according to the actual content in this codebase rather than the earlier illustrative placeholder layout.

```text
EpiClaw/
├── README.md
└── skills/
    ├── early-warning-system/
    ├── outbreak-investigator/
    ├── disease-modeler/
    ├── variant-surveillance/
    ├── epi-data-fetcher/
    └── ...
```

The key points are:

- all skills are stored flatly under `skills/`
- each skill directory is independently usable
- the path convention is always `skills/<skill-name>/`
- classification is maintained in documentation and summaries, not by nested directory grouping

At the time of writing, the repository contains the following grouped skill inventory:

- `Surveillance & Monitoring`:
  `early-warning-system`, `excess-mortality`, `multi-pathogen-dashboard`, `syndromic-surveillance`, `wastewater-surveillance`
- `Outbreak Investigation`:
  `contact-tracing`, `epi-analyst`, `outbreak-investigator`
- `Modeling & Forecasting`:
  `age-structured-modeler`, `disease-forecaster`, `disease-modeler`, `network-epidemic-model`, `rt-estimator`, `stochastic-modeler`, `within-host-modeler`
- `Statistical Epidemiology & Policy`:
  `epi-calculator`, `meta-analysis`, `policy-evaluator`, `risk-factor-regression`, `sample-size-calculator`, `seroprevalence`, `survival-analysis`, `vaccine-effectiveness`
- `Genomic Epidemiology`:
  `amr-surveillance`, `pathogen-typing`, `phylodynamics`, `recombination-detector`, `transmission-inference`, `variant-surveillance`
- `Bioinformatics & Omics`:
  `bioconductor-bridge`, `comparative-genomics`, `epitope-predictor`, `genome-assembler`, `immune-repertoire`, `metagenomics-classifier`, `protein-structure`, `rnaseq-de`, `seq-wrangler`, `sequence-qc`, `vcf-annotator`
- `Spatial & Environmental`:
  `climate-health`, `epi-gis`
- `Evidence & Intelligence`:
  `disease-profiler`, `lit-reviewer`, `pathogen-intel`, `travel-health`
- `Data Acquisition & Connectors`:
  `epi-data-fetcher`, `ncbi-sequence-fetcher`
- `Cross-cutting`:
  `epidemiologist-analyst`

Each skill's introduction, trigger keywords, expected inputs, dependency notes, and usage instructions are primarily documented inside its own `SKILL.md`.

## How to contribute

If you want to add a new skill, please put it under the `skills/` directory and organize it with a clear name and structure.

Recommended principles:

- one skill for one clear purpose
- keep naming explicit and understandable
- document inputs, outputs, trigger keywords, and usage in `SKILL.md`
- keep the path flat as `skills/<skill-name>/`
- make it easy for other teammates to reuse
- if a skill spans multiple domains, keep the directory stable and express categorization in documentation instead of moving paths around

For consistency with the imported skill set, a typical skill directory should ideally include:

- `SKILL.md`
- a standalone script entrypoint
- optional `demo_data/`
- optional `tests/`
- predictable output artifacts such as `report.md` and `result.json`

## Vision

We hope EpiClaw can gradually become a practical capability layer built on OpenClaw for our own scenarios:

- continuously accumulating team-specific skills
- continuously enhancing BioOS integration
- eventually forming a more usable agent capability set for our real-world work

More concretely, the current imported skills already give EpiClaw a strong base in epidemiology and public health workflows. The next stage is not only to collect more skills, but also to make them easier to route, compose, and connect to real execution environments such as BioOS, public data sources, and internal operational workflows.
